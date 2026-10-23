"""Extend the disposable preview, then rescreen its actual quality schedule."""
import json
import os
from datetime import timedelta
from pathlib import Path

import frappe

os.chdir('/workspace/frappe-bench/sites')
frappe.init(site='s8ts023preview.localhost', sites_path='.')
frappe.connect()
frappe.set_user('Administrator')
try:
    from frappe_debug.demo.registry import get_registry
    from frappe_debug.scenario.params import load_scenario
    from frappe_debug.scenario.quality import export_quality_sample_plan
    from frappe_debug.scenario.runner import _last_generated_date, generate

    registry = get_registry()
    assert frappe.conf.db_name == registry['work_db']
    sc = load_scenario()
    assert str(sc.E) == '2026-10-24'
    last = _last_generated_date(sc)
    plan = Path(frappe.get_site_path('private', 'frappe_debug', 'quality-plan.json'))
    archived = plan.with_name('quality-plan-E20261023-archived.json')
    if plan.exists():
        assert not archived.exists()
        plan.rename(archived)
    if last < sc.E - timedelta(days=1):
        result = generate(last + timedelta(days=1), sc.E - timedelta(days=1), preview_quality_schedule=True)
        print(json.dumps(result.__json__(), default=str), flush=True)
    exported = export_quality_sample_plan()
    payload = json.loads(Path(exported).read_text())
    print(json.dumps({'path':exported, 'E':str(sc.E), 'groups':len(payload['manifest']), 'attempts':payload['attempts'], 'schedule_fingerprint':payload['schedule_fingerprint']}, ensure_ascii=False), flush=True)
finally:
    frappe.destroy()
