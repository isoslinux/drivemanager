"""Disposable bounded FUSE worker. Output contains only file identity metadata."""
import json
import os
import stat
import sys
from pathlib import Path

def main():
    folder,name,action=sys.argv[1:4]
    expected=('Drive Manager disposable acceptance test\n'+name+'\n').encode()
    target=Path(folder)/name
    fd=os.open(target,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as file:
        before=os.fstat(file.fileno())
        if not stat.S_ISREG(before.st_mode) or file.read(1025)!=expected:return 2
    identity=[before.st_ino,before.st_dev,before.st_size,before.st_mtime_ns]
    if action=='delete':
        # Recheck both identity from the earlier probe and the payload before unlink.
        if identity!=json.loads(sys.argv[4]):return 2
        after=target.lstat()
        if identity!=[after.st_ino,after.st_dev,after.st_size,after.st_mtime_ns]:return 2
        target.unlink()
    elif action!='verify':return 2
    print(json.dumps(identity));return 0

if __name__=='__main__':
    try:sys.exit(main())
    except FileNotFoundError:sys.exit(4)
    except Exception:sys.exit(2)
