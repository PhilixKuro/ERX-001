"""R14 F: does frappe_debug.demo.locks actually exclude other processes on the bind-mounted bench?

R11 SB's probe only counted FileNotFoundError on the mount; its mutual-exclusion test ran in /tmp.
Here 4 processes x 200 times do an unprotected read-modify-write of a counter file inside the lock,
all on the given directory. Lost updates (final != 800) mean the lock does not exclude.
Usage (container): ../env/bin/python -I lock_mutex_probe.py <dir>   (only creates/deletes files in <dir>)
"""

import multiprocessing as mp
import os
import sys
from unittest.mock import patch

from frappe_debug.demo import locks


def worker(lock, counter, n, q):
	errors = 0
	for _ in range(n):
		try:
			with patch.object(locks, "lock_path", return_value=lock):
				with locks.site_lock("probe", timeout=30):
					with open(counter) as stream:
						value = int(stream.read() or 0)
					with open(counter, "w") as stream:
						stream.write(str(value + 1))
		except Exception:  # noqa: BLE001
			errors += 1
	q.put(errors)


if __name__ == "__main__":
	mp.set_start_method("spawn")
	directory = sys.argv[1]
	os.makedirs(directory, exist_ok=True)
	lock, counter = os.path.join(directory, "probe.lock"), os.path.join(directory, "counter")
	with open(counter, "w") as stream:
		stream.write("0")
	q = mp.Queue()
	processes = [mp.Process(target=worker, args=(lock, counter, 200, q)) for _ in range(4)]
	for p in processes:
		p.start()
	for p in processes:
		p.join()
	errors = sum(q.get() for _ in processes)
	with open(counter) as stream:
		final = int(stream.read())
	print(directory, "expected=800 final=", final, "errors=", errors)
	for path in (lock, counter):
		os.unlink(path)
	os.rmdir(directory)
