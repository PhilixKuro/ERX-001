# V-22 segment 5: two follow-ups that change the cost estimate.
#
# F1  Did the import CORRUPT Bank.bank_transaction_mapping?
#     start_import (bank_statement_import.py:283) calls update_mapping_db() FIRST,
#     which at :318-324 DELETES every existing mapping row and rewrites the table
#     from template_options:
#         bank.append(..., {"bank_transaction_field": d[1], "file_field": d[0]})
#     So whatever keys template_options carries become file_field. Segment 4 fed it
#     index keys, so the 7 Chinese file_field values should now be "0".."7".
#     If so, one import DESTROYS the Chinese mapping the user configured.
#
# F2  Can the gate at bank_statement_import.py:84 be satisfied WITHOUT editing the
#     file?  The gate tests the literal string Bank Account against the whole
#     preview-columns JSON, which includes each column df.label. So mapping any
#     column to the bank_account field may make the label appear and pass the gate.
#     If that works, the workaround is mapping-only; if not, every statement file
#     must be physically rewritten before import.
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg5-sideeffect.py

import json

import frappe

SITE = "erx.localhost"
BANK = "V22测试银行"
OUT = "/workspace/Spike/V22-out/seg5-sideeffect.json"

result = {"segment": "5 mapping-table corruption + gate workaround"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

# ------------------------------------------------------------------------ F1
bank = frappe.get_doc("Bank", BANK)
rows = [(d.file_field, d.bank_transaction_field) for d in bank.bank_transaction_mapping]
rec("F1_bank_mapping_rows_NOW", rows)
rec("F1_file_field_values_NOW", [r[0] for r in rows])
chinese_left = [r[0] for r in rows if any(ord(c) > 127 for c in str(r[0]))]
rec("F1_chinese_file_fields_still_present", chinese_left)
rec("F1_VERDICT",
    "CORRUPTED: the 7 Chinese file_field values were replaced by numeric strings"
    if not chinese_left else
    "intact: Chinese file_field values survived the import")

# ------------------------------------------------------------------------ F2
# Rebuild the ORIGINAL Chinese mapping first (it is our fixture, and F2 needs it).
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
rec("F2_mapping_restored",
    [(d.file_field, d.bank_transaction_field) for d in frappe.get_doc("Bank", BANK).bank_transaction_mapping])

# Now: the ORIGINAL file (no Bank Account column at all), with an index-keyed map
# that additionally points the 余额 (balance) column at bank_account.
from frappe.core.doctype.data_import.importer import ImportFile

file_url = frappe.db.get_value("File", {"file_name": ["like", "V22-sample-statement9%.xlsx"]}, "file_url")
if not file_url:
    cands = frappe.get_all("File", filters={"file_name": ["like", "V22-sample-statement%"]},
                           fields=["name", "file_name", "file_url"])
    rec("F2_file_candidates", cands)
    file_url = next((c.file_url for c in cands if "gated" not in c.file_name), None)
rec("F2_using_file", file_url)

HEADERS_NO_GATE = ["交易日期", "摘要", "借方发生额", "贷方发生额", "余额", "对方户名", "交易流水号", "币种"]

# map index 4 (余额 / balance) to bank_account, just to make the label appear
by_name = {ff: btf for ff, btf in ORIG}
m = {str(j): by_name[h] for j, h in enumerate(HEADERS_NO_GATE) if h in by_name}
m["4"] = "bank_account"
rec("F2_map_used", m)

try:
    imp = ImportFile("Bank Transaction", file_url, frappe._dict({"column_to_field_map": m}),
                     "Insert New Records")
    prev = imp.get_data_for_import_preview()
    cols = [{"col_no": c.get("column_number"), "header": c.get("header_title"),
             "df_label": (c.get("df") or {}).get("label") if c.get("df") else None,
             "df_fieldname": (c.get("df") or {}).get("fieldname") if c.get("df") else None}
            for c in prev["columns"]]
    rec("F2_preview_columns", cols)
    passes = "Bank Account" in json.dumps(prev["columns"], default=str)
    rec("F2_gate_passes_without_editing_file", passes)
    rec("F2_VERDICT",
        "gate satisfiable by MAPPING alone (df.label 'Bank Account' lands in the preview JSON), "
        "so the statement file itself need not be rewritten -- but a real column must be "
        "sacrificed to carry the bank account, and add_bank_account() at :327-341 then "
        "overwrites that column's values"
        if passes else
        "gate NOT satisfiable by mapping alone: every statement file must be physically "
        "rewritten to carry a literal 'Bank Account' header before import")
except Exception:
    rec("F2_ERROR", frappe.get_traceback())

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
