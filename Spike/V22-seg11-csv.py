# V-22 segment 11: the proposition says xlsx OR csv, so test csv too -- in both
# UTF-8 and GBK, because Chinese online-banking exports are very often GBK/GB18030.
#
# read_content (importer.py:624-635) sends csv to read_csv_content(); the File doc's
# get_content() decodes the bytes. If GBK is not handled, a real bank export fails
# at the very first step.
#
# Also repeats the winning recipe from segment 10 so the csv result is comparable:
# file carries a literal 'Bank Account' column, 余额 left unmapped, map index-keyed.
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg11-csv.py

import csv as _csv
import json
import time

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
ABBR = "HDS"
BANK = "V22测试银行"
BANK_ACCT = "V22测试账户 - V22测试银行"
ACC = f"V22测试银行存款 - {ABBR}"
REF = "V22REF20260929001"
OUT = "/workspace/Spike/V22-out/seg11-csv.json"

result = {"segment": "11 csv path, utf-8 and gbk"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

rec("bt_before", frappe.db.count("Bank Transaction"))

H = ["交易日期", "摘要", "借方发生额", "贷方发生额", "余额", "对方户名", "交易流水号", "币种",
     "Bank Account"]
ROWS = [
    ["2026-09-29", "货款收入", "", "3333.00", "14022.18", "江南机械", REF, "CNY", BANK_ACCT],
    ["2026-09-29", "手续费", "8.00", "", "14014.18", "", "V22REF20260929002", "CNY", BANK_ACCT],
]

CSV_UTF8 = "/workspace/Spike/V22-sample-statement.csv"
with open(CSV_UTF8, "w", encoding="utf-8", newline="") as f:
    w = _csv.writer(f)
    w.writerow(H)
    w.writerows(ROWS)
rec("wrote_csv_utf8", CSV_UTF8)

CSV_GBK = "/workspace/Spike/V22-sample-statement-gbk.csv"
with open(CSV_GBK, "w", encoding="gbk", newline="") as f:
    w = _csv.writer(f)
    w.writerow(H)
    w.writerows(ROWS)
rec("wrote_csv_gbk", CSV_GBK)
with open(CSV_GBK, "rb") as f:
    head = f.read(40)
rec("gbk_first_bytes", head.hex())

# throwaway PE for the csv run
if not frappe.db.exists("Payment Entry", {"reference_no": REF}):
    pe = frappe.get_doc({
        "doctype": "Payment Entry", "payment_type": "Receive", "company": COMPANY,
        "posting_date": "2026-09-29", "party_type": "Customer", "party": "江南机械",
        "paid_from": f"应收账款 1 - {ABBR}", "paid_to": ACC,
        "paid_amount": 3333.00, "received_amount": 3333.00,
        "source_exchange_rate": 1, "target_exchange_rate": 1,
        "reference_no": REF, "reference_date": "2026-09-29", "bank_account": BANK_ACCT,
    })
    pe.insert()
    pe.submit()
    rec("pe_created", pe.name)

from frappe.utils.file_manager import save_file

MAP = {"0": "date", "1": "description", "2": "withdrawal", "3": "deposit",
       "5": "bank_party_name", "6": "reference_number", "7": "currency",
       "8": "bank_account"}


def run(tag, path, fname):
    bsi = frappe.get_doc({
        "doctype": "Bank Statement Import", "company": COMPANY, "bank_account": BANK_ACCT,
        "bank": BANK, "reference_doctype": "Bank Transaction",
        "import_type": "Insert New Records", "submit_after_import": 1, "mute_emails": 1,
    }).insert()
    with open(path, "rb") as f:
        content = f.read()
    fdoc = save_file(fname, content, "Bank Statement Import", bsi.name,
                     is_private=1, df="import_file")
    try:
        bsi.import_file = fdoc.file_url
        bsi.save()
        rec(f"{tag}_save_ok", True)
    except Exception:
        rec(f"{tag}_save_TRACEBACK", frappe.get_traceback())
        return bsi.name

    opts = json.loads(bsi.template_options or "{}")
    opts["column_to_field_map"] = {**opts.get("column_to_field_map", {}), **MAP}
    bsi.template_options = json.dumps(opts)
    bsi.save()
    bsi.reload()

    try:
        prev = bsi.get_preview_from_template(bsi.import_file, None)
        rec(f"{tag}_header_read_back", [c.get("header_title") for c in prev["columns"]])
        rec(f"{tag}_mapped",
            [(c.get("header_title"), (c.get("df") or {}).get("fieldname") if c.get("df") else None)
             for c in prev["columns"]])
        rec(f"{tag}_blocking_warnings",
            [w for w in (prev.get("warnings") or []) if w.get("type") != "info"])
    except Exception:
        rec(f"{tag}_preview_TRACEBACK", frappe.get_traceback())
        return bsi.name

    t0 = time.time()
    try:
        bsi.start_import()
        rec(f"{tag}_import_threw", False)
    except Exception:
        rec(f"{tag}_import_threw", True)
        rec(f"{tag}_import_TRACEBACK", frappe.get_traceback())
    rec(f"{tag}_seconds", round(time.time() - t0, 2))
    frappe.db.commit()
    bsi.reload()
    rec(f"{tag}_status", bsi.status)
    rec(f"{tag}_template_warnings", bsi.template_warnings)
    rec(f"{tag}_logs", frappe.get_all("Data Import Log", filters={"data_import": bsi.name},
                                      fields=["success", "docname", "exception"]))
    return bsi.name


# clean the Bank mapping first: segment 10 proved update_mapping_db pollutes it and
# the pollution is reinstated into template_options on the next save
ORIG = [("交易日期", "date"), ("摘要", "description"), ("贷方发生额", "deposit"),
        ("借方发生额", "withdrawal"), ("对方户名", "bank_party_name"),
        ("交易流水号", "reference_number"), ("币种", "currency")]
bank = frappe.get_doc("Bank", BANK)
bank.bank_transaction_mapping = []
for ff, btf in ORIG:
    bank.append("bank_transaction_mapping", {"file_field": ff, "bank_transaction_field": btf})
bank.save()
frappe.db.commit()

rec("csv_utf8_bsi", run("csv_utf8", CSV_UTF8, "V22-sample-statement.csv"))
rec("bt_after_utf8", frappe.db.count("Bank Transaction"))
rec("utf8_rows", frappe.get_all(
    "Bank Transaction", filters={"reference_number": ["like", "V22REF2026092900%"]},
    fields=["name", "date", "status", "deposit", "withdrawal", "description",
            "reference_number", "bank_party_name", "currency"], order_by="name"))

# scrub again before the gbk run
bank = frappe.get_doc("Bank", BANK)
bank.bank_transaction_mapping = []
for ff, btf in ORIG:
    bank.append("bank_transaction_mapping", {"file_field": ff, "bank_transaction_field": btf})
bank.save()
frappe.db.commit()

rec("csv_gbk_bsi", run("csv_gbk", CSV_GBK, "V22-sample-statement-gbk.csv"))
rec("bt_after_gbk", frappe.db.count("Bank Transaction"))

# ------------------------------------------------------- auto reconcile the csv row
from erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool import (
    auto_reconcile_vouchers,
)

frappe.local.message_log = []
try:
    auto_reconcile_vouchers(bank_account=BANK_ACCT, from_date="2026-09-01", to_date="2026-09-30")
    rec("auto_reconcile_threw", False)
except Exception:
    rec("auto_reconcile_threw", True)
    rec("auto_reconcile_TRACEBACK", frappe.get_traceback())
rec("auto_reconcile_messages", [str(m) for m in (frappe.local.message_log or [])])
frappe.db.commit()

rec("csv_row_status_after_reconcile", frappe.get_all(
    "Bank Transaction", filters={"reference_number": REF},
    fields=["name", "status", "allocated_amount", "unallocated_amount"]))
rec("csv_pe_clearance", frappe.db.get_value(
    "Payment Entry", {"reference_no": REF}, ["name", "clearance_date"], as_dict=True))
rec("status_counts", frappe.db.sql(
    "select status, count(*) from `tabBank Transaction` group by status", as_list=True))
rec("errorlog_now", frappe.db.count("Error Log"))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
