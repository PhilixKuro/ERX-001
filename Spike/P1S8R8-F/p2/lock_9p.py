"""片2探针：/workspace（9p 挂载）上 filelock 能否跨进程互斥。只写本目录临时文件，结束删除。"""
import os, sys, time, subprocess
from filelock import FileLock, Timeout
path = sys.argv[1]
if len(sys.argv) > 2:
    try:
        FileLock(path, timeout=0).acquire(); print("child: ACQUIRED (no mutual exclusion)")
    except Timeout:
        print("child: TIMEOUT (mutual exclusion works)")
    sys.exit(0)
lock = FileLock(path, timeout=0); lock.acquire()
print("parent holds", path)
subprocess.run([sys.executable, __file__, path, "child"])
lock.release()
for p in (path,):
    try: os.unlink(p)
    except FileNotFoundError: pass
