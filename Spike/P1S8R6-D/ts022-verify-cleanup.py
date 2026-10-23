"""Read-only verification after the browser cleanup request outlived CDP."""
import json
import os
import subprocess
from pathlib import Path
import frappe

bench = Path('/workspace/frappe-bench')
os.chdir(bench / 'sites')
fixture = json.loads((bench / 'logs/s8-ts022-fixture.json').read_text())
frappe.init(site='s8dev.localhost', sites_path=str(bench / 'sites'))
frappe.connect()
frappe.set_user('Administrator')
try:
    from frappe_debug.demo import registry
    from frappe_debug.demo.progress import get_progress
    assert frappe.local.site == 's8dev.localhost'
    assert frappe.conf.db_name == fixture['base_db']
    assert registry.get_registry() == {'base_db': None, 'acts': {}}
    progress = get_progress()
    assert progress == fixture['progress'], (progress, fixture['progress'])
    counts = {dt: frappe.db.count(dt) for dt in fixture['counts']}
    assert counts == fixture['counts'], counts
    names = [f"{fixture['base_db']}_a{act}_{copy}" for act in (5, 6, 7, 8) for copy in ('o', 'm', 'b')]
    quoted = ','.join("'" + name + "'" for name in names)
    result = subprocess.run(['mariadb', '-h', frappe.conf.db_host, '-uroot', '-N', '-e', f'SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME IN ({quoted})'], env={**os.environ, 'MYSQL_PWD': frappe.conf.root_password}, capture_output=True, text=True, check=True)
    assert not result.stdout.strip(), 'Snapshot databases remain'
    evidence = {'site': frappe.local.site, 'base_db': frappe.conf.db_name, 'progress': progress, 'counts': counts, 'registry': registry.get_registry(), 'absent_databases': names}
    (bench / 'logs/s8-ts022-cleanup.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
    print('PASS base database, original progress/counts, empty registry and all 12 database absences')
finally:
    frappe.destroy()
