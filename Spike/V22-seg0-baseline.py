# V-22 segment 0: baseline snapshot BEFORE anything is written.
#
# Proposition V-22: can a Chinese-header xlsx/csv bank statement be imported into
# Bank Transaction via Bank Statement Import + Bank Transaction Mapping, and can
# auto_reconcile_vouchers() then reconcile at least one of them against a voucher?
#
# This segment writes NOTHING. Everything later segments diff against comes from here.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg0-baseline.py

import json

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
OUT = "/workspace/Spike/V22-out/seg0-baseline.json"

result = {"segment": "0 baseline, writes nothing"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()

rec("installed_apps", frappe.get_installed_apps())
rec("developer_mode", frappe.conf.developer_mode)
rec("in_test", bool(getattr(frappe, "in_test", False)))

# the 5 counts the caller asked to be tracked, plus supporting ones
for dt in ("Bank Transaction", "Payment Entry", "Bank Account", "Bank", "Error Log",
           "Bank Statement Import", "Data Import Log", "Bank Transaction Payments",
           "Journal Entry", "Sales Invoice", "File",
           "Bank Transaction Rule", "Bank Transaction Mapping"):
    rec(f"count_{dt}", frappe.db.count(dt))

rec("banks", frappe.get_all("Bank", fields=["name", "bank_name"]))
rec("bank_accounts", frappe.get_all(
    "Bank Account", fields=["name", "account_name", "bank", "account", "company", "is_company_account"]))
rec("bank_transactions", frappe.get_all(
    "Bank Transaction", fields=["name", "date", "status", "bank_account", "deposit", "withdrawal"]))

# every Payment Entry that already exists, with its clearance_date -- so residue or
# accidental mutation of the demo's vouchers is visible afterwards
rec("payment_entries", frappe.get_all(
    "Payment Entry",
    fields=["name", "payment_type", "party_type", "party", "paid_amount", "received_amount",
            "reference_no", "reference_date", "posting_date", "clearance_date", "docstatus",
            "paid_from", "paid_to", "company", "bank_account"],
    order_by="name"))

# accounts of type Bank in the demo company -- a Bank Account must point at one
rec("bank_type_accounts", frappe.get_all(
    "Account",
    filters={"company": COMPANY, "account_type": "Bank"},
    fields=["name", "account_name", "is_group", "root_type", "account_currency"]))

rec("company_row", frappe.db.get_value(
    "Company", COMPANY,
    ["abbr", "country", "default_currency", "default_bank_account", "default_receivable_account",
     "default_payable_account", "cost_center", "default_cash_account"], as_dict=True))

rec("customers", frappe.get_all("Customer", fields=["name", "customer_name"], limit=10))
rec("suppliers", frappe.get_all("Supplier", fields=["name", "supplier_name"], limit=10))

rec("error_logs_last10", frappe.get_all(
    "Error Log", fields=["name", "method", "creation"], order_by="creation desc", limit=10))

# the Select options for the mapping child field -- if this is a closed list that
# does not contain the fields a Chinese statement needs, (a) is dead on arrival
mapping_meta = frappe.get_meta("Bank Transaction Mapping")
rec("mapping_field_options_raw", mapping_meta.get_field("bank_transaction_field").options)
bt_meta = frappe.get_meta("Bank Transaction")
rec("bank_transaction_fieldnames", [df.fieldname for df in bt_meta.fields])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
