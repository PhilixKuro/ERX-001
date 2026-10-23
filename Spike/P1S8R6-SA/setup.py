import json, os, pathlib, secrets, subprocess, sys
import pymysql
BENCH=pathlib.Path('/workspace/frappe-bench'); SITE='s8ht015.localhost'
compose=json.load(sys.stdin); pw=compose['services']['mariadb']['environment']['MYSQL_ROOT_PASSWORD']
cfg=json.loads((BENCH/'sites/s8dev.localhost/site_config.json').read_text()); src=cfg['db_name']
conn=pymysql.connect(host='mariadb', user='root', password=pw, autocommit=True)
user='_ht015_sa'; password=secrets.token_urlsafe(24)
with conn.cursor() as c:
 c.execute('CREATE USER IF NOT EXISTS %s@%s IDENTIFIED BY %s',(user,'%',password))
 c.execute('ALTER USER %s@%s IDENTIFIED BY %s',(user,'%',password))
 for db in ['_ht015_sa_a','_ht015_sa_b']:
  c.execute('CREATE DATABASE `'+db+'`')
  c.execute('GRANT ALL PRIVILEGES ON `'+db+'`.* TO %s@%s',(user,'%'))
  env=dict(os.environ,MYSQL_PWD=pw)
  dump=subprocess.Popen(['mariadb-dump','-h','mariadb','-uroot','--single-transaction','--quick','--routines',src],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
  load=subprocess.run(['mariadb','-h','mariadb','-uroot',db],stdin=dump.stdout,capture_output=True,env=env); dump.stdout.close(); _,err=dump.communicate()
  assert load.returncode==dump.returncode==0,(err,load.stderr)
  c.execute('CREATE TABLE `'+db+'`.`ht015_audit` (label varchar(120), marker varchar(120), pid int, ts double) ENGINE=InnoDB')
  c.execute('INSERT INTO `'+db+'`.`tabSingles` (doctype,field,value) VALUES (%s,%s,%s)',('HT015 Probe','marker',db))
  c.execute('UPDATE `'+db+'`.`tabScheduled Job Type` SET stopped=1')
  c.execute('DELETE FROM `'+db+'`.`tabSingles` WHERE doctype=%s AND field=%s',('System Settings','enable_scheduler'))
  c.execute('INSERT INTO `'+db+'`.`tabSingles` (doctype,field,value) VALUES (%s,%s,%s)',('System Settings','enable_scheduler','1'))
  print(json.dumps({'cloned':db}),flush=True)
cfg.update(db_name='_ht015_sa_a',db_user=user,db_password=password,db_host='mariadb',pause_scheduler=1,disable_scheduler=0)
site=BENCH/'sites'/SITE; site.mkdir(exist_ok=True)
for folder in ['private','public','locks','logs']: (site/folder).mkdir(exist_ok=True)
(site/'site_config.json').write_text(json.dumps(cfg,indent=1)+'\n')
conn.close()
print(json.dumps({'site':SITE,'ready':True}),flush=True)
