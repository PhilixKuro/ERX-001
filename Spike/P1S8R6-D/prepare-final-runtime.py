"""Refresh only the dedicated acceptance runtime and its verified SPC plan."""
import csv
import json
import os
import shutil
import signal
import subprocess
from pathlib import Path

bench = Path('/workspace/frappe-bench')
source = bench / 'sites/s8ts023preview.localhost/private/frappe_debug/quality-plan.json'
target = bench / 'sites/s8dev.localhost/private/frappe_debug/quality-plan.json'
old = target.with_name('quality-plan-E20261023-archived.json')
assert source.is_file() and target.is_file() and not old.exists()
payload = json.loads(source.read_text())
assert len(payload['manifest']) == 185 and payload['attempts'] == 1146
shutil.copy2(target, old)
shutil.copy2(source, target)
for pid, expected in [(66386, 'worker --queue long'), (74360, 'serve --port 6787 --noreload')]:
    command = Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\x00', b' ').decode()
    assert expected in command, command
    os.kill(pid, signal.SIGTERM)
for label, arguments in [('serve', ['--site','s8dev.localhost','serve','--port','6787','--noreload']), ('worker', ['worker','--queue','long'])]:
    with (bench / f'logs/s8-acceptance-{label}.log').open('a') as log:
        process = subprocess.Popen(['bench',*arguments], cwd=bench, stdout=log, stderr=log, start_new_session=True)
    print(json.dumps({'runtime':label,'pid':process.pid}), flush=True)
keys = {'Quotation','Material Request','Supplier Scorecard','Job Card','Work Order','Stock Entry','Delivery Note','Workstation','BOM','Sales Order','Purchase Order','Purchase Receipt','Purchase Invoice','Payment Entry','SPC Chart','Capacity Load','Piece Rate Summary','Stock and Account Value Comparison'}
with (bench / 'apps/frappe_china/frappe_china/translations/zh.csv').open(encoding='utf-8-sig', newline='') as stream:
    print(json.dumps([row for row in csv.reader(stream) if row and row[0] in keys], ensure_ascii=False))
