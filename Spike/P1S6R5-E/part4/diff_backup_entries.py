"""Compare pre-S6 demo backup (20261008_211805) original-entry rows with the current demo export.
Host Python, read-only. Usage: PYTHONUTF8=1 python -I diff_backup_entries.py
"""
import gzip
import json
import re
from pathlib import Path

ROOT = Path('D:/ERX-001')
DUMP = ROOT / 'docker/backups/20261008_211805-erx_localhost-database.sql.gz'
CUR = ROOT / 'Spike/P1S6R5-E/part4/probe_demo.json'
TABLES = {'tabDesktop Icon': 'Desktop Icon', 'tabWorkspace Sidebar': 'Workspace Sidebar',
          'tabWorkspace Sidebar Item': 'Workspace Sidebar Item'}


def split_rows(values):
    rows, row, field, i, inq, depth = [], [], '', 0, False, 0
    while i < len(values):
        c = values[i]
        if inq:
            if c == '\\':
                field += values[i + 1]; i += 2; continue
            if c == "'":
                inq = False
            else:
                field += c
        elif c == "'":
            inq = True
        elif c == '(' and depth == 0:
            depth = 1; row = []; field = ''
        elif c == ',' and depth == 1:
            row.append(field); field = ''
        elif c == ')' and depth == 1:
            row.append(field); rows.append(row); depth = 0
        elif depth == 1:
            field += c
        i += 1
    return rows


cols, data = {}, {v: [] for v in TABLES.values()}
current = None
pending_table, pending = None, []
with gzip.open(DUMP, 'rt', encoding='utf-8', errors='replace') as fh:
    for line in fh:
        if pending_table:
            pending.append(line)
            if line.rstrip().endswith(';'):
                for r in split_rows(''.join(pending)):
                    data[TABLES[pending_table]].append(dict(zip(cols[pending_table], r)))
                pending_table, pending = None, []
            continue
        m = re.match(r'INSERT INTO `([^`]+)` VALUES\s*$', line)
        if m and m.group(1) in TABLES:
            pending_table, pending = m.group(1), []
            continue
        m = re.match(r'CREATE TABLE `([^`]+)`', line)
        if m:
            current = m.group(1) if m.group(1) in TABLES else None
            if current:
                cols[current] = []
            continue
        if current and line.strip().startswith('`'):
            cols[current].append(line.strip().split('`')[1])
        elif current and line.startswith(')'):
            current = None
        m = re.match(r'INSERT INTO `([^`]+)` VALUES (.*);\s*$', line, re.S)
        if m and m.group(1) in TABLES:
            t = m.group(1)
            for r in split_rows(m.group(2)):
                data[TABLES[t]].append(dict(zip(cols[t], r)))

cur = json.loads(CUR.read_text(encoding='utf-8'))['original_entries']
report = {}
sidebar_names = {r['name'] for r in cur['Workspace Sidebar']}
for dt, rows in data.items():
    if dt == 'Workspace Sidebar Item':
        old = {r['name']: r for r in rows if r.get('parent') in sidebar_names}
    else:
        old = {r['name']: r for r in rows if r.get('app') != 'frappe_china'}
    new = {r['name']: r for r in cur[dt]}
    diffs = []
    for n in sorted(set(old) | set(new)):
        o, c = old.get(n), new.get(n)
        if not o or not c:
            diffs.append({'name': n, 'only_in': 'backup' if o else 'current'}); continue
        for k in ('modified', 'hidden', 'idx'):
            if k in c and str(o.get(k)) != str(c.get(k)):
                diffs.append({'name': n, 'field': k, 'backup': o.get(k), 'current': c.get(k)})
    report[dt] = {'backup_rows': len(old), 'current_rows': len(new), 'diffs': diffs[:40], 'diff_count': len(diffs)}
out = ROOT / 'Spike/P1S6R5-E/part4/diff_backup_entries.json'
out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps({k: (v['backup_rows'], v['current_rows'], v['diff_count']) for k, v in report.items()}))
