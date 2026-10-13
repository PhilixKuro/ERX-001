# R9 TS-036 第 4 步补（由 Spike/P1S6R7/ts023/je_draft.py 复制，只改状态文件）：演示线另用到的 Journal Entry（期初）——复制已提交的期初凭证为草稿，供提交确认框；写回造数状态文件
import json, os
from pathlib import Path
import frappe
STATE = Path('/workspace/Spike/P1S6R9-closed-loop-erx.json')
os.chdir('/workspace/frappe-bench/sites'); frappe.init(site='erx.localhost', sites_path='.'); frappe.connect(); frappe.set_user('Administrator')
try:
    state = json.loads(STATE.read_text(encoding='utf-8'))
    if 'je_draft' not in state:
        doc = frappe.copy_doc(frappe.get_doc('Journal Entry', state['opening'])); doc.insert()
        state['je_draft'] = doc.name; state['docs'].append(['Journal Entry', doc.name]); frappe.db.commit()
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    print(state['opening'], state['je_draft'], frappe.db.get_value('Journal Entry', state['je_draft'], 'docstatus'))
    print('stock reconciliation', frappe.db.count('Stock Reconciliation'))
finally:
    frappe.db.rollback(); frappe.destroy()
