"""Fail-closed upload checks and durable-cache protection for writable mounts."""
import json
import os
from pathlib import Path
import subprocess
from .process import OperationError
from .internxt import UnixConnection

class TransferError(OperationError):
    pass

def request(endpoint, method):
    connection=UnixConnection(endpoint);connection.timeout=3
    try:
        connection.request('POST','/'+method,'{}',{'Content-Type':'application/json'})
        response=connection.getresponse()
        if response.status!=200:raise ValueError()
        return json.loads(response.read(1024*1024))
    except Exception:raise TransferError('uploads_unknown') from None
    finally:connection.close()

def pending(endpoint):
    stats=request(endpoint,'vfs/stats'); cache=stats.get('diskCache',{})
    keys=('uploadsQueued','uploadsInProgress','erroredFiles')
    if any(type(cache.get(k)) is not int or cache[k]<0 for k in keys):raise TransferError('uploads_unknown')
    if cache.get('outOfSpace') is not False:raise TransferError('uploads_unknown')
    return sum(cache[k] for k in keys)

def dirty_files(cache):
    root=Path(cache)/'vfsMeta'; count=0
    if root.is_symlink():raise TransferError('uploads_unknown')
    if not root.exists():return 0
    try:
        for folder,dirs,files in os.walk(root,followlinks=False):
            if any((Path(folder)/name).is_symlink() for name in dirs):raise ValueError()
            for name in files:
                path=Path(folder)/name
                if path.is_symlink() or path.stat().st_size>1024*1024:raise ValueError()
                data=json.loads(path.read_text())
                if type(data.get('Dirty')) is not bool:raise ValueError()
                count+=int(data['Dirty'])
        return count
    except Exception:raise TransferError('uploads_unknown') from None

def ensure_closed(path):
    try:
        result=subprocess.run(['fuser','-m','--',str(path)],stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
        if result.returncode==0:raise TransferError('files_open')
        if result.returncode!=1:raise TransferError('uploads_unknown')
    except TransferError:raise
    except Exception:raise TransferError('uploads_unknown') from None

from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Transfer:
    name: str
    percentage: float | None
    speed: float
    eta: float | None

@dataclass(frozen=True)
class Progress:
    state: str = 'unmonitored'
    queued: int = 0
    uploading: int = 0
    errors: int = 0
    speed: float = 0
    files: tuple = ()

def number(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value>=0

def progress(endpoint):
    try:
        vfs=request(endpoint,'vfs/stats'); core=request(endpoint,'core/stats')
        cache=vfs.get('diskCache',{})
        keys=('uploadsQueued','uploadsInProgress','erroredFiles')
        if any(type(cache.get(k)) is not int or cache[k]<0 for k in keys):raise ValueError()
        if type(cache.get('outOfSpace')) is not bool:raise ValueError()
        queued,uploading,errors=(cache[k] for k in keys)
        files=[]
        for item in core.get('transferring') or []:
            if not isinstance(item,dict):raise ValueError()
            name=item.get('name','')
            if not isinstance(name,str):raise ValueError()
            name=''.join(c for c in name if ord(c)>=32)[:200]
            percentage=item.get('percentage');speed=item.get('speedAvg',item.get('speed',0));eta=item.get('eta')
            files.append(Transfer(name,min(100,percentage) if number(percentage) else None,
                                  speed if number(speed) else 0,eta if number(eta) else None))
        state='uploading' if uploading else 'queued' if queued else 'transferring' if files else 'idle'
        if errors or cache.get('outOfSpace'):
            message=core.get('lastError','')
            message=message.lower() if isinstance(message,str) else ''
            if any(word in message for word in ('invalid_grant','unauthorized','401','authentication')):state='auth_required'
            elif any(word in message for word in ('no such host','network is unreachable','timeout','connection refused','dial tcp')):state='network_retry'
            else:state='transfer_error'
        speed=core.get('speed',0)
        return Progress(state,queued,uploading,errors,speed if number(speed) else 0,tuple(files[:50]))
    except Exception:
        return Progress('monitor_unknown')
