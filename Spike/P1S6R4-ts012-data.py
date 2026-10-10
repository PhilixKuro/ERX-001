import json
import os
from pathlib import Path

import frappe


STATE = Path('/workspace/Spike/P1S6R4-ts012-state.json')
COMPANY = '_FCT S6 TS012'


def prepare():
	assert not frappe.db.exists('Company', COMPANY)
	from frappe_china.tests.utils import make_cn_company

	company = make_cn_company(COMPANY, 'TS12')
	accounts = {
		'cash': frappe.db.get_value('Account', {'company': COMPANY, 'account_number': '1001'}),
		'equity': frappe.db.get_value('Account', {'company': COMPANY, 'account_number': '3001'}),
	}
	assert all(accounts.values()), accounts
	names = {}
	for label, is_opening in (('opening', 'Yes'), ('normal', 'No')):
		doc = frappe.get_doc({
			'doctype': 'Journal Entry', 'company': COMPANY,
			'posting_date': '2025-01-15', 'voucher_type': 'Journal Entry',
			'is_opening': is_opening, 'user_remark': 'S6 TS012 browser evidence',
		})
		doc.append('accounts', {'account': accounts['cash'], 'debit_in_account_currency': 100, 'cost_center': company.cost_center})
		doc.append('accounts', {'account': accounts['equity'], 'credit_in_account_currency': 100, 'cost_center': company.cost_center})
		doc.insert(ignore_permissions=True)
		doc.submit()
		names[label] = doc.name
	frappe.db.commit()
	state = {'company': COMPANY, 'journals': names}
	STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
	print(frappe.as_json(state))


def cleanup():
	state = json.loads(STATE.read_text(encoding='utf-8'))
	for name in state['journals'].values():
		doc = frappe.get_doc('Journal Entry', name)
		if doc.docstatus == 1:
			doc.cancel()
		entries = frappe.get_all('GL Entry', filters={'voucher_type': 'Journal Entry', 'voucher_no': name}, pluck='name')
		if entries:
			frappe.db.delete('GL Entry', {'name': ('in', entries)})
		frappe.delete_doc('Journal Entry', name, ignore_permissions=True)
	frappe.delete_doc('Company', state['company'], ignore_permissions=True)
	frappe.db.commit()
	assert not frappe.db.exists('Company', state['company'])
	assert all(not frappe.db.exists('Journal Entry', name) for name in state['journals'].values())
	state['cleanup_verified'] = True
	STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
	print(frappe.as_json(state))


def main(action):
	os.chdir('/workspace/frappe-bench/sites')
	frappe.init(site='test.localhost', sites_path='.')
	frappe.connect()
	frappe.set_user('Administrator')
	try:
		{'prepare': prepare, 'cleanup': cleanup}[action]()
	finally:
		frappe.db.rollback()
		frappe.destroy()
