import json
from pathlib import Path

root = Path('frappe-bench/apps/frappe_china')
path = root / 'frappe_china/workspace_sidebar/business_flow.json'
data = json.loads(path.read_text(encoding='utf-8'))
additions = {
    'Master Data': [('Holiday List', 'DocType', 'Holiday List'),
                    ('Quality Inspection Parameter', 'DocType', 'Quality Inspection Parameter'),
                    ('Quality Inspection Template', 'DocType', 'Quality Inspection Template'),
                    ('Batch', 'DocType', 'Batch'), ('Salary Structure', 'DocType', 'Salary Structure'),
                    ('Salary Structure Assignment', 'DocType', 'Salary Structure Assignment'),
                    ('Stock Settings', 'DocType', 'Stock Settings'),
                    ('Manufacturing Settings', 'DocType', 'Manufacturing Settings')],
    'Buying': [('Replenishment Suggestion', 'DocType', 'Replenishment Suggestion'),
               ('Supplier Scorecard', 'DocType', 'Supplier Scorecard')],
    'Manufacturing': [('Piece Rate Summary', 'DocType', 'Piece Rate Summary'),
                      ('Capacity Load', 'Report', 'Capacity Load'),
                      ('SPC Control Chart', 'Report', 'SPC Control Chart'),
                      ('SPC Chart', 'Page', 'spc-chart'),
                      ('Replenishment Strategy Comparison', 'Report', 'Replenishment Strategy Comparison')],
}
existing = {item.get('link_to') for item in data['items'] if item['type'] == 'Link'}
items, section = [], None
def append_section():
    for label, kind, target in additions.get(section, []):
        if target not in existing:
            items.append(dict(type='Link', label=label, link_type=kind, child=1,
                              indent=0, collapsible=1, keep_closed=0, link_to=target))
for item in data['items']:
    if item['type'] == 'Section Break':
        append_section()
        section = item['label']
    items.append(item)
append_section()
data['items'] = items
data['modified'] = '2026-10-21 21:51:00.000000'
assert sum(item['type'] == 'Link' for item in items) == 66
path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
readme = root / 'README.md'
s = readme.read_text(encoding='utf-8').replace('7 个分节、51 个入口', '7 个分节、66 个入口')
s = s.replace('承载补货建议单；', '承载补货建议单与补货策略对比报表；')
readme.write_text(s, encoding='utf-8', newline='\n')
print('Business Flow: 7 sections, 66 links (15 added per D discussion step 9)')
