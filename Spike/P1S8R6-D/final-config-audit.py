"""Audit final narration against the site's zh translations and routing rules."""
import csv
import json
import os

import frappe
from frappe.translate import get_all_translations

os.chdir('/workspace/frappe-bench/sites')
frappe.init(site='s8dev.localhost', sites_path='.')
frappe.connect()
try:
    from frappe_debug.demo.config import CONFIG_PATH, get_demo_config
    config = get_demo_config()
    translations = get_all_translations('zh')
    steps = [step for act in config['acts'] for step in act['steps'] if step.get('say')]
    terms = ['Quotation','Sales Order','Purchase Order','Purchase Receipt','Purchase Invoice','Payment Entry',
             'Work Order','Job Card','SPC Chart','Piece Rate Summary','Supplier Scorecard','Capacity Load',
             'Material Request','Replenishment Suggestion']
    output = {'narration_count': len(steps), 'forbidden': [word for word in ('今天','今日')
              if any(word in step['say'] for step in steps)],
              'awesomebar_actions': [step for act in config['acts'] for step in act['steps']
              if 'awesomebar' in json.dumps(step,ensure_ascii=False).lower()],
              'routes': [act['route'] for act in config['acts']],
              'translations': {term: translations.get(term,term) for term in terms},
              'items': []}
    with open('/workspace/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv',
              encoding='utf-8-sig',newline='') as stream:
        rows = {row[0]: row[1] for row in csv.reader(stream) if len(row)>1}
    for source in ('SPC Chart','Capacity Load','Piece Rate Summary'):
        output['items'].append({'source':source,'csv':rows.get(source),
                                'effective':translations.get(source,source)})
    print(json.dumps(output,ensure_ascii=False,default=str))
    assert len(config['acts']) == 9 and not output['forbidden'] and not output['awesomebar_actions']
    assert all('Business%20Flow' in route for route in output['routes'])
    assert translations.get('Work Order') == '生产工单'
    assert translations.get('Job Card') == '生产任务单'
    assert translations.get('SPC Chart') == '过程控制图'
    assert translations.get('Supplier Scorecard') == '供应商评分卡'
finally:
    frappe.db.rollback()
    frappe.destroy()
