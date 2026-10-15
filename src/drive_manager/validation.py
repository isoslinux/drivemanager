"""Live root-read acceptance runner; writing/reconnect remain explicit actions."""
from .connectivity import check
from .providers import ACTIVE_TYPES
from dataclasses import dataclass
from pathlib import Path
import os,signal,subprocess,time
from uuid import uuid4
from .connectivity import private_snapshot
from .wallet import PASSWORD_COMMAND,clean_env
from . import transfers
from . import test_files
import json
import sys
from threading import Event


def read_all(manager,cancel,on_result=None,on_start=None):
    rows=[]
    if cancel.is_set():return rows
    for remote in manager.discover_accounts():
        if cancel.is_set():break
        provider=manager.provider_of(remote)
        if provider not in ACTIVE_TYPES:continue
        if on_start:on_start("connection_checking",remote)
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
    start=time.monotonic();name='';created=False
    try:
        with manager.lock():
            if cancel.is_set():return WriteResult('connection_cancelled')
            status=manager.status(remote)
            if not status.managed or not status.writable or status.pending!=0:return WriteResult('validation_write_requires')
            manager.ensure_no_dirty_cache(remote)
            name='DriveManager-test-'+uuid4().hex+'.txt'
            test_files.add(manager,remote,[name])
            payload=('Drive Manager disposable acceptance test\n'+name+'\n').encode()
            target=Path(status.path)/name
            fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            created=True
            with os.fdopen(fd,'wb') as file:file.write(payload);file.flush();os.fsync(file.fileno())
            deadline=time.monotonic()+60
            while time.monotonic()<deadline and not cancel.is_set():
                if transfers.pending(manager.rc_endpoint(remote))==0:
                    if remote_bytes(manager,remote,name,cancel)==payload:
                        return WriteResult('validation_write_ok',name,time.monotonic()-start)
                cancel.wait(1)
            return WriteResult('connection_cancelled' if cancel.is_set() else 'validation_timeout',name,time.monotonic()-start)
    except FileNotFoundError:
        removed=False
        if name and not created:
            try:test_files.remove(manager,remote,name);removed=True
            except Exception:pass
        return WriteResult('validation_error','' if removed else name,time.monotonic()-start)
    except Exception:return WriteResult('validation_error',name,time.monotonic()-start)

def bounded_output(args,cancel,limit=10,max_bytes=131072,allow_missing=False):
    """Bounded disposable child, including a bounded reap after killing it."""
    if cancel.is_set():return 'connection_cancelled',None
    process=None;started=time.monotonic()
    try:
        process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True,env=clean_env(),umask=0o077)
        os.set_blocking(process.stdout.fileno(),False);output=bytearray()
        while True:
            for _ in range(16):
                try:part=os.read(process.stdout.fileno(),8192)
                except BlockingIOError:break
                if not part:break
                output.extend(part)
                if len(output)>max_bytes:return 'validation_error',None
            if cancel.is_set():return 'connection_cancelled',None
            if process.poll() is not None:
                while True:
                    try:part=os.read(process.stdout.fileno(),8192)
                    except BlockingIOError:break
                    if not part:break
                    output.extend(part)
                    if len(output)>max_bytes:return 'validation_error',None
                if allow_missing and process.returncode==4:return 'validation_cleanup_absent',None
                return ('operation_finished',bytes(output)) if process.returncode==0 else ('validation_error',None)
            if time.monotonic()-started>=limit:return 'validation_timeout',None
            cancel.wait(.05)
    except Exception:return 'validation_error',None
    finally:
        if process is not None:
            if process.poll() is None:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                try:process.wait(timeout=1)
                except subprocess.TimeoutExpired:pass
            if process.stdout is not None:process.stdout.close()


def cleanup_test(manager,remote,name,confirmed=False,cancel=None):
    """Verify outside the global lock; final deletion is bounded and cancellable."""
    cancel=cancel if cancel is not None else Event()
    if not confirmed:return WriteResult('validation_confirm')
    if not isinstance(name,str) or not test_files.PATTERN.fullmatch(name):return WriteResult('validation_error')
    try:
        with manager.lock():
            if cancel.is_set():return WriteResult('connection_cancelled',name)
            status=manager.status(remote)
            if not status.managed or not status.writable or status.pending!=0:return WriteResult('validation_write_requires',name)
            manager.ensure_no_dirty_cache(remote)
            folder=status.path
        worker=str(Path(__file__).with_name('cleanup_probe.py'))
        state,output=bounded_output([sys.executable,'-I',worker,folder,name,'verify'],cancel,allow_missing=True)
        if output is None:
            if state=='validation_cleanup_absent':
                with manager.lock():
                    if cancel.is_set():return WriteResult('connection_cancelled',name)
                    current=manager.status(remote)
                    if current.path!=folder or not current.managed or not current.writable or current.pending!=0:return WriteResult('validation_write_requires',name)
                    manager.ensure_no_dirty_cache(remote)
                    test_files.remove(manager,remote,name)
            return WriteResult(state,name)
        identity=json.loads(output)
        with manager.lock():
            if cancel.is_set():return WriteResult('connection_cancelled',name)
            current=manager.status(remote)
            if current.path!=folder or not current.managed or not current.writable or current.pending!=0:return WriteResult('validation_write_requires',name)
            manager.ensure_no_dirty_cache(remote)
            state,output=bounded_output([sys.executable,'-I',worker,folder,name,'delete',json.dumps(identity)],cancel,allow_missing=True)
            if output is None and state!='validation_cleanup_absent':return WriteResult(state,name)
            test_files.remove(manager,remote,name)
            if state=='validation_cleanup_absent':return WriteResult(state,name)
        return WriteResult('validation_cleanup_requested',name)
    except Exception:return WriteResult('validation_error',name)


def discover_test_files(manager,remote,cancel):
    """List only root test-file candidates; deletion still verifies exact content."""
    with private_snapshot(manager,remote) as (config,encrypted):
        args=['rclone','lsf',remote+':','--files-only','--max-depth=1','--include=DriveManager-test-*.txt','--config='+str(config),'--contimeout=5s','--timeout=10s','--retries=1','--low-level-retries=1','--log-level=ERROR']
        if encrypted:args.append('--password-command='+PASSWORD_COMMAND)
        state,output=bounded_output(args,cancel,20)
        if output is None:return WriteResult(state)
        candidates=[n for n in output.decode('utf-8').splitlines() if test_files.PATTERN.fullmatch(n)]
        if cancel.is_set():return WriteResult('connection_cancelled')
        with manager.lock():test_files.add(manager,remote,candidates)
        return WriteResult('validation_discovered')
