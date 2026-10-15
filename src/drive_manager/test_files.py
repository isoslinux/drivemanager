"""Private retained-test inventory; never includes tokens or document contents."""
import json
import re
from pathlib import Path
from .portable import atomic
from .process import OperationError

PATTERN = re.compile(r'DriveManager-test-[0-9a-f]{32}\.txt')

def path(manager,remote):
    manager.unit_name(remote)
    folder=manager.home/'.local/state/drive-manager/test-files'
    if any(p.is_symlink() for p in [folder,*folder.parents]):raise OperationError('validation_error')
    folder.mkdir(parents=True,exist_ok=True,mode=0o700);folder.chmod(0o700)
    return folder/(manager.settings.path(remote).stem+'.json')

def read(manager,remote):
    source=path(manager,remote)
    if not source.exists():return []
    try:
        if source.is_symlink() or not source.is_file() or source.stat().st_size>128*1024:raise ValueError()
        data=json.loads(source.read_text())
        if not isinstance(data,list) or len(data)>1000 or any(not isinstance(n,str) or not PATTERN.fullmatch(n) for n in data):raise ValueError()
        return list(dict.fromkeys(data))
    except Exception:raise OperationError('validation_error') from None

def add(manager,remote,names):
    current=read(manager,remote)
    if any(not isinstance(n,str) or not PATTERN.fullmatch(n) for n in names):raise OperationError('validation_error')
    values=list(dict.fromkeys(current+list(names)))
    if len(values)>1000:raise OperationError('validation_error')
    atomic(path(manager,remote),json.dumps(values).encode())

def remove(manager,remote,name):
    atomic(path(manager,remote),json.dumps([n for n in read(manager,remote) if n!=name]).encode())
