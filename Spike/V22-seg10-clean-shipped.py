# V-22 segment 10: the clean shipped-flow run, plus proof that the mapping-table
# corruption is STICKY.
#
# Segment 9 failed for a reason worth recording: the stale '4': 'bank_account' that
# poisoned it came from the Bank doc itself. update_mapping_db
# (bank_statement_import.py:315-324) had written the previous run's INDEX keys into
# Bank.bank_transaction_mapping as file_field values; validate() (:68-70) then
# rebuilt template_options from that polluted table, silently reinstating '4'.
# So one bad import permanently contaminates the Bank and every later import.
#
# This segment: scrub the Bank mapping back to pure Chinese, then run the shipped
# flow properly (file carries a literal 'Bank Account' column; 余额 left unmapped),
# then run auto_reconcile_vouchers() against a fresh throwaway Payment Entry so
# both halves are demonstrated on the clean path.
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg10-clean-shipped.py

import json
import time

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
ABBR = "HDS"
BANK = "V22测试银行"
BANK_ACCT = "V22测试账户 - V22测试银行"
ACC = f"V22测试银行存款 - {ABBR}"
REF = "V22REF20260928001"
OUT = "/workspace/Spike/V22-out/seg10-clean-shipped.json"

result = {"segment": "10 clean shipped flow + sticky corruption proof"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

rec("bt_before", frappe.db.count("Bank Transaction"))
rec("pe_before", frappe.db.count("Payment Entry"))
rec("errorlog_before", frappe.db.count("Error Log"))

# --------------------------------------- 0. proof + scrub of the sticky corruption
bank = frappe.get_doc("Bank", BANK)
polluted = [(d.file_field, d.bank_transaction_field) for d in bank.bank_transaction_mapping]
rec("mapping_BEFORE_scrub", polluted)
rec("numeric_file_fields_present", [p[0] for p in polluted if str(p[0]).isdigit()])

ORIG = [
    ("交易日期", "date"),
    ("摘要", "description"),
    ("贷方发生额", "deposit"),
    ("借方发生额", "withdrawal"),
    ("对方户名", "bank_party_name"),
    ("交易流水号", "reference_number"),
    ("币种", "currency"),
]
bank.bank_transaction_mapping = []
for ff, btf in ORIG:
    bank.append("bank_transaction_mapping", {"file_field": ff, "bank_transaction_field": btf})
bank.save()
frappe.db.commit()
rec("mapping_AFTER_scrub", [(d.file_field, d.bank_transaction_field)
                           for d in frappe.get_doc("Bank", BANK).bank_transaction_mapping])

# ------------------------------------------- 1. throwaway PE for this run to match
if not frappe.db.exists("Payment Entry", {"reference_no": REF}):
    pe = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": "Receive",
        "company": COMPANY,
        "posting_date": "2026-09-28",
        "party_type": "Customer",
        "party": "江南机械",
        "paid_from": f"应收账款 1 - {ABBR}",
        "paid_to": ACC,
        "paid_amount": 8888.00,
        "received_amount": 8888.00,
        "source_exchange_rate": 1,
        "target_exchange_rate": 1,
        "reference_no": REF,
        "reference_date": "2026-09-28",
        "bank_account": BANK_ACCT,
    })
    pe.insert()
    pe.submit()
    rec("pe_created", pe.name)
rec("pe_row", frappe.db.get_value(
    "Payment Entry", {"reference_no": REF},
    ["name", "payment_type", "received_amount_after_tax", "paid_to", "posting_date",
     "reference_no", "clearance_date", "docstatus"], as_dict=True))

# --------------------------------------------------------------- 2. statement file
H = ["交易日期", "摘要", "借方发生额", "贷方发生额", "余额", "对方户名", "交易流水号", "币种",
     "Bank Account"]
ROWS = [
    ["2026-09-28", "货款收入", "", "8888.00", "10694.18", "江南机械", REF, "CNY", BANK_ACCT],
    ["2026-09-28", "手续费", "5.00", "", "10689.18", "", "V22REF20260928002", "CNY", BANK_ACCT],
]
import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "对账单"
ws.append(H)
for r in ROWS:
    ws.append(r)
XLSX = "/workspace/Spike/V22-sample-statement-clean.xlsx"
wb.save(XLSX)
rec("wrote_xlsx", XLSX)
rec("headers", H)

# ------------------------------------------------ 3. shipped flow, nothing patched
from frappe.utils.file_manager import save_file

t_setup0 = time.time()
bsi = frappe.get_doc({
    "doctype": "Bank Statement Import",
    "company": COMPANY,
    "bank_account": BANK_ACCT,
    "bank": BANK,
    "reference_doctype": "Bank Transaction",
    "import_type": "Insert New Records",
    "submit_after_import": 1,
    "mute_emails": 1,
}).insert()
with open(XLSX, "rb") as f:
    content = f.read()
fdoc = save_file("V22-sample-statement-clean.xlsx", content, "Bank Statement Import",
                 bsi.name, is_private=1, df="import_file")
bsi.import_file = fdoc.file_url
bsi.save()
rec("template_options_from_Bank_mapping", bsi.template_options)

# The desk Map Columns dialog, 8 fields. 余额 (index 4) deliberately NOT mapped:
# Bank Transaction has no balance field, and pointing it at a Link field is what
# produced the blocking 'values do not exist' warning in segments 6 and 9.
changed_map = {"0": "date", "1": "description", "2": "withdrawal", "3": "deposit",
               "5": "bank_party_name", "6": "reference_number", "7": "currency",
               "8": "bank_account"}
opts = json.loads(bsi.template_options or "{}")
merged = {**opts.get("column_to_field_map", {}), **changed_map}
opts["column_to_field_map"] = merged
bsi.template_options = json.dumps(opts)
bsi.save()
bsi.reload()
rec("mapping_setup_seconds", round(time.time() - t_setup0, 2))
rec("fields_mapped_count", len(changed_map))
rec("template_options_final", bsi.template_options)

prev = bsi.get_preview_from_template(bsi.import_file, None)
rec("preview_mapped",
    [(c.get("header_title"), (c.get("df") or {}).get("fieldname") if c.get("df") else None)
     for c in prev["columns"]])
blocking = [w for w in (prev.get("warnings") or []) if w.get("type") != "info"]
rec("BLOCKING_warnings", blocking)
rec("gate_present", "Bank Account" in json.dumps(prev["columns"], default=str))

t0 = time.time()
try:
    job = bsi.start_import()
    rec("start_import_returned", job)
    rec("threw", False)
except Exception:
    rec("threw", True)
    rec("TRACEBACK", frappe.get_traceback())
rec("import_seconds", round(time.time() - t0, 2))
frappe.db.commit()

bsi.reload()
rec("bsi_status", bsi.status)
rec("bsi_template_warnings", bsi.template_warnings)
rec("bt_after_import", frappe.db.count("Bank Transaction"))
rec("new_rows", frappe.get_all(
    "Bank Transaction", filters={"reference_number": ["like", "V22REF2026092800%"]},
    fields=["name", "date", "status", "deposit", "withdrawal", "currency", "description",
            "reference_number", "bank_party_name", "bank_account", "unallocated_amount",
            "docstatus"], order_by="name"))
rec("import_logs", frappe.get_all(
    "Data Import Log", filters={"data_import": bsi.name},
    fields=["success", "docname", "exception"], order_by="log_index"))

# ------------------------------------------------ 4. half (b) on the clean path
from erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool import (
    auto_reconcile_vouchers,
)

frappe.local.message_log = []
t0 = time.time()
try:
    auto_reconcile_vouchers(bank_account=BANK_ACCT, from_date="2026-09-01", to_date="2026-09-30")
    rec("auto_reconcile_threw", False)
except Exception:
    rec("auto_reconcile_threw", True)
    rec("auto_reconcile_TRACEBACK", frappe.get_traceback())
rec("auto_reconcile_seconds", round(time.time() - t0, 2))
rec("auto_reconcile_messages", [str(m) for m in (frappe.local.message_log or [])])
frappe.db.commit()

rec("all_bank_transactions_final", frappe.get_all(
    "Bank Transaction",
    fields=["name", "date", "status", "deposit", "withdrawal", "reference_number",
            "allocated_amount", "unallocated_amount"], order_by="date, name"))
rec("status_counts_final", frappe.db.sql(
    "select status, count(*) from `tabBank Transaction` group by status", as_list=True))
rec("bt_payments_rows", frappe.get_all(
    "Bank Transaction Payments",
    fields=["parent", "payment_document", "payment_entry", "allocated_amount"]))
rec("ALL_pe_clearance", frappe.get_all(
    "Payment Entry",
    fields=["name", "payment_type", "reference_no", "paid_amount", "clearance_date", "docstatus"],
    order_by="name"))
rec("errorlog_after", frappe.db.count("Error Log"))
rec("mapping_after_this_import", [(d.file_field, d.bank_transaction_field)
                                 for d in frappe.get_doc("Bank", BANK).bank_transaction_mapping])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
