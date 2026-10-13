"""Local cache health without reading documents or deleting pending data."""
from dataclasses import dataclass
from pathlib import Path
import shutil
from .transfers import dirty_files

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

import os,signal,subprocess,sys,time

@dataclass(frozen=True)
class BrowseTiming:
    listing:float|None=None
    space:float|None=None


def browse(manager,remote):
    """Bounded subprocesses keep FUSE waits off the GUI; output contains no names."""
    status=manager.status(remote)
    if status.state not in {'mounted','external'}:return BrowseTiming()
    values=[]
    for code in ['import os,sys; it=os.scandir(sys.argv[1]); sum(1 for entry in it); it.close()',
                 'import os,sys; os.statvfs(sys.argv[1])']:
        started=time.monotonic();process=None
        try:
            process=subprocess.Popen([sys.executable,'-c',code,status.path],stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            process.wait(timeout=10)
            values.append(time.monotonic()-started if process.returncode==0 else None)
        except Exception:values.append(None)
        finally:
            if process is not None and process.poll() is None:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait()
    return BrowseTiming(*values)
