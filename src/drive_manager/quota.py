"""Bounded read-only quota queries with isolated refreshable credentials."""
from dataclasses import dataclass
from pathlib import Path
import json
import os
import shutil
import subprocess
import tempfile
from .wallet import clean_env

@dataclass(frozen=True)
class Quota:
    total: int | None = None
    used: int | None = None
    free: int | None = None
    other: int | None = None
    trashed: int | None = None
    @property
    def percentage(self):
        if not self.total: return None
        if self.free is not None: occupied = max(0, self.total-self.free)
        elif self.used is not None: occupied = self.used+(self.other or 0)  # Trash may already be included in used.
        else: return None
        return min(100, round(100*occupied/self.total))
    @property
    def low(self):
        return self.free == 0 or (self.free is not None and bool(self.total) and self.free*10 <= self.total)


def parse(data):
    if not isinstance(data,dict): return Quota()
    values = {}
    for key in ('total','used','free','other','trashed'):
        value = data.get(key)
        if value is not None and (type(value) is not int or not 0 <= value <= 2**63-1):
            return Quota()
        values[key] = value
    if values['total'] is not None and values['free'] is not None and values['free'] > values['total']:
        return Quota()
    return Quota(**values)


def run(args):
    result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, timeout=12, check=False, env=clean_env())
    if result.returncode or len(result.stdout)>65536: return None
    return json.loads(result.stdout)


def read_quota(manager, remote):
    """Never write source configs, launch OAuth/Wallet or invoke a data command."""
    try:
        manager.identity(remote)  # Validate remote before passing it to Rclone.
        source = manager.accounts.path(remote)
        if not manager.is_app_account(remote):
            output = manager.runner.run(['rclone','config','file'])
            lines = output.strip().splitlines()
            source = Path(lines[-1]) if lines else Path('/nonexistent')
        if not source.is_absolute() or not source.is_file() or source.is_symlink(): return Quota()
        if manager.accounts.encrypted(source):
            # Read through an already running private mount; never unlock Wallet in the background.
            endpoint = manager.rc_endpoint(remote)
            if not manager.is_app_account(remote) or not endpoint.exists(): return Quota()
            from .internxt import UnixConnection
            connection = UnixConnection(endpoint); connection.timeout = 10
            try:
                connection.request('POST','/operations/about',json.dumps({'fs':remote+':'}),{'Content-Type':'application/json'})
                response = connection.getresponse()
                if response.status != 200: return Quota()
                return parse(json.loads(response.read(65536)))
            finally: connection.close()
        folder = manager.home/'.local/state/drive-manager/quota'
        if any(parent.is_symlink() for parent in [folder,*folder.parents]): return Quota()
        folder.mkdir(parents=True,exist_ok=True,mode=0o700);folder.chmod(0o700)
        with tempfile.TemporaryDirectory(dir=folder,prefix='.query-') as temporary:
            config = Path(temporary)/'rclone.conf'
            with config.open('xb') as file:
                os.fchmod(file.fileno(),0o600)
                with source.open('rb') as original: shutil.copyfileobj(original,file)
            return parse(run(['rclone','about',remote+':','--json','--config='+str(config),
                              '--contimeout=5s','--timeout=8s','--retries=1','--low-level-retries=1','--log-level=ERROR']))
    except Exception:
        return Quota()  # No raw errors, tokens or subprocess output reach the UI.


def size(value):
    if value is None: return '—'
    for label,power in [('TiB',40),('GiB',30),('MiB',20),('KiB',10)]:
        if value >= 2**power: return f'{value/2**power:.1f} {label}'
    return f'{value} B'
