# -*- coding: utf-8 -*-
import os, sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.join('D:', os.sep, 'ERX-001', 'Reference', 'zelin-tech-erpnext_china', 'erpnext_china')
SEP = os.sep

print('===== DocType / Report / Workspace JSON metadata =====')
for root, dirs, files in os.walk(BASE):
    for fn in sorted(files):
        if not fn.endswith('.json'):
            continue
        fp = os.path.join(root, fn)
        rel = os.path.relpath(fp, BASE).replace(SEP, '/')
        try:
            d = json.load(open(fp, encoding='utf-8'))
        except Exception as e:
            print('  %-70s !! parse error: %s' % (rel, e))
            continue
        if isinstance(d, list):
            dts = sorted({str(x.get('doctype')) for x in d if isinstance(x, dict)})
            print('  %-70s LIST len=%-4d doctypes=%s' % (rel, len(d), dts))
            continue
        dt, mod = d.get('doctype'), d.get('module')
        extra = []
        if dt == 'DocType':
            flds = d.get('fields', [])
            extra = ['issingle=%s' % d.get('issingle'), 'istable=%s' % d.get('istable'),
                     'custom=%s' % d.get('custom'), 'fields=%d' % len(flds)]
            links = sorted({str(f.get('options')) for f in flds
                            if f.get('fieldtype') in ('Link', 'Table', 'Table MultiSelect')})
            extra.append('links=%s' % links)
        elif dt == 'Report':
            extra = ['ref_doctype=%s' % d.get('ref_doctype'), 'report_type=%s' % d.get('report_type'),
                     'is_standard=%s' % d.get('is_standard')]
        elif dt == 'Workspace':
            extra = ['label=%s' % d.get('label'), 'icon=%s' % d.get('icon')]
        print('  %-70s doctype=%-10s module=%-14s %s' % (rel, dt, mod, ' '.join(extra)))

print()
print('===== setup/field_property.csv (consumed by install.py change_field_property) =====')
for i, r in enumerate(csv.reader(open(os.path.join(BASE, 'setup', 'field_property.csv'), encoding='utf-8')), 1):
    print('  %2d %s' % (i, r))

print()
print('===== tax_template.json : SME(2024) block detail =====')
tt = json.load(open(os.path.join(BASE, 'chart_of_accounts', 'company_default', 'tax_template.json'), encoding='utf-8'))
sme = tt['chart_of_accounts']['小企业会计准则(2024)']
for sect, items in sme.items():
    print('  -- %s (%d) --' % (sect, len(items)))
    for it in items:
        heads = [(x.get('account_head', {}).get('account_number'),
                  x.get('account_head', {}).get('account_name'), x.get('rate'))
                 for x in it.get('taxes', [])]
        print('     title=%-18s tax_category=%-16s taxes=%s' % (it.get('title'), it.get('tax_category'), heads))
