"""R11 SB FD-037 复验：在给定目录下用 frappe_debug.demo.locks（修后）与 filelock（修前）各跑 4 进程×300 次取锁。

用法（容器内）：../env/bin/python -I site_lock_probe.py <目录>
只在 <目录> 下建删 probe.lock，不碰任何站点文件。
"""

import multiprocessing as mp
import os
import sys
from unittest.mock import patch

from filelock import FileLock

from frappe_debug.demo import locks


def worker(kind, path, n, q):
	errs = {}
	for _ in range(n):
		try:
			if kind == "site_lock":
				with patch.object(locks, "lock_path", return_value=path):
					with locks.site_lock("probe", timeout=30):
						pass
			else:
				with FileLock(path, timeout=30):
					pass
		except Exception as e:  # noqa: BLE001
			k = f"{type(e).__name__}:{getattr(e, 'errno', '')}"
			errs[k] = errs.get(k, 0) + 1
	q.put(errs)


if __name__ == "__main__":
	d = sys.argv[1]
	os.makedirs(d, exist_ok=True)
	path = os.path.join(d, "probe.lock")
	for kind in ("filelock", "site_lock"):
		q = mp.Queue()
		ps = [mp.Process(target=worker, args=(kind, path, 300, q)) for _ in range(4)]
		for p in ps:
			p.start()
		for p in ps:
			p.join()
		total = {}
		for _ in ps:
			for k, v in q.get().items():
				total[k] = total.get(k, 0) + v
		print(d, kind, "attempts=1200 errors=", total)
	if os.path.exists(path):
		os.unlink(path)
	os.rmdir(d)
