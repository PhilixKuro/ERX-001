# V-22 segment 9: the corrected mechanism, and the one combination that works
# through the SHIPPED flow with no source patch at all.
#
# Correction to segment 8's stated mechanism: the blocking warning is NOT a
# row-length mismatch. It is Link validation. Mapping 余额 (balance) to
# bank_account made Column.validate_values() check the BALANCE NUMBERS against
# existing Bank Account names:
#     {'col': 5, 'message': 'The following values do not exist for Bank Account:
#      6806.18, 6506.18', 'type': 'warning'}
# type == 'warning' != 'info', so import_data (:85-92) returns silently.
# => sacrificing a real column to satisfy the :84 gate POISONS the import.
#     Segment 5's F2 verdict is therefore wrong in practice: the gate is passable
#     that way, but the import then silently does nothing.
#
# So the only viable shipped path is: the FILE itself carries a real
# 'Bank Account' column holding the actual bank account name, and the column map
# is supplied index-keyed the way the desk Map Columns dialog supplies it
# (import_preview.js:311-315), which segment 6 proved survives validate().
#
# This segment runs exactly that, start to finish, with NOTHING patched:
# insert -> attach -> save -> index-keyed map via normal save -> start_import().
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg9-shipped-viable.py

import json
import time

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
BANK = "V22测试银行"
BANK_ACCT = "V22测试账户 - V22测试银行"
REF2 = "V22REF20260927001"
OUT = "/workspace/Spike/V22-out/seg9-shipped-viable.json"

result = {"segment": "9 shipped flow, no patch, file carries a real Bank Account column"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

rec("bt_before", frappe.db.count("Bank Transaction"))
rec("errorlog_before", frappe.db.count("Error Log"))

# 9 columns: 8 genuinely Chinese + the one literal 'Bank Account' the :84 gate needs
H = ["交易日期", "摘要", "借方发生额", "贷方发生额", "余额", "对方户名", "交易流水号", "币种",
     "Bank Account"]
ROWS = [
    ["2026-09-27", "货款收入", "", "8888.00", "10694.18", "江南机械", REF2, "CNY", BANK_ACCT],
    ["2026-09-27", "手续费", "5.00", "", "10689.18", "", "V22REF20260927002", "CNY", BANK_ACCT],
]
import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "对账单"
ws.append(H)
for r in ROWS:
    ws.append(r)
XLSX = "/workspace/Spike/V22-sample-statement-shipped.xlsx"
wb.save(XLSX)
rec("wrote_xlsx", XLSX)
rec("headers", H)
rec("chinese_headers", [h for h in H if any(ord(c) > 127 for c in h)])

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
fdoc = save_file("V22-sample-statement-shipped.xlsx", content, "Bank Statement Import",
                 bsi.name, is_private=1, df="import_file")
bsi.import_file = fdoc.file_url
bsi.save()
rec("shipped_map_from_Bank_Transaction_Mapping", bsi.template_options)

# The desk Map Columns dialog: 8 real fields. 余额 (balance) deliberately left
# UNMAPPED -- Bank Transaction has no balance field, and mapping it anywhere that
# Link-validates is what silently killed segment 6.
changed_map = {
    "0": "date",
    "1": "description",
    "2": "withdrawal",
    "3": "deposit",
    "5": "bank_party_name",
    "6": "reference_number",
    "7": "currency",
    "8": "bank_account",
}
opts = json.loads(bsi.template_options or "{}")
opts["column_to_field_map"] = {**opts.get("column_to_field_map", {}), **changed_map}
bsi.template_options = json.dumps(opts)
bsi.save()
bsi.reload()
t_setup = time.time() - t_setup0
rec("mapping_setup_seconds", round(t_setup, 2))
rec("fields_mapped_via_dialog", len(changed_map))
rec("template_options_after_save", bsi.template_options)

prev = bsi.get_preview_from_template(bsi.import_file, None)
rec("preview_mapped",
    [(c.get("header_title"), (c.get("df") or {}).get("fieldname") if c.get("df") else None)
     for c in prev["columns"]])
allw = prev.get("warnings") or []
rec("preview_warnings", allw)
rec("BLOCKING_warnings", [w for w in allw if w.get("type") != "info"])
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
rec("bt_after", frappe.db.count("Bank Transaction"))
rec("new_rows", frappe.get_all(
    "Bank Transaction", filters={"reference_number": ["like", "V22REF2026092700%"]},
    fields=["name", "date", "status", "deposit", "withdrawal", "currency", "description",
            "reference_number", "bank_party_name", "bank_account", "unallocated_amount",
            "docstatus"], order_by="name"))
rec("import_logs", frappe.get_all(
    "Data Import Log", filters={"data_import": bsi.name},
    fields=["success", "docname", "exception"], order_by="log_index"))
rec("errorlog_after", frappe.db.count("Error Log"))
rec("bank_mapping_after", [(d.file_field, d.bank_transaction_field)
                          for d in frappe.get_doc("Bank", BANK).bank_transaction_mapping])

rec("VERDICT_a_shipped",
    "Chinese-header xlsx DOES import through the shipped flow when (i) the file carries a "
    "literal 'Bank Account' column with a real bank account value and (ii) the column map is "
    "index-keyed as the desk Map Columns dialog writes it. The Bank Transaction Mapping child "
    "table plays NO part -- its Chinese file_field entries are never read."
    if frappe.db.count("Bank Transaction") > result["bt_before"] else
    "still fails")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
