# V-22 segment 6: does the REAL UI flow work, without patching anything?
#
# Segment 3 showed Bank Transaction Mapping (Chinese file_field) never reaches the
# importer. But the desk UI has a SECOND path to the same map: the Map Columns
# dialog. import_preview.js:311-315 builds
#       changed_map[header_row_index] = values[i]     # keyed by column INDEX
# and bank_statement_import.js:373-377 merges that into template_options and saves.
#
# Index keys are exactly what importer.py:879 reads. And on that save,
# BankStatementImport.validate() (bank_statement_import.py:58-77) only REBUILDS
# template_options when import_file CHANGED -- it did not -- so the index keys
# should SURVIVE. If they do, half (a) is reachable from the shipped UI with no
# code change, and the Bank Transaction Mapping child table is simply dead weight.
#
# This segment replays that exact sequence through the doc API: insert -> attach
# file -> save -> emulate remap_column() -> save -> start_import().
# Nothing but a throwaway BSI is created.
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg6-ui-flow.py

import json
import time

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
BANK = "V22测试银行"
BANK_ACCT = "V22测试账户 - V22测试银行"
OUT = "/workspace/Spike/V22-out/seg6-ui-flow.json"

result = {"segment": "6 replay the shipped UI Map Columns flow, no patching"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

rec("bt_before", frappe.db.count("Bank Transaction"))

# A fresh file with genuinely Chinese headers and NO literal Bank Account column,
# so this run also proves whether the gate needs a physical file edit.
H = ["交易日期", "摘要", "借方发生额", "贷方发生额", "余额", "对方户名", "交易流水号", "币种"]
ROWS = [
    ["2026-09-25", "货款收入", "", "5000.00", "6806.18", "江南机械", "V22REF20260925001", "CNY"],
    ["2026-09-25", "电汇付款", "300.00", "", "6506.18", "宝钢弹簧钢丝", "V22REF20260925002", "CNY"],
]
import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "对账单"
ws.append(H)
for r in ROWS:
    ws.append(r)
XLSX = "/workspace/Spike/V22-sample-statement-uiflow.xlsx"
wb.save(XLSX)
rec("wrote_xlsx", XLSX)
rec("headers", H)

from frappe.utils.file_manager import save_file

# step 1: insert with bank set, no file -> validate() writes the header-keyed map
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
rec("step1_template_options", bsi.template_options)

# step 2: attach the file and save -> validate() rebuilds, still header-keyed
with open(XLSX, "rb") as f:
    content = f.read()
fdoc = save_file("V22-sample-statement-uiflow.xlsx", content, "Bank Statement Import",
                 bsi.name, is_private=1, df="import_file")
bsi.import_file = fdoc.file_url
bsi.save()
rec("step2_template_options", bsi.template_options)

prev = bsi.get_preview_from_template(bsi.import_file, None)
rec("step2_columns_mapped",
    [(c.get("header_title"), ((c.get("df") or {}) or {}).get("fieldname") if c.get("df") else None)
     for c in prev["columns"]])

# step 3: emulate the Map Columns dialog -- index-keyed, merged, then frm.save()
changed_map = {
    "0": "date",
    "1": "description",
    "2": "withdrawal",
    "3": "deposit",
    "4": "bank_account",     # 余额 sacrificed to satisfy the :84 gate
    "5": "bank_party_name",
    "6": "reference_number",
    "7": "currency",
}
opts = json.loads(bsi.template_options or "{}")
opts["column_to_field_map"] = {**opts.get("column_to_field_map", {}), **changed_map}
bsi.template_options = json.dumps(opts)
bsi.save()          # THE test: does validate() wipe the index keys again?
bsi.reload()
rec("step3_template_options_AFTER_SAVE", bsi.template_options)
survived = set(changed_map) <= set(json.loads(bsi.template_options or "{}")
                                   .get("column_to_field_map", {}))
rec("step3_index_keys_SURVIVED_validate", survived)
rec("step3_fields_mapped_count", len(changed_map))

prev2 = bsi.get_preview_from_template(bsi.import_file, None)
rec("step3_columns_mapped",
    [(c.get("header_title"), (c.get("df") or {}).get("fieldname") if c.get("df") else None)
     for c in prev2["columns"]])
rec("step3_gate_BankAccount_present", "Bank Account" in json.dumps(prev2["columns"], default=str))

# step 4: the shipped import, unpatched
t0 = time.time()
try:
    job = bsi.start_import()
    rec("step4_start_import_returned", job)
    rec("step4_threw", False)
except Exception:
    rec("step4_threw", True)
    rec("step4_TRACEBACK", frappe.get_traceback())
rec("step4_seconds", round(time.time() - t0, 2))
frappe.db.commit()

bsi.reload()
rec("step4_bsi_status", bsi.status)
rec("bt_after", frappe.db.count("Bank Transaction"))
rec("new_bank_transactions", frappe.get_all(
    "Bank Transaction",
    filters={"reference_number": ["like", "V22REF202609250%"]},
    fields=["name", "date", "status", "deposit", "withdrawal", "currency", "description",
            "reference_number", "bank_party_name", "bank_account", "unallocated_amount"],
    order_by="name"))
rec("step4_import_logs", frappe.get_all(
    "Data Import Log", filters={"data_import": bsi.name},
    fields=["success", "docname", "exception"], order_by="log_index"))

# what did the sacrificed 余额 column become, and what is left of the Bank mapping?
rec("bank_mapping_after_this_import",
    [(d.file_field, d.bank_transaction_field)
     for d in frappe.get_doc("Bank", BANK).bank_transaction_mapping])
rec("VERDICT",
    "shipped UI flow WORKS end to end with Chinese headers and no code change"
    if survived and frappe.db.count("Bank Transaction") > result["bt_before"] else
    "shipped UI flow still fails")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
