"""Native switch acceptance fixture; only the s8dev temporary site is writable."""
import json
import os
import re
import subprocess
from pathlib import Path

import frappe

bench = Path('/workspace/frappe-bench')
os.chdir(bench / 'sites')
site = 's8dev.localhost'
frappe.init(site=site, sites_path=str(bench / 'sites'))
frappe.connect()
frappe.set_user('Administrator')
assert frappe.local.site == site
assert not frappe.conf.get('scheduler_enabled')
from frappe_debug.demo import registry, snapshot
from frappe_debug.demo.config import get_demo_config
from frappe_debug.demo.progress import get_progress, save_progress

assert registry.get_registry() == {'base_db': None, 'acts': {}}, 'Existing evidence must not be overwritten'
base_db = frappe.conf.db_name
original_progress = get_progress()
state_file = bench / 'logs/s8-ts022-fixture.json'
state = {'base_db': base_db, 'progress': original_progress, 'counts': {}, 'root_present': bool(frappe.conf.get('root_password'))}
state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2))
if not frappe.conf.get('root_password'):
    env = Path('/workspace/docker/.env').read_text()
    match = re.search(r'^DB_ROOT_PASSWORD=(.*)$', env, re.M)
    password = match.group(1).strip().strip(chr(34)).strip(chr(39)) if match else '123'
    subprocess.run(['bench', '--site', site, 'set-config', 'root_password', password], check=True, capture_output=True)
    frappe.conf.root_password = password
try:
    config = get_demo_config()
    refs = original_progress.get('refs') or {}
    if not refs.get('sales_order'):
        refs['sales_order'] = frappe.db.get_value('Sales Order', {}, 'name')
    assert refs['sales_order']
    for act in (5, 6, 7, 8):
        spec = config['acts'][act - 1]
        save_progress(act=act, step=0, refs=refs, scene_date=spec['scene_date'])
        print('SNAPSHOT', act, snapshot.take_snapshot(act), flush=True)
    state['refs'] = refs
    state['counts'] = {dt: frappe.db.count(dt) for dt in ('ToDo', 'Sales Order', 'Purchase Order', 'CRM Lead')}
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2))
finally:
    save_progress(act=original_progress['act'] or 1, step=original_progress['step'], refs=original_progress['refs'], scene_date=original_progress['scene_date'])
    if not original_progress['active']:
        frappe.db.set_single_value('Demo Progress', 'active', 0)
        frappe.db.commit()
    frappe.destroy()
