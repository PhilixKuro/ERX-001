"""R11 F 片3 探针：filelock 3.20 在释放时 unlink 锁文件，多进程并发取同一把锁时是否抛 FileNotFoundError。

用法（容器内，-I 运行）：python -I lock_unlink_probe.py <目录>
只在 <目录> 下建删 probe.lock，不碰任何站点文件。
"""

import multiprocessing as mp
import os
import sys

from filelock import FileLock


def worker(path, n, q):
	errs = {}
	for _ in range(n):
		try:
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
	q = mp.Queue()
	ps = [mp.Process(target=worker, args=(path, 300, q)) for _ in range(4)]
	for p in ps:
		p.start()
	for p in ps:
		p.join()
	total = {}
	for _ in ps:
		for k, v in q.get().items():
			total[k] = total.get(k, 0) + v
	print(d, "attempts=1200 errors=", total)
	if os.path.exists(path):
		os.unlink(path)
	os.rmdir(d)
