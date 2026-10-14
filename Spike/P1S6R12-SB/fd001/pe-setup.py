# R12 SB FD-001：测试站造一张开账收付款凭证（PE）供实点。prepare／cleanup／check。
# 只动本脚本建的东西：PE 以 remarks 标记认；公司「预收预付记入单独科目」开关记下原值，cleanup 还原。
import os, sys, json, frappe
COMPANY = '_S6R6 测试公司'
CUSTOMER = '_S6R6 验收客户'
MARK = 'P1-S6-R12 SB FD-001 probe'
STATE = '/workspace/Spike/P1S6R12-SB/fd001/state.json'
os.chdir('/workspace/frappe-bench/sites'); frappe.init(site='test.localhost', sites_path='.'); frappe.connect(); frappe.set_user('Administrator')

def mine():
    # remarks 提交时被上游重写，故按 state.json 里记下的单号认
    names = json.load(open(STATE)).get('pe', []) if os.path.exists(STATE) else []
    return frappe.get_all('Payment Entry', filters={'name': ('in', names or ['-'])}, fields=['name', 'docstatus', 'is_opening', 'paid_from'])

try:
    action = sys.argv[1]
    if action == 'prepare':
        assert not mine(), 'probe PE already exists'
        flag = frappe.db.get_value('Company', COMPANY, 'book_advance_payments_in_separate_party_account')
        state = {'flag_before': flag, 'pe': []}
        frappe.db.set_value('Company', COMPANY, 'book_advance_payments_in_separate_party_account', 1)
        from erpnext.accounts.doctype.payment_entry.payment_entry import get_party_details
        pe = frappe.new_doc('Payment Entry')
        pe.update({'payment_type': 'Receive', 'company': COMPANY, 'posting_date': '2026-10-01',
                   'mode_of_payment': 'Cash', 'party_type': 'Customer', 'party': CUSTOMER,
                   'paid_amount': 100, 'received_amount': 100, 'is_opening': 'Yes', 'remarks': MARK})
        details = get_party_details(COMPANY, 'Customer', CUSTOMER, '2026-10-01')
        pe.paid_from = details['party_account']
        pe.paid_from_account_currency = details['party_account_currency']
        pe.paid_to = frappe.db.get_value('Company', COMPANY, 'default_cash_account')
        pe.paid_to_account_currency = 'CNY'
        pe.insert(); pe.submit()
        state['pe'].append(pe.name)
        json.dump(state, open(STATE, 'w'))
    elif action == 'cleanup':
        for row in mine():
            doc = frappe.get_doc('Payment Entry', row.name)
            if doc.docstatus == 1: doc.cancel()
            frappe.delete_doc('Payment Entry', row.name, force=1)
        state = json.load(open(STATE))
        frappe.db.set_value('Company', COMPANY, 'book_advance_payments_in_separate_party_account', state['flag_before'])
    frappe.db.commit()
    print(json.dumps({'action': action, 'probe': mine(),
                      'flag': frappe.db.get_value('Company', COMPANY, 'book_advance_payments_in_separate_party_account')},
                     default=str, ensure_ascii=False))
finally:
    frappe.destroy()
