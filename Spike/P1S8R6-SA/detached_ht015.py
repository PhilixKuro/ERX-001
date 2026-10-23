"""A6 explicit-source detached clone during switch, reads credential from stdin."""
import json, os, shlex, subprocess, sys, time
from pathlib import Path
import pymysql
import frappe

BENCH=Path('/workspace/frappe-bench'); SITE='s8ht015.localhost'
CONFIG=BENCH/'sites'/SITE/'site_config.json'
STATE=BENCH/'logs/ht015-state'
SRC='_ht015_sa_a'; DST='_ht015_sa_detached'

def switch(db):
 os.chdir(BENCH/'sites'); frappe.init(SITE,force=True); frappe.connect()
 from frappe.installer import update_site_config
 from frappe.config import clear_site_config_cache
 update_site_config('db_name',db); clear_site_config_cache(); frappe.destroy()

pw=json.load(sys.stdin)['services']['mariadb']['environment']['MYSQL_ROOT_PASSWORD']
conn=pymysql.connect(host='mariadb',user='root',password=pw,autocommit=True)
original=CONFIG.read_bytes(); p=None
try:
 switch(SRC)
 with conn.cursor() as c: c.execute('CREATE DATABASE `'+DST+'`')
 # Delay only establishes that db_name has changed before the clone connects.
 command='sleep 2; set -o pipefail; mariadb-dump -h mariadb -uroot --single-transaction --quick --routines '+SRC+' | mariadb -h mariadb -uroot '+DST
 command+=' && touch '+str(STATE/'detached.ok')+' || touch '+str(STATE/'detached.fail')
 log=(BENCH/'logs/ht015-detached-child.log').open('w')
 t0=time.monotonic()
 p=subprocess.Popen(['bash','-c',command],start_new_session=True,env=dict(os.environ,MYSQL_PWD=pw),stdout=log,stderr=subprocess.STDOUT)
 switch('_ht015_sa_b'); switched=time.monotonic()-t0
 p.wait(timeout=180); log.close()
 with conn.cursor() as c:
  c.execute('SELECT value FROM `'+DST+'`.tabSingles WHERE doctype=%s AND field=%s',('HT015 Probe','marker'))
  marker=c.fetchone()[0]
 assert (STATE/'detached.ok').exists() and not (STATE/'detached.fail').exists()
 assert marker==SRC and json.loads(CONFIG.read_text())['db_name']=='_ht015_sa_b'
 print(json.dumps(dict(pid=p.pid,session_leader=True,switch_elapsed=switched,clone_elapsed=time.monotonic()-t0,source=SRC,dest=DST,marker=marker,current_db='_ht015_sa_b',ok=True)))
finally:
 if p is not None and p.poll() is None: p.terminate(); p.wait(timeout=10)
 frappe.destroy(); CONFIG.write_bytes(original); conn.close()
