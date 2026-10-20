"""P1-S8-R3 SA：在 6787 起 sa.localhost 的 web 服务，并注入探针用的 whitelisted 方法（不落生产目录）。
做法：把本文件里的函数登记成模块 `frappe.sa_probe`（放进 sys.modules）并用 frappe.whitelist 装饰——
`/api/method/frappe.sa_probe.<fn>` 走的是与正式 app 方法完全相同的请求路径（handler.execute_cmd → get_attr → is_whitelisted）。
用法（容器内 sites 目录）：../env/bin/python /workspace/Spike/P1S8R3-SA/sa_serve.py
V-01 ②、V-02、V-03、V-09 共用这一个服务；各命题的逻辑分在 sa_probe 的不同函数里。"""
import json
import os
import subprocess
import sys
import time
import types

import frappe

SITE = "sa.localhost"
BENCH = "/workspace/frappe-bench"
STATUS = f"{BENCH}/sites/{SITE}/private/sa_probe_status.json"  # 完成信号写文件：换库／恢复期间数据库不可用，不能靠库
LOG = f"{BENCH}/logs/sa-probe.log"
ROOT_PW = "123"

mod = types.ModuleType("frappe.sa_probe")
sys.modules["frappe.sa_probe"] = mod
frappe.sa_probe = mod


def log(msg):
	with open(LOG, "a", encoding="utf-8") as f:
		f.write(f"{time.strftime('%H:%M:%S')} pid={os.getpid()} {msg}\n")


def write_status(**kw):
	kw["t"] = time.time()
	with open(STATUS, "w", encoding="utf-8") as f:
		json.dump(kw, f, ensure_ascii=False)


def _switch_db(db_name):
	"""V-01 ②：只改站点 db_name 指向一份预导好的库，清本进程的配置缓存。不碰旧库。"""
	from frappe.config import clear_site_config_cache
	from frappe.installer import update_site_config

	t0 = time.monotonic()
	update_site_config("db_name", db_name)
	clear_site_config_cache()
	# redis 键按 db_name 加前缀（redis_wrapper.py:62），目标库名下可能留着上次用它时的旧缓存，换过去前清掉
	stale = frappe.cache.keys(f"{db_name}|*".encode())
	if stale:
		frappe.cache.delete(*stale)
	return round(time.monotonic() - t0, 3)


def _carry_session(sid, target_db):
	"""V-03 ②：把当前会话行从现库抄进目标库（恢复前读、恢复后写）。"""
	row = frappe.db.sql("select sid, user, sessiondata, ipaddress, lastupdate, status from tabSessions where sid=%s",
		sid, as_dict=True)
	if not row:
		return 0
	r = row[0]
	import pymysql

	conn = pymysql.connect(host="mariadb", user="root", password=ROOT_PW, database=target_db, charset="utf8mb4")
	try:
		with conn.cursor() as c:
			c.execute("delete from tabSessions where sid=%s", (r.sid,))
			c.execute("insert into tabSessions (sid, user, sessiondata, ipaddress, lastupdate, status) values (%s,%s,%s,%s,%s,%s)",
				(r.sid, r.user, r.sessiondata, r.ipaddress, r.lastupdate, r.status))
		conn.commit()
	finally:
		conn.close()
	return 1


@frappe.whitelist(methods=["POST"])
def switch(db_name, carry_session=0):
	"""同步：在本请求内换库并返回。carry_session=1 时先把本会话行抄进目标库。"""
	log(f"switch -> {db_name} carry={carry_session} from {frappe.conf.db_name}")
	carried = _carry_session(frappe.session.sid, db_name) if int(carry_session) else 0
	took = _switch_db(db_name)
	write_status(state="done", kind="switch", db_name=db_name, took=took)
	log(f"switch done {took}s")
	return {"took": took, "carried": carried, "from": frappe.conf.db_name, "to": db_name}


def _restore_job(sql, carry_sid=None):
	"""全量恢复（同 restore.sh 的 bench restore，不带 migrate），在后台进程里跑。"""
	t0 = time.monotonic()
	write_status(state="running", kind="restore", sql=sql)
	saved = None
	if carry_sid:
		saved = frappe.db.sql("select sid, user, sessiondata, ipaddress, lastupdate, status from tabSessions where sid=%s",
			carry_sid, as_dict=True)
	frappe.db.commit()
	p = subprocess.run(["bench", "--site", SITE, "restore", "--force", "--db-root-password", ROOT_PW, sql],
		cwd=BENCH, capture_output=True, text=True)
	took = round(time.monotonic() - t0, 2)
	carried = 0
	if p.returncode == 0 and saved:
		import pymysql

		r = saved[0]
		conn = pymysql.connect(host="mariadb", user="root", password=ROOT_PW, database=frappe.conf.db_name, charset="utf8mb4")
		with conn.cursor() as c:
			c.execute("delete from tabSessions where sid=%s", (r.sid,))
			c.execute("insert into tabSessions (sid, user, sessiondata, ipaddress, lastupdate, status) values (%s,%s,%s,%s,%s,%s)",
				(r.sid, r.user, r.sessiondata, r.ipaddress, r.lastupdate, r.status))
		conn.commit()
		conn.close()
		carried = 1
	write_status(state="done" if p.returncode == 0 else "failed", kind="restore", took=took, rc=p.returncode,
		carried=carried, tail=(p.stdout + p.stderr)[-600:])
	log(f"restore job rc={p.returncode} {took}s")


@frappe.whitelist(methods=["POST"])
def restore_sync(sql, carry_session=0):
	"""同步：本请求内跑完全量恢复才返回。"""
	log(f"restore_sync {sql}")
	_restore_job(sql, frappe.session.sid if int(carry_session) else None)
	with open(STATUS, encoding="utf-8") as f:
		return json.load(f)


@frappe.whitelist(methods=["POST"])
def restore_async(sql, carry_session=0):
	"""异步：经正式的 RQ worker（bench start 起的那个）提交后台任务，立即返回；前端轮询 status_file。
	worker 进程里没有 frappe.sa_probe 模块，故任务方法用框架自带的 frappe.utils.execute_in_shell，
	由 shell 跑 bench restore 并把结果写进状态文件——worker 侧走的仍是正式的取任务、建站点上下文、跑完收尾那条路径。"""
	log(f"restore_async {sql}")
	write_status(state="queued", kind="restore", sql=sql)
	cmd = (f"cd {BENCH} && t0=$(date +%s%N) && "
		f"bench --site {SITE} restore --force --db-root-password {ROOT_PW} {sql} > {BENCH}/logs/sa-restore-async.log 2>&1; "
		f"rc=$?; t1=$(date +%s%N); "
		f"echo \"{{\\\"state\\\": \\\"$([ $rc = 0 ] && echo done || echo failed)\\\", \\\"kind\\\": \\\"restore\\\", "
		f"\\\"rc\\\": $rc, \\\"took_ms\\\": $(( (t1 - t0) / 1000000 )), \\\"t\\\": $(( t1 / 1000000000 ))}}\" > {STATUS}")
	job = frappe.enqueue("frappe.utils.execute_in_shell", queue="long", timeout=1800, cmd=cmd)
	return {"queued": True, "job": job.id if job else None}


@frappe.whitelist(methods=["POST"])
def backup_now(mode="bench"):
	"""V-09：前端触发存快照。mode=bench 走 bench backup；mode=clone 走整库复制到新库（V-01 ② 的快照形态）。"""
	t0 = time.monotonic()
	if mode == "bench":
		p = subprocess.run(["bench", "--site", SITE, "backup"], cwd=BENCH, capture_output=True, text=True)
		ok, extra = p.returncode == 0, p.stdout[-300:]
	else:
		target = f"{frappe.conf.db_name}_snap{int(time.time())}"
		cmd = (f"mariadb -h mariadb -uroot -p{ROOT_PW} -e 'create database `{target}`' && "
			f"mariadb-dump -h mariadb -uroot -p{ROOT_PW} --single-transaction --quick --routines {frappe.conf.db_name} | "
			f"mariadb -h mariadb -uroot -p{ROOT_PW} {target}")
		p = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
		ok, extra = p.returncode == 0, target
	took = round(time.monotonic() - t0, 2)
	log(f"backup_now {mode} ok={ok} {took}s")
	return {"ok": ok, "took": took, "extra": extra, "stderr": p.stderr[-300:]}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def marker():
	"""本请求实际连着哪个库、库里的快照标记、当前会话用户、GL 条数——用来判定换库后是否真在新库上服务。"""
	m = frappe.db.sql("select value from tabSingles where doctype='SA Probe' and field='marker'")
	return {"conf_db": frappe.conf.db_name, "connected_db": frappe.db.sql("select database()")[0][0],
		"marker": m[0][0] if m else None, "user": frappe.session.user, "pid": os.getpid(),
		"gl": frappe.db.count("GL Entry")}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def status_file():
	try:
		with open(STATUS, encoding="utf-8") as f:
			return json.load(f)
	except FileNotFoundError:
		return {}


for _name in ("switch", "restore_sync", "restore_async", "backup_now", "status_file", "marker", "_restore_job"):
	setattr(mod, _name, globals()[_name])
mod._switch_db = _switch_db

if __name__ == "__main__":
	os.chdir(f"{BENCH}/sites")
	from frappe.app import serve

	log("serve start")
	serve(port=6787, site=SITE, sites_path=".", no_reload=True)
