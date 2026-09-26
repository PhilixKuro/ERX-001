import json, collections, io, sys
p = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china\fixtures\property_setter.json'
with open(p, encoding='utf-8') as f:
    data = json.load(f)
print('total records:', len(data))
cnt = collections.Counter(d.get('property') for d in data)
print('--- property histogram ---')
for k, v in cnt.most_common():
    print('  %-28s %d' % (k, v))
print('--- doctype_or_field histogram ---')
for k, v in collections.Counter(d.get('doctype_or_field') for d in data).most_common():
    print('  %-20s %d' % (k, v))
labels = [d for d in data if d.get('property') == 'label']
print('--- label records: %d ---' % len(labels))
print('idx | doc_type | field_name | doctype_or_field | property_type | value')
for i, d in enumerate(labels, 1):
    print('%2d | %s | %s | %s | %s | %s' % (
        i, d.get('doc_type'), d.get('field_name'), d.get('doctype_or_field'),
        d.get('property_type'), d.get('value')))
print('--- keys present on a label record ---')
print(sorted(labels[0].keys()))
