# V-22 segment 3: isolate WHY the Chinese columns did not map.
#
# Two suspects read out of the source:
#
#   S1  KEY MISMATCH.
#       bank_statement_import.py:68-70 builds
#           column_to_field_map[i.file_field] = i.bank_transaction_field
#       i.e. keyed by the Chinese HEADER STRING.
#       importer.py:879 reads it back as
#           map_to_field = column_to_field_map.get(str(j))
#       i.e. keyed by the 0-based COLUMN INDEX.
#       If S1 is real, feeding the SAME map keyed by "0".."7" must map correctly.
#
#   S2  GATE ORDER.
#       bank_statement_import.py:84-85 refuses unless the literal string
#       "Bank Account" appears in the preview columns, but the helper that ADDS
#       that column (add_bank_account, :327) runs inside the queued start_import
#       AFTER the gate. So the gate can only pass if the FILE already carries a
#       literal "Bank Account" header.
#
# Writes nothing but a throwaway BSI (deleted by V22-seg5-cleanup.py).
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg3-diagnose.py

import json

import frappe
from frappe.core.doctype.data_import.importer import ImportFile

SITE = "erx.localhost"
XLSX = "/workspace/Spike/V22-sample-statement.xlsx"
OUT = "/workspace/Spike/V22-out/seg3-diagnose.json"

result = {"segment": "3 isolate the mapping failure"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

BANK = "V22测试银行"
bank = frappe.get_doc("Bank", BANK)
by_name = {d.file_field: d.bank_transaction_field for d in bank.bank_transaction_mapping}
rec("map_keyed_by_header", by_name)

HEADERS = ["交易日期", "摘要", "借方发生额", "贷方发生额", "余额", "对方户名", "交易流水号", "币种"]
by_index = {}
for j, h in enumerate(HEADERS):
    if h in by_name:
        by_index[str(j)] = by_name[h]
rec("map_keyed_by_index", by_index)

fdoc_name = frappe.db.get_value("File", {"file_name": ["like", "V22-sample-statement%.xlsx"]})
file_url = frappe.db.get_value("File", fdoc_name, "file_url") if fdoc_name else None
rec("reused_file_url", file_url)
if not file_url:
    from frappe.utils.file_manager import save_file
    with open(XLSX, "rb") as f:
        content = f.read()
    fdoc = save_file("V22-sample-statement.xlsx", content, None, None, is_private=1)
    file_url = fdoc.file_url
    rec("saved_new_file_url", file_url)


def resolve(label, template_options):
    """Run ImportFile with a given column_to_field_map and report per column."""
    try:
        imp = ImportFile("Bank Transaction", file_url,
                         frappe._dict(template_options), "Insert New Records")
        cols = [{"col_no": c.column_number, "header": c.header_title,
                 "map_to_field": c.map_to_field,
                 "df_fieldname": c.df.fieldname if c.df else None,
                 "skip_import": c.skip_import} for c in imp.columns]
        rec(f"{label}_columns", cols)
        rec(f"{label}_mapped_fieldnames", [c["df_fieldname"] for c in cols if c["df_fieldname"]])
        rec(f"{label}_n_mapped", len([c for c in cols if c["df_fieldname"]]))
    except Exception:
        rec(f"{label}_ERROR", frappe.get_traceback())


# S1 test: the two keyings, same data, same file
resolve("A_keyed_by_header_AS_SHIPPED", {"column_to_field_map": by_name})
resolve("B_keyed_by_index_HYPOTHESIS", {"column_to_field_map": by_index})
resolve("C_no_map_at_all", {"column_to_field_map": {}})

# What DOES match with no map: prove the auto-matcher only knows en/zh ERPNext labels
from frappe.core.doctype.data_import.importer import build_fields_dict_for_column_matching

frappe.local.lang = "zh"
frappe.cache.delete_key("data_import_column_header_map")
d = build_fields_dict_for_column_matching("Bank Transaction")
rec("zh_label_for_date", [k for k, v in d.items() if v.fieldname == "date" and any(ord(c) > 127 for c in k)])
rec("zh_label_for_deposit", [k for k, v in d.items() if v.fieldname == "deposit" and any(ord(c) > 127 for c in k)])
rec("chinese_bank_headers_recognised_natively",
    {h: (d.get(h).fieldname if d.get(h) else None) for h in HEADERS})
frappe.cache.delete_key("data_import_column_header_map")
frappe.local.lang = "en"

# S2 test: does the gate string ever appear on its own?
imp = ImportFile("Bank Transaction", file_url, frappe._dict({"column_to_field_map": by_index}),
                 "Insert New Records")
prev = imp.get_data_for_import_preview()
rec("S2_gate_BankAccount_in_preview_columns", "Bank Account" in json.dumps(prev["columns"], default=str))
rec("S2_gate_verdict",
    "gate at bank_statement_import.py:84 needs the literal string 'Bank Account' in the "
    "preview columns; add_bank_account() at :327 only runs later inside start_import, "
    "so the FILE must already carry a 'Bank Account' header column")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
