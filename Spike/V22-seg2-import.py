# V-22 segment 2: drive the NATIVE Bank Statement Import path with the
# Chinese-header xlsx, and dump exactly how each Chinese column resolved.
#
# This emulates the UI flow:
#   1. insert BSI with no import_file  -> validate() builds template_options
#                                          from Bank.bank_transaction_mapping
#   2. set import_file and save        -> validate() rebuilds template_options
#   3. start_import()                  -> developer_mode=1 makes run_now True,
#                                          so enqueue(now=True) runs IN-PROCESS
#                                          (this container has NO queue worker)
#
# The diagnostic that matters is per-column: header_title -> df.fieldname /
# skip_import, i.e. whether the Chinese header actually reached a field.
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg2-import.py

import json
import time

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
BANK = "V22测试银行"
BANK_ACCT = "V22测试账户 - V22测试银行"
XLSX = "/workspace/Spike/V22-sample-statement.xlsx"
OUT = "/workspace/Spike/V22-out/seg2-import.json"

result = {"segment": "2 native Bank Statement Import with chinese headers"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

rec("errorlog_before", frappe.db.count("Error Log"))
rec("bt_before", frappe.db.count("Bank Transaction"))

# ------------------------------------------------------------ 1. attach the file
from frappe.utils.file_manager import save_file

with open(XLSX, "rb") as f:
    content = f.read()
rec("xlsx_bytes", len(content))

# ------------------------------------- 2. insert BSI WITHOUT import_file (step 1)
bsi = frappe.get_doc({
    "doctype": "Bank Statement Import",
    "company": COMPANY,
    "bank_account": BANK_ACCT,
    "bank": BANK,
    "reference_doctype": "Bank Transaction",
    "import_type": "Insert New Records",
    "submit_after_import": 1,
    "mute_emails": 1,
})
try:
    bsi.insert()
    rec("bsi_created", bsi.name)
except Exception:
    rec("bsi_insert_ERROR", frappe.get_traceback())
    raise

# THE key observation: what did validate() put in template_options, and with
# WHAT KEYS?  bank_statement_import.py:68-70 keys it by file_field (the Chinese
# header string).  importer.py:879 looks it up with column_to_field_map.get(str(j))
# where j is the 0-based COLUMN INDEX.  If those disagree the mapping is dead.
rec("template_options_after_insert", bsi.template_options)
rec("template_options_keys", list(json.loads(bsi.template_options or "{}")
                                  .get("column_to_field_map", {}).keys()))

# ------------------------------------------- 3. attach file and save it (step 2)
fdoc = save_file("V22-sample-statement.xlsx", content, "Bank Statement Import",
                 bsi.name, is_private=1, df="import_file")
rec("file_url", fdoc.file_url)

bsi.import_file = fdoc.file_url
try:
    bsi.save()
    rec("bsi_saved_with_file", True)
except Exception:
    rec("bsi_save_ERROR", frappe.get_traceback())
    raise

rec("template_options_after_file", bsi.template_options)
rec("payload_count", bsi.get("payload_count"))

# ------------------------------- 4. the preview: per-column resolution (POSITIVE evidence)
try:
    preview = bsi.get_preview_from_template(bsi.import_file, None)
    cols = []
    for c in preview["columns"]:
        cols.append({
            "col_no": c.get("column_number"),
            "header_title": c.get("header_title"),
            "map_to_field": c.get("map_to_field"),
            "df_fieldname": (c.get("df") or {}).get("fieldname") if c.get("df") else None,
            "df_label": (c.get("df") or {}).get("label") if c.get("df") else None,
            "skip_import": c.get("skip_import"),
        })
    rec("preview_columns", cols)
    rec("preview_columns_mapped", [c for c in cols if c["df_fieldname"]])
    rec("preview_columns_skipped", [c["header_title"] for c in cols if c["skip_import"]])
    rec("preview_row_count", len(preview.get("data") or []))
    rec("preview_warnings", preview.get("warnings"))
    rec("gate_BankAccount_in_columns", "Bank Account" in json.dumps(preview["columns"], default=str))
except Exception:
    rec("preview_ERROR", frappe.get_traceback())

# --------------------------------------------------------- 5. start_import (step 3)
rec("scheduler_inactive", None)
try:
    from frappe.utils.scheduler import is_scheduler_inactive
    rec("scheduler_inactive", is_scheduler_inactive())
except Exception:
    rec("scheduler_check_ERROR", frappe.get_traceback())
rec("developer_mode", frappe.conf.developer_mode)

t0 = time.time()
try:
    job_id = bsi.start_import()
    rec("start_import_returned", job_id)
    rec("start_import_threw", False)
except Exception:
    rec("start_import_threw", True)
    rec("start_import_TRACEBACK", frappe.get_traceback())
rec("start_import_seconds", round(time.time() - t0, 2))

frappe.db.commit()

# ------------------------------------------------------------------ 6. the result
bsi.reload()
rec("bsi_status", bsi.status)
rec("bt_after", frappe.db.count("Bank Transaction"))
rec("bank_transactions", frappe.get_all(
    "Bank Transaction",
    fields=["name", "date", "status", "deposit", "withdrawal", "currency", "description",
            "reference_number", "bank_party_name", "bank_account", "unallocated_amount", "docstatus"],
    order_by="creation"))
rec("data_import_logs", frappe.get_all(
    "Data Import Log", filters={"data_import": bsi.name},
    fields=["success", "docname", "messages", "exception", "row_indexes"], order_by="log_index"))
rec("errorlog_after", frappe.db.count("Error Log"))
rec("new_error_logs", frappe.get_all(
    "Error Log", fields=["name", "method", "error"], order_by="creation desc", limit=3))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
