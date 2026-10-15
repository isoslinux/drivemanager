"""Linux mountinfo is read without traversing potentially disconnected FUSE."""
from dataclasses import dataclass
from pathlib import Path
import re

@dataclass(frozen=True)
class Mount:
    path: str
    source: str
    kind: str

def unescape(value):
    return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), value)

def read_mounts(path=Path("/proc/self/mountinfo")):
    mounts = []
    for line in path.read_text().splitlines():
        before, sep, after = line.partition(" - ")
        left, right = before.split(), after.split()
        if sep and len(left) >= 5 and len(right) >= 2:
            mounts.append(Mount(unescape(left[4]), unescape(right[1]), right[0]))
    return mounts

def disconnected(path):
    """Probe ENOTCONN in a bounded child; never traverse a stalled FUSE in UI."""
    import subprocess,sys
    code='import os,sys,errno\ntry: os.stat(sys.argv[1])\nexcept OSError as e: sys.exit(3 if e.errno==errno.ENOTCONN else 2)\nsys.exit(0)'
    try:
        result=subprocess.run([sys.executable,'-c',code,str(path)],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3,start_new_session=True)
        return result.returncode==3
    except (OSError,subprocess.TimeoutExpired):return False
