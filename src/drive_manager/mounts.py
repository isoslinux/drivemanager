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
