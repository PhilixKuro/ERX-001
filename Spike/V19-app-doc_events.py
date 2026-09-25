# V-19 probe payload: zelin's three Company doc_events, copied VERBATIM from
# Reference/zelin-tech-erpnext_china/erpnext_china/doc_events.py (MIT).
#
# The ONLY change is the two import module prefixes erpnext_china -> erx_v19,
# which is unavoidable because the test app has a different name.  Everything
# else -- including `frappe.flags.country_change = False` in
# `company_before_insert`, the `china_coa` list, the bare `except` around
# `set_company_default`, and the exact order of the flag assignments in
# `company_on_update` -- is byte-identical to the upstream file.

import frappe
from erx_v19.chart_of_accounts.company_default.utils import set_company_default
from erx_v19.chart_of_accounts.custom_accounts.custom_account import erpnext_china_create_charts

china_coa = ["一般企业会计准则(2024)", "小企业会计准则(2024)", "小企业会计准则", "民间非营利组织会计制度(2025)"]

def company_before_insert(doc, method):
    chart_of_accounts = doc.chart_of_accounts
    if chart_of_accounts and chart_of_accounts in china_coa and doc.country == 'China':
        frappe.local.flags.ignore_chart_of_accounts = True
        frappe.flags.country_change = False

def company_after_insert(doc, method):
    doc.erpnext_china_in_insert = True

def company_on_update(doc, method):
    if not frappe.db.exists("Account", {"company": doc.name, "docstatus": ("<", 2)}):
        frappe.flags.country_change = True
        frappe.local.flags.ignore_root_company_validation = True
        frappe.local.flags.ignore_chart_of_accounts = 1
        erpnext_china_create_charts(doc.name, doc.chart_of_accounts, doc.existing_company)
        doc.create_default_warehouses()

    chart_of_accounts = doc.chart_of_accounts
    if (
        doc.get("erpnext_china_in_insert") and chart_of_accounts and chart_of_accounts in china_coa
        and doc.country == 'China'
    ):
        try:
            set_company_default(doc.name)
        except:
            frappe.log_error("erpnext_china.doc_events.company_on_update set company default error")
