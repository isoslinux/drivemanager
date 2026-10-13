"""Live root-read acceptance runner; writing/reconnect remain explicit actions."""
from .connectivity import check
from .providers import ACTIVE_TYPES


def read_all(manager,cancel,on_result=None):
    rows=[]
    if cancel.is_set():return rows
    for remote in manager.discover_accounts():
        if cancel.is_set():break
        provider=manager.provider_of(remote)
        if provider not in ACTIVE_TYPES:continue
        result=check(manager,remote,cancel);row=(remote,provider,result);rows.append(row)
        if on_result:on_result(row)
    return rows


def reconnect(manager,remote,confirmed=False,cancel=None):
    from .process import OperationError
    if not confirmed:raise OperationError('validation_confirm')
    if cancel is not None and cancel.is_set():raise OperationError('connection_cancelled')
    status=manager.status(remote)
    if not status.managed:raise OperationError('validation_error')
    manager.unmount(remote,confirmed=True)
    status=manager.mount(remote);deadline=time.monotonic()+20
    while status.state=='starting' and time.monotonic()<deadline and not (cancel and cancel.is_set()):
        if cancel:cancel.wait(.2)
        else:time.sleep(.2)
        status=manager.status(remote)
    return status

from dataclasses import dataclass
from pathlib import Path
import os,signal,subprocess,time
from uuid import uuid4
from .connectivity import private_snapshot
from .wallet import PASSWORD_COMMAND,clean_env
from . import transfers

@dataclass(frozen=True)
class WriteResult:
    state:str
    file:str=''
    seconds:float=0


def remote_bytes(manager,remote,name,cancel):
    """Read only a uniquely generated test file; no document contents are reported."""
    with private_snapshot(manager,remote) as (config,encrypted):
        args=['rclone','cat',remote+':'+name,'--count=1024','--config='+str(config),
              '--contimeout=5s','--timeout=10s','--retries=1','--low-level-retries=1','--log-level=ERROR']
        if encrypted:args.append('--password-command='+PASSWORD_COMMAND)
        process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            start_new_session=True,umask=0o077,env=clean_env())
        deadline=time.monotonic()+20
        try:
            while time.monotonic()<deadline and not cancel.is_set():
                try:
                    output,_=process.communicate(timeout=.2)
                    return output if process.returncode==0 and len(output)<=1024 else None
                except subprocess.TimeoutExpired:pass
            return None
        finally:
            if process.poll() is None:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait()
            if process.stdout is not None:process.stdout.close()


def write_test(manager,remote,cancel,confirmed=False):
    if not confirmed:return WriteResult('validation_confirm')
    start=time.monotonic();name=''
    try:
        with manager.lock():
            if cancel.is_set():return WriteResult('connection_cancelled')
            status=manager.status(remote)
            if not status.managed or not status.writable or status.pending!=0:return WriteResult('validation_write_requires')
            manager.ensure_no_dirty_cache(remote)
            name='DriveManager-test-'+uuid4().hex+'.txt'
            payload=('Drive Manager disposable acceptance test\n'+name+'\n').encode()
            target=Path(status.path)/name
            fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'wb') as file:file.write(payload);file.flush();os.fsync(file.fileno())
            deadline=time.monotonic()+60
            while time.monotonic()<deadline and not cancel.is_set():
                if transfers.pending(manager.rc_endpoint(remote))==0:
                    if remote_bytes(manager,remote,name,cancel)==payload:
                        return WriteResult('validation_write_ok',name,time.monotonic()-start)
                cancel.wait(1)
            return WriteResult('connection_cancelled' if cancel.is_set() else 'validation_timeout',name,time.monotonic()-start)
    except Exception:return WriteResult('validation_error',name,time.monotonic()-start)
