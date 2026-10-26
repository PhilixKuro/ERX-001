"""Probe: does the site_operation FileLock (timeout=0) exclude a second thread of the same process?"""
import sys, threading
from filelock import FileLock, Timeout
path = sys.argv[1]
holder = FileLock(path, timeout=0)
holder.acquire()
result = {}
def other():
    try:
        FileLock(path, timeout=0).acquire(); result["other"] = "acquired"
    except Timeout:
        result["other"] = "Timeout"
t = threading.Thread(target=other); t.start(); t.join()
holder.release()
import os; os.path.exists(path) and os.unlink(path)
print(result)
