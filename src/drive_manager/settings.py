"""Private per-account preferences; no credentials or subprocess output."""
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import json
import os
import tempfile
from .process import OperationError

@dataclass(frozen=True)
class Preferences:
    mount_path: str = ''
    cache_gib: int = 2
    cache_hours: int = 24
    automount: bool = False
    writable: bool = False
    upload_kib: int = 0
    download_kib: int = 0

class Settings:
    def __init__(self, home):
        self.home = Path(home)
        self.folder = self.home / '.config/drive-manager/accounts'

    def path(self, remote):
        return self.folder / (sha256(remote.encode()).hexdigest()[:24] + '.json')

    def validate(self, prefs):
        if any(type(value) is not int or not 0<=value<=1048576 for value in (prefs.upload_kib,prefs.download_kib)):
            raise OperationError("Invalid bandwidth limits")
        if (type(prefs.writable) is not bool or type(prefs.automount) is not bool or type(prefs.cache_gib) is not int or not 1 <= prefs.cache_gib <= 1024
            or type(prefs.cache_hours) is not int or not 1 <= prefs.cache_hours <= 8760
            or not isinstance(prefs.mount_path, str)):
            raise OperationError('Invalid preferences')
        if prefs.mount_path:
            path = Path(prefs.mount_path)
            if not path.is_absolute() or any(ord(c) < 32 for c in prefs.mount_path):
                raise OperationError('Invalid mount path')
            if '..' in path.parts or not path.is_relative_to(self.home) or path == self.home:
                raise OperationError('Mount path must be inside your home directory')
            for parent in [path, *path.parents]:
                if parent.is_symlink():
                    raise OperationError('Symbolic links are not allowed in mount paths')
            for protected in ('.config', '.cache', '.local'):
                if path.is_relative_to(self.home / protected):
                    raise OperationError('Mount path overlaps application data')
        return prefs

    def load(self, remote):
        path = self.path(remote)
        try:
            if path.is_symlink(): raise ValueError()
            data = json.loads(path.read_text())
            return self.validate(Preferences(**data))
        except FileNotFoundError:
            return Preferences()
        except (OSError, ValueError, TypeError):
            raise OperationError('Cannot read preferences') from None

    def save(self, remote, prefs):
        self.validate(prefs)
        folder = self.home
        for part in ('.config', 'drive-manager', 'accounts'):
            folder = folder / part
            if folder.is_symlink(): raise OperationError('Invalid settings directory')
            folder.mkdir(mode=0o700, exist_ok=True)
            if part != '.config': os.chmod(folder, 0o700)
        # Manager's operation lock serializes read/validate/write across instances.
        target = self.path(remote)
        if prefs.mount_path:
            for other in self.folder.glob('*.json'):
                if other != target:
                    try: data = json.loads(other.read_text())
                    except (OSError, ValueError): raise OperationError('Cannot validate other accounts') from None
                    other_path = data.get('mount_path', '')
                    if other_path and (Path(other_path).is_relative_to(Path(prefs.mount_path))
                                       or Path(prefs.mount_path).is_relative_to(Path(other_path))):
                        raise OperationError('Mount paths of accounts must not overlap')
        fd, tmp = tempfile.mkstemp(dir=self.folder, prefix='.preferences-')
        try:
            with os.fdopen(fd, 'w') as file:
                os.fchmod(file.fileno(), 0o600)
                json.dump(asdict(prefs), file)
                file.flush(); os.fsync(file.fileno())
            os.replace(tmp, target)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
