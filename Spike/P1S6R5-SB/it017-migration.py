"""R5 IT-017 重做 SL-007 ⑥⑦（只在测试站）：一次跑完
  old    ：json 改一个 label、modified 保持原值（早于库里）→ migrate → 库里 label 与 modified 都不变
  new    ：同一 label、modified 取当前时刻 → migrate → 库里变为新 label、modified 等于该时刻
  restore：原内容、modified 取当前时刻 → migrate → 库里 label 回原值
  again  ：不改文件再 migrate → 库里 modified 不变（不重复导入）
最后把 json 按字节还原成实验前的文件（不写库，不改 git 跟踪内容）。不用 frappe.db.set_value。
其余 app 的 Desktop Icon／Workspace Sidebar／Workspace Sidebar Item 行与 CN Tax 前后逐字比对。"""
import copy, json, os, shutil, subprocess, datetime
from pathlib import Path
import frappe

ROOT = Path('/workspace/Spike/P1S6R5-SB/it017')
SOURCE = Path('/workspace/frappe-bench/apps/frappe_china/frappe_china/workspace_sidebar/business_flow.json')
BACKUP = ROOT / 'business_flow.json.orig'
PROBE = 'S6 IT-017 Probe'
raw = SOURCE.read_bytes()
BACKUP.write_bytes(raw)
original = json.loads(raw)
report = {'json_modified_before': original['modified'], 'rounds': []}

def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

def state():
    os.chdir('/workspace/frappe-bench/sites'); frappe.init(site='test.localhost', sites_path='.'); frappe.connect()
    try:
        others = {}
        for dt in ('Desktop Icon', 'Workspace Sidebar'):
            others[dt] = frappe.get_all(dt, filters={'app': ('!=', 'frappe_china')}, fields=['name', 'modified', 'hidden' if dt == 'Desktop Icon' else 'title', 'idx'], order_by='name')
        names = [x.name for x in others['Workspace Sidebar']]
        others['Workspace Sidebar Item'] = frappe.get_all('Workspace Sidebar Item', filters={'parent': ('in', names)}, fields=['name', 'parent', 'label', 'modified', 'idx'], order_by='name')
        own = frappe.get_doc('Workspace Sidebar', 'Business Flow')
        return json.loads(frappe.as_json({
            'others': others,
            'cn_tax': frappe.db.get_value('Workspace Sidebar', 'CN Tax', ['modified', 'title'], as_dict=True),
            'icon': frappe.db.get_value('Desktop Icon', 'Business Flow', ['modified', 'label', 'idx', 'hidden'], as_dict=True),
            'own': {'modified': own.modified, 'label_1': own.items[1].label, 'items': len(own.items)},
        }))
    finally:
        frappe.destroy(); os.chdir('/workspace/frappe-bench')

def migrate(label):
    started = now()
    with (ROOT / f'migrate-{label}.log').open('w') as log:
        code = subprocess.call(['/home/frappe/.local/bin/bench', '--site', 'test.localhost', 'migrate'], cwd='/workspace/frappe-bench', stdout=log, stderr=subprocess.STDOUT)
    assert code == 0, (label, code)
    return started

def write(data):
    SOURCE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

def save():
    (ROOT / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

def record(name, json_modified, expect_label, started):
    s = state()
    row = {'name': name, 'migrate_started': started, 'json_modified': json_modified, 'json_label_1': expect_label,
           'db_modified': s['own']['modified'], 'db_label_1': s['own']['label_1'], 'db_items': s['own']['items']}
    report['rounds'].append(row); save()
    return s, row

before = state(); report['before'] = before; save()
assert before['own']['label_1'] == original['items'][1]['label']
try:
    # old：modified 保持 json 原值，而库里已更新（R7 TS-022 的 save 把它改到 2026-10-12）
    assert original['modified'] < before['own']['modified'], 'json modified must be older than db for the old round'
    probe = copy.deepcopy(original); probe['items'][1]['label'] = PROBE
    write(probe); started = migrate('old')
    s, row = record('old', probe['modified'], PROBE, started)
    row['pass'] = (s['own']['label_1'] == original['items'][1]['label'] and s['own']['modified'] == before['own']['modified']); save()
    assert row['pass'], row
    # new：同一 label，modified 取当前时刻
    probe['modified'] = now(); write(probe); started = migrate('new')
    s, row = record('new', probe['modified'], PROBE, started)
    row['pass'] = (s['own']['label_1'] == PROBE and s['own']['modified'] == probe['modified']); save()
    assert row['pass'], row
finally:
    # restore：原内容，modified 取当前时刻
    restored = copy.deepcopy(original); restored['modified'] = now(); write(restored); started = migrate('restore')
    s, row = record('restore', restored['modified'], original['items'][1]['label'], started)
    row['pass'] = (s['own']['label_1'] == original['items'][1]['label'] and s['own']['modified'] == restored['modified']); save()
    # again：不改文件再跑一次
    started = migrate('again')
    s2, row2 = record('again', restored['modified'], original['items'][1]['label'], started)
    row2['pass'] = (s2['own']['modified'] == s['own']['modified'] and s2['own']['label_1'] == original['items'][1]['label']); save()
    # json 按字节还原为实验前文件
    shutil.copyfile(BACKUP, SOURCE)
    report['json_bytes_restored'] = SOURCE.read_bytes() == raw
after = state(); report['after'] = after
report['others_unchanged'] = before['others'] == after['others']
report['cn_tax_unchanged'] = before['cn_tax'] == after['cn_tax']
report['icon_unchanged'] = before['icon'] == after['icon']
report['pass'] = all(r['pass'] for r in report['rounds']) and report['others_unchanged'] and report['cn_tax_unchanged'] and report['icon_unchanged'] and report['json_bytes_restored']
save()
print(json.dumps({k: report[k] for k in ('pass', 'json_modified_before', 'others_unchanged', 'cn_tax_unchanged', 'icon_unchanged', 'json_bytes_restored')} | {'rounds': report['rounds'], 'before_db': before['own'], 'after_db': after['own']}, ensure_ascii=False))
