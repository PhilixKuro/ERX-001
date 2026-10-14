import copy,json,os,subprocess
from pathlib import Path
import frappe
ROOT=Path('/workspace/Spike'); SOURCE=Path('/workspace/frappe-bench/apps/frappe_china/frappe_china/workspace_sidebar/business_flow.json'); original=json.loads(SOURCE.read_text())
def state():
 os.chdir('/workspace/frappe-bench/sites');frappe.init(site='test.localhost',sites_path='.');frappe.connect()
 try:return json.loads(frappe.as_json({'own':frappe.get_doc('Workspace Sidebar','Business Flow').as_dict(),'cn':frappe.get_doc('Workspace Sidebar','CN Tax').as_dict()}))
 finally:frappe.destroy();os.chdir('/workspace/frappe-bench')
def migrate(label):
 with (ROOT/f'P1S6R4-migrate-future-{label}.log').open('w') as log: assert subprocess.call(['/home/frappe/.local/bin/bench','--site','test.localhost','migrate'],cwd='/workspace/frappe-bench',stdout=log,stderr=subprocess.STDOUT)==0
before=state();probe=copy.deepcopy(original);probe['modified']='2099-01-01 00:00:00.000000';probe['items'][1]['label']='S6 Migration Probe';SOURCE.write_text(json.dumps(probe,ensure_ascii=False,indent=1)+'\n');migrate('probe');changed=state();assert changed['own']['items'][1]['label']=='S6 Migration Probe'
original['modified']='2099-01-01 00:00:00.000001';SOURCE.write_text(json.dumps(original,ensure_ascii=False,indent=1)+'\n');migrate('restore');after=state();assert after['own']['items'][1]['label']=='Company';assert after['cn']==before['cn'];(ROOT/'P1S6R4-migration-future.json').write_text(json.dumps({'pass':True,'probe_imported':True,'restored':True,'cn_tax_unchanged':True},indent=2));print(json.dumps({'pass':True,'probe_imported':True,'restored':True,'cn_tax_unchanged':True}))
