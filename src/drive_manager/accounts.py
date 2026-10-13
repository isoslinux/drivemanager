"""OAuth registration in isolated private configs; no secrets enter logs or argv."""
import configparser
import json
from hashlib import sha256
from pathlib import Path
import os
import re
import subprocess
import tempfile
from .process import OperationError
from .remotes import discover
from .oauth_output import OAuthOutput
from .providers import ENCRYPTED_TYPES

class AuthorizationError(OperationError):
    def __init__(self, key):
        super().__init__("Authorization failed")
        self.key = key

class Accounts:
    def __init__(self, home):
        self.folder = Path(home) / '.config/drive-manager/connections'

    def path(self, remote):
        return self.folder / (sha256(remote.encode()).hexdigest()[:24] + '.conf')

    @staticmethod
    def encrypted(path):
        if not Path(path).is_file(): return False
        with Path(path).open('rb') as file:
            return b'RCLONE_ENCRYPT_V0:' in file.read(256)

    def metadata_path(self, remote):
        return self.path(remote).with_suffix('.meta.json')

    def configs(self):
        return sorted(self.folder.glob('*.conf')) if self.folder.exists() else []

    def names(self, runner):
        names = []
        for config in self.configs():
            if config.is_symlink(): raise OperationError('Invalid account configuration')
            if self.encrypted(config):
                try:
                    metadata=json.loads(config.with_suffix('.meta.json').read_text())
                    if metadata.get('type') not in ENCRYPTED_TYPES: raise ValueError()
                    self.validate_name(metadata['name'])
                    if self.path(metadata['name'])!=config: raise ValueError()
                    names.append(metadata['name'])
                except Exception:
                    raise OperationError('Invalid encrypted account metadata') from None
            else:
                names.extend(discover(runner, config))
        return names

    def validate_name(self, name):
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,47}', name):
            raise OperationError('Use a unique name with letters, numbers, underscores or hyphens')

    def authorize(self, remote, cancel, on_url=None, writable=False, provider="drive"):
        if provider not in {"drive", "dropbox"}: raise OperationError("Unsupported provider")
        """Return a staged file. Caller commits or removes it under operation lock."""
        self.validate_name(remote)
        if cancel.is_set(): raise OperationError("Authorization cancelled")
        folder = self.folder
        for parent in reversed([folder, *folder.parents]):
            if parent.is_symlink(): raise OperationError('Invalid account directory')
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(folder, 0o700); os.chmod(folder.parent, 0o700)
        fd, temp = tempfile.mkstemp(dir=folder, prefix='.oauth-', suffix='.tmp')
        os.close(fd)
        process = None
        output = OAuthOutput(on_url)
        try:
            options = ['scope='+('drive' if writable else 'drive.readonly')] if provider == 'drive' else []
            process = subprocess.Popen(['rclone', 'config', 'create', remote, provider,
                *options, 'config_is_local=true', 'config_auth_no_browser=true',
                '--config=' + temp, '--no-output', '--log-level=NOTICE'],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                env={k: v for k, v in os.environ.items() if not k.startswith('RCLONE_')},
                umask=0o077)
            stream = getattr(process, 'stdout', None)
            if stream is not None: os.set_blocking(stream.fileno(), False)
            def drain():
                if stream is None: return
                while True:
                    try: chunk = os.read(stream.fileno(), 4096)
                    except BlockingIOError: break
                    if not chunk: break
                    output.feed(chunk)
            import time
            deadline = time.monotonic() + 600
            while process.poll() is None:
                drain()
                if cancel.wait(0.2) or time.monotonic() >= deadline:
                    raise OperationError('Authorization cancelled or timed out')
            drain()
            if cancel.is_set() or process.returncode != 0:
                raise OperationError('Authorization failed or cancelled')
            parser = configparser.ConfigParser(interpolation=None)
            parser.read(temp)
            if not parser.has_section(remote) or not parser.get(remote, 'token', fallback=''):
                raise OperationError('Authorization did not complete')
            os.chmod(temp, 0o600)
            return Path(temp)
        except Exception:
            if process is not None and process.poll() is None:
                process.terminate()
                try: process.wait(timeout=3)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
            Path(temp).unlink(missing_ok=True)
            raise AuthorizationError(output.error_key or 'auth_error') from None
        finally:
            stream = getattr(process, 'stdout', None) if process is not None else None
            if stream is not None: stream.close()
