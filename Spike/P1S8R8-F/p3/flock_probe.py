"""Probe: does fcntl.flock / py-filelock exclude across processes on the /workspace bind mount?"""
import os, subprocess, sys, time
from filelock import FileLock
target = sys.argv[1]
if len(sys.argv) > 2 and sys.argv[2] == "child":
    lock = FileLock(target, timeout=0)
    try:
        lock.acquire(); print("child_acquired"); lock.release()
    except Exception as e:
        print("child_blocked", type(e).__name__)
    sys.exit(0)
lock = FileLock(target, timeout=0)
lock.acquire()
out = subprocess.run([sys.executable, __file__, target, "child"], capture_output=True, text=True).stdout.strip()
lock.release()
out2 = subprocess.run([sys.executable, __file__, target, "child"], capture_output=True, text=True).stdout.strip()
print("while_held:", out, "| after_release:", out2)
os.path.exists(target) and os.unlink(target)
