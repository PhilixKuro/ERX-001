# V-22 segment 4: end-to-end. Import the Chinese-header statement for real, then
# run auto_reconcile_vouchers() and read back status + clearance_date.
#
# Segment 3 proved the shipped path cannot map Chinese headers (two defects, quoted
# there). This segment applies the SMALLEST possible patch to DATA ONLY -- no
# erpnext/frappe source file is edited -- so that half (b) can still be tested:
#
#   P1  write template_options keyed by column index (what importer.py:879 reads)
#       instead of by header name (what bank_statement_import.py:69 writes).
#   P2  append a literal Bank Account header column to the file, so the gate at
#       bank_statement_import.py:84 can pass.
#
# Then the real native machinery runs: ImportFile -> Importer.import_data() ->
# Bank Transaction rows, and erpnext's own auto_reconcile_vouchers().
#
# Route note: this container has NO queue worker (only bench serve), and
# is_scheduler_inactive() is True. developer_mode=1 makes run_now True inside
# start_import, so enqueue(..., now=True) executes IN-PROCESS. Recorded below.
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg4-e2e.py

import json
import time

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
BANK = "V22测试银行"
BANK_ACCT = "V22测试账户 - V22测试银行"
MATCH_REF = "V22REF20260922001"
OUT = "/workspace/Spike/V22-out/seg4-e2e.json"

result = {"segment": "4 end-to-end import + auto reconcile"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

rec("errorlog_before", frappe.db.count("Error Log"))
rec("bt_before", frappe.db.count("Bank Transaction"))
rec("pe_before", frappe.db.count("Payment Entry"))

# The same genuinely-Chinese headers, plus the literal gate column (P2).
#   交易日期 transaction date / 摘要 abstract / 借方发生额 debit amount
#   贷方发生额 credit amount / 余额 balance / 对方户名 counterparty name
#   交易流水号 transaction serial no / 币种 currency
H_DATE = "交易日期"
H_DESC = "摘要"
H_DEBIT = "借方发生额"
H_CREDIT = "贷方发生额"
H_BALANCE = "余额"
H_PARTY = "对方户名"
H_SERIAL = "交易流水号"
H_CCY = "币种"

HEADERS = [H_DATE, H_DESC, H_DEBIT, H_CREDIT, H_BALANCE, H_PARTY, H_SERIAL, H_CCY, "Bank Account"]

CUST = "江南机械"          # 江南机械, the demo customer
SUPP = "宝钢弹簧钢丝"  # 宝钢弹簧钢丝, the demo supplier
D_SALES = "货款收入"        # 货款收入
D_WIRE = "电汇付款"         # 电汇付款
D_FEE = "手续费"                # 手续费
D_INT = "利息收入"          # 利息收入
D_TRAVEL = "差旅报销"       # 差旅报销

ROWS = [
    ["2026-09-22", D_SALES, "", "1045.00", "1045.00", CUST, MATCH_REF, "CNY", BANK_ACCT],
    ["2026-09-22", D_WIRE, "750.00", "", "295.00", SUPP, "V22REF20260922002", "CNY", BANK_ACCT],
    ["2026-09-23", D_FEE, "12.50", "", "282.50", "", "V22REF20260923001", "CNY", BANK_ACCT],
    ["2026-09-23", D_INT, "", "3.68", "286.18", "", "V22REF20260923002", "CNY", BANK_ACCT],
    ["2026-09-24", D_SALES, "", "2000.00", "2286.18", CUST, "V22REF20260924001", "CNY", BANK_ACCT],
    ["2026-09-24", D_TRAVEL, "480.00", "", "1806.18", "", "V22REF20260924002", "CNY", BANK_ACCT],
]
rec("headers_used", HEADERS)
rec("chinese_header_count", len([h for h in HEADERS if any(ord(c) > 127 for c in h)]))
rec("row_count", len(ROWS))

import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "对账单"
ws.append(HEADERS)
for r in ROWS:
    ws.append(r)
XLSX = "/workspace/Spike/V22-sample-statement-gated.xlsx"
wb.save(XLSX)
rec("wrote_xlsx", XLSX)

# ---------------------------------------------------------------- build the BSI
from frappe.utils.file_manager import save_file

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
rec("bsi_created", bsi.name)

with open(XLSX, "rb") as f:
    content = f.read()
fdoc = save_file("V22-sample-statement-gated.xlsx", content, "Bank Statement Import",
                 bsi.name, is_private=1, df="import_file")
bsi.import_file = fdoc.file_url
bsi.save()
rec("shipped_template_options", bsi.template_options)

# P1: re-key the map by column index, which is what importer.py:879 actually reads
bank = frappe.get_doc("Bank", BANK)
by_name = {d.file_field: d.bank_transaction_field for d in bank.bank_transaction_mapping}
by_index = {str(j): by_name[h] for j, h in enumerate(HEADERS) if h in by_name}
bsi.db_set("template_options", json.dumps({"column_to_field_map": by_index}),
           update_modified=False)
bsi.reload()
rec("patched_template_options", bsi.template_options)
rec("fields_mapped_count", len(by_index))

# ------------------------------------------ preview: positive per-column evidence
preview = bsi.get_preview_from_template(bsi.import_file, None)
cols = [{"col_no": c.get("column_number"), "header": c.get("header_title"),
         "df_fieldname": (c.get("df") or {}).get("fieldname") if c.get("df") else None,
         "skip_import": c.get("skip_import")} for c in preview["columns"]]
rec("preview_columns", cols)
rec("preview_mapped", [(c["header"], c["df_fieldname"]) for c in cols if c["df_fieldname"]])
rec("gate_BankAccount_present", "Bank Account" in json.dumps(preview["columns"], default=str))

# ------------------------------------------------------------ run native import
from frappe.utils.scheduler import is_scheduler_inactive

rec("scheduler_inactive", is_scheduler_inactive())
rec("developer_mode", frappe.conf.developer_mode)
rec("route", "start_import() -> enqueue(now=True) because developer_mode=1; runs "
             "IN-PROCESS, no queue worker exists in this container")

t0 = time.time()
try:
    job = bsi.start_import()
    rec("start_import_returned", job)
    rec("start_import_threw", False)
except Exception:
    rec("start_import_threw", True)
    rec("start_import_TRACEBACK", frappe.get_traceback())
rec("import_seconds", round(time.time() - t0, 2))
frappe.db.commit()

bsi.reload()
rec("bsi_status", bsi.status)
rec("bt_after_import", frappe.db.count("Bank Transaction"))
rec("bank_transactions_after_import", frappe.get_all(
    "Bank Transaction",
    fields=["name", "date", "status", "deposit", "withdrawal", "currency", "description",
            "reference_number", "bank_party_name", "unallocated_amount", "docstatus"],
    order_by="date, name"))
rec("data_import_logs", frappe.get_all(
    "Data Import Log", filters={"data_import": bsi.name},
    fields=["success", "docname", "exception", "row_indexes"], order_by="log_index"))

# -------------------------------------------------------- half (b): auto reconcile
from erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool import (
    auto_reconcile_vouchers,
    get_bank_transactions,
)

rec("candidates_for_reconcile", [
    {"name": t.name, "date": str(t.date), "deposit": t.deposit, "withdrawal": t.withdrawal,
     "ref": t.reference_number, "unallocated": t.unallocated_amount}
    for t in get_bank_transactions(BANK_ACCT)])

rec("target_pe_before", frappe.db.get_value(
    "Payment Entry", {"reference_no": MATCH_REF},
    ["name", "payment_type", "paid_to", "received_amount_after_tax", "posting_date",
     "reference_no", "clearance_date", "docstatus"], as_dict=True))

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

# ---------------------------------------------- POSITIVE evidence of reconciliation
rec("bank_transactions_after_reconcile", frappe.get_all(
    "Bank Transaction",
    fields=["name", "date", "status", "deposit", "withdrawal", "reference_number",
            "allocated_amount", "unallocated_amount", "party_type", "party"],
    order_by="date, name"))
rec("status_counts_after_reconcile", frappe.db.sql(
    "select status, count(*) from `tabBank Transaction` group by status", as_list=True))
rec("bank_transaction_payments_rows", frappe.get_all(
    "Bank Transaction Payments",
    fields=["parent", "payment_document", "payment_entry", "allocated_amount"]))
rec("ALL_payment_entries_clearance", frappe.get_all(
    "Payment Entry",
    fields=["name", "payment_type", "reference_no", "paid_amount", "clearance_date", "docstatus"],
    order_by="name"))
rec("errorlog_after", frappe.db.count("Error Log"))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
