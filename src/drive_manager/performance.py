"""Local cache health without reading documents or deleting pending data."""
from dataclasses import dataclass
from pathlib import Path
import shutil
from .transfers import dirty_files
import os,signal,subprocess,sys,time

@dataclass(frozen=True)
class CacheHealth:
    free: int | None = None
    pending: int | None = None
    @property
    def low(self):return self.free is not None and self.free<1024**3


def inspect(manager,remote):
    try:
        cache=manager.write_cache_path(remote)
        if any(p.is_symlink() for p in [cache,*cache.parents]):return CacheHealth()
        existing=cache
        while not existing.exists():existing=existing.parent
        free=shutil.disk_usage(existing).free
        try:pending=dirty_files(cache)
        except Exception:pending=None
        return CacheHealth(free,pending)
    except Exception:return CacheHealth()


def slow(result):
    return result.state=='connection_ok' and result.seconds>=5


@dataclass(frozen=True)
class BrowseTiming:
    listing:float|None=None
    space:float|None=None


def browse(manager,remote,cancel=None,on_stage=None):
    """Bounded subprocesses keep FUSE waits off the GUI; output contains no names."""
    if cancel is not None and cancel.is_set():return BrowseTiming()
    if on_stage:on_stage("operation_status",remote)
    status=manager.status(remote)
    if status.state not in {'mounted','external'}:return BrowseTiming()
    values=[]
    for index,code in enumerate(['import os,sys; it=os.scandir(sys.argv[1]); sum(1 for entry in it); it.close()',
                 'import os,sys; os.statvfs(sys.argv[1])']):
        if cancel is not None and cancel.is_set():return BrowseTiming()
        if on_stage:on_stage('operation_listing' if index==0 else 'operation_space',remote)
        started=time.monotonic();process=None
        try:
            process=subprocess.Popen([sys.executable,'-c',code,status.path],stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            deadline=time.monotonic()+10
            while process.poll() is None:
                if cancel is not None and cancel.is_set():return BrowseTiming()
                if time.monotonic()>=deadline:raise TimeoutError()
                try:process.wait(timeout=.1)
                except subprocess.TimeoutExpired:pass
            values.append(time.monotonic()-started if process.returncode==0 else None)
        except Exception:values.append(None)
        finally:
            if process is not None and process.poll() is None:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait()
    return BrowseTiming(*values)


def browsing_advice(result):
    """Heuristic guidance, not a diagnosis of provider or Dolphin internals."""
    if result is None or result.listing is None or result.space is None:
        return 'browse_incomplete'
    listing=result.listing>=2;space=result.space>=2
    if listing and space:return 'browse_both_slow'
    if listing:return 'browse_listing_slow'
    if space:return 'browse_space_slow'
    return 'browse_fast'
