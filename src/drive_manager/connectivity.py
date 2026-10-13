"""Manual root-read checks: private snapshots, bounded processes, safe results."""
from dataclasses import dataclass
from pathlib import Path
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from .wallet import PASSWORD_COMMAND, clean_env

@dataclass(frozen=True)
class Result:
    state: str
    seconds: float = 0


def classify(message):
    """Discard raw diagnostics after mapping known patterns to fixed catalog keys."""
    message = message[:65536].lower()
    if any(word in message for word in ('password command', 'decrypt configuration', 'incorrect configuration password')):
        return 'connection_wallet'
    if re.search(r'\b401\b', message) or any(word in message for word in ('invalid_grant','unauthorized','token expired','invalid credentials','invalid access token')):
        return 'connection_auth'
    if re.search(r'\b403\b', message) or any(word in message for word in ('permission denied','access denied','insufficient permission')):
        return 'connection_permission'
    if re.search(r'\b429\b', message) or 'rate limit' in message or 'too many requests' in message:
        return 'connection_rate'
    if any(word in message for word in ('no such host','network is unreachable','connection refused','connection reset','i/o timeout','tls handshake timeout','context deadline exceeded')):
        return 'connection_network'
    return 'connection_error'


def probe(args, cancel=None, limit=20):
    """Never emit filenames or logs. Kill only this check's process group on timeout."""
    started=time.monotonic(); process=None
    try:
        process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,env=clean_env(),umask=0o077,start_new_session=True)
        os.set_blocking(process.stderr.fileno(),False)
        diagnostic=bytearray()
        def drain():
            for _ in range(16):
                try: chunk=os.read(process.stderr.fileno(),8192)
                except BlockingIOError: return
                if not chunk: return
                diagnostic.extend(chunk[:max(0,65536-len(diagnostic))])
        while True:
            drain()
            if cancel is not None and cancel.is_set(): return Result('connection_cancelled')
            if process.poll() is not None:
                drain()
                state='connection_ok' if process.returncode==0 else classify(diagnostic.decode('utf-8',errors='replace'))
                return Result(state,time.monotonic()-started)
            if time.monotonic()-started>=limit: return Result('connection_timeout',time.monotonic()-started)
            if cancel is not None: cancel.wait(.05)
            else: time.sleep(.05)
    except Exception:
        return Result('connection_error')
    finally:
        if process is not None:
            if process.poll() is None:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait()
            if process.stderr is not None:process.stderr.close()


def check(manager, remote, cancel=None):
    """Read access only; never mount, change preferences, or update source secrets."""
    try:
        manager.identity(remote)
        if cancel is not None and cancel.is_set(): return Result('connection_cancelled')
        own=manager.is_app_account(remote)
        source=manager.accounts.path(remote)
        if not own:
            lines=manager.runner.run(['rclone','config','file']).strip().splitlines()
            if not lines:return Result('connection_error')
            source=Path(lines[-1])
        if not source.is_absolute() or source.is_symlink() or not source.is_file():return Result('connection_error')
        encrypted=manager.accounts.encrypted(source)
        if encrypted and not own:return Result('connection_locked')
        folder=manager.home/'.local/state/drive-manager/connectivity'
        if any(p.is_symlink() for p in [folder,*folder.parents]):return Result('connection_error')
        folder.mkdir(parents=True,exist_ok=True,mode=0o700);folder.chmod(0o700)
        with tempfile.TemporaryDirectory(dir=folder,prefix='.check-') as temporary:
            config=Path(temporary)/'rclone.conf'
            with config.open('xb') as copy:
                os.fchmod(copy.fileno(),0o600)
                with source.open('rb') as original:shutil.copyfileobj(original,copy)
            args=['rclone','lsf',remote+':','--dirs-only','--max-depth=1','--config='+str(config),
                  '--contimeout=5s','--timeout=10s','--retries=1','--low-level-retries=1','--log-level=ERROR']
            if encrypted:args.append('--password-command='+PASSWORD_COMMAND)
            return probe(args,cancel)
    except Exception:
        return Result('connection_error')

from contextlib import contextmanager
from .process import OperationError

@contextmanager
def private_snapshot(manager,remote):
    """Reusable isolated config for explicit readback of a disposable test file."""
    manager.identity(remote);own=manager.is_app_account(remote);source=manager.accounts.path(remote)
    if not own:
        lines=manager.runner.run(['rclone','config','file']).strip().splitlines()
        if not lines:raise OperationError('connection_error')
        source=Path(lines[-1])
    if not source.is_absolute() or source.is_symlink() or not source.is_file():raise OperationError('connection_error')
    encrypted=manager.accounts.encrypted(source)
    if encrypted and not own:raise OperationError('connection_locked')
    folder=manager.home/'.local/state/drive-manager/connectivity'
    if any(p.is_symlink() for p in [folder,*folder.parents]):raise OperationError('connection_error')
    folder.mkdir(parents=True,exist_ok=True,mode=0o700);folder.chmod(0o700)
    with tempfile.TemporaryDirectory(dir=folder,prefix='.check-') as temporary:
        config=Path(temporary)/'rclone.conf'
        with config.open('xb') as copy:
            os.fchmod(copy.fileno(),0o600)
            with source.open('rb') as original:shutil.copyfileobj(original,copy)
        yield config,encrypted
