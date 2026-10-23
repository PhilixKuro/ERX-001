"""Verify disabled scheduler then clean exact probe-owned resources."""
import json, os, shutil, sys
from pathlib import Path
import pymysql
import frappe
from rq import Queue
from rq.job import Job

BENCH=Path('/workspace/frappe-bench'); SITE='s8ht015.localhost'
os.chdir(BENCH/'sites')
frappe.init(SITE); frappe.connect()
assert frappe.conf.pause_scheduler == 1
from frappe.utils.scheduler import enqueue_events_for_site
from frappe.utils.background_jobs import get_redis_conn
queue_conn=get_redis_conn()
q=Queue('ht015-sa-nofork',connection=queue_conn)
before=q.count
frappe.destroy(); enqueue_events_for_site(SITE)
assert q.count == before == 0
print(json.dumps(dict(disabled_scheduler=True, queue_before=before, queue_after=q.count)))
frappe.init(SITE); frappe.connect()
cache=frappe.cache
counts={}
for db in ('_ht015_sa_a','_ht015_sa_b','_ht015_sa_detached'):
 keys=cache.keys((db+'|*').encode()); counts[db]=len(keys)
 if keys: cache.delete(*keys)
frappe.destroy()
deleted_jobs=0
for key in list(queue_conn.scan_iter(match='rq:job:*')):
 raw=queue_conn.hget(key,'origin')
 if raw in (b'ht015-sa-fork',b'ht015-sa-nofork'):
  job=Job.fetch(key.decode().removeprefix('rq:job:'),connection=queue_conn)
  job.delete(remove_from_queue=True); deleted_jobs+=1
deleted_queue_keys=0
for pattern in ('rq:*ht015-sa-fork*','rq:*ht015-sa-nofork*'):
 for key in list(queue_conn.scan_iter(match=pattern)):
  queue_conn.delete(key); deleted_queue_keys+=1
pw=json.load(sys.stdin)['services']['mariadb']['environment']['MYSQL_ROOT_PASSWORD']
conn=pymysql.connect(host='mariadb',user='root',password=pw,autocommit=True)
dbs=('_ht015_sa_a','_ht015_sa_b','_ht015_sa_detached')
with conn.cursor() as c:
 for db in dbs: c.execute('DROP DATABASE `'+db+'`')
 c.execute('DROP USER %s@%s',('_ht015_sa','%'))
 c.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME LIKE '_ht015%'")
 remaining=c.fetchall(); assert not remaining,remaining
conn.close()
target=(BENCH/'sites'/SITE).resolve()
assert target.parent == (BENCH/'sites').resolve() and target.name == SITE
shutil.rmtree(target)
print(json.dumps(dict(cache_removed=counts,deleted_jobs=deleted_jobs,deleted_queue_keys=deleted_queue_keys,
 databases_dropped=list(dbs),user_dropped='_ht015_sa',site_removed=not target.exists(),remaining_databases=remaining)))
