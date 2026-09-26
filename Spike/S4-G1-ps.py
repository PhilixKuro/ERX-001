# -*- coding: utf-8 -*-
import json, csv, os, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = os.path.join('D:', os.sep, 'ERX-001', 'Reference', 'zelin-tech-erpnext_china', 'erpnext_china')

ps = json.load(open(os.path.join(B, 'fixtures', 'property_setter.json'), encoding='utf-8'))
print('===== fixtures/property_setter.json : %d entries =====' % len(ps))
bydt = collections.Counter(p.get('doc_type') for p in ps)
byprop = collections.Counter(p.get('property') for p in ps)
print('  by doc_type: %s' % dict(bydt))
print('  by property: %s' % dict(byprop))
print('  --- full list ---')
for p in ps:
    print('    %-26s %-22s %-14s value=%s' % (p.get('doc_type'), p.get('field_name'),
                                              p.get('property'), repr(p.get('value'))[:44]))

print()
print('===== overlap check: property_setter.json  vs  setup/field_property.csv =====')
csvrows = [r for r in csv.reader(open(os.path.join(B, 'setup', 'field_property.csv'), encoding='utf-8')) if r]
csvkeys = {(r[0], r[1], r[2]) for r in csvrows}
jsonkeys = {(p.get('doc_type'), p.get('field_name'), p.get('property')) for p in ps}
print('  csv keys=%d  json keys=%d  intersection=%d' % (len(csvkeys), len(jsonkeys), len(csvkeys & jsonkeys)))
print('  overlapping: %s' % sorted(csvkeys & jsonkeys))
print('  => two independent mechanisms write Property Setter:')
print('     (a) fixtures/property_setter.json  -> frappe sync_fixtures (directory scan)')
print('     (b) setup/field_property.csv       -> install.py change_field_property()')

print()
print('===== fixtures/cash_flow_code.json =====')
cf = json.load(open(os.path.join(B, 'fixtures', 'cash_flow_code.json'), encoding='utf-8'))
print('  %d Cash Flow Code records' % len(cf))
for c in cf:
    print('    code=%-4s seq=%-5s outflow=%s formula=%-20s party_type=%-9s %s'
          % (c.get('code'), c.get('report_sequence'), c.get('is_outflow'),
             str(c.get('formula')), str(c.get('party_type')), c.get('cash_flow_name')))
