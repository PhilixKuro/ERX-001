# V-22 segment 7: segment 6 returned a job_id, threw nothing, wrote NO Bank
# Transaction rows and left status = Pending. That is the project's classic silent
# failure, so find the actual exception.
#
# start_import (bank_statement_import.py:283-312) wraps Importer.import_data() in
#     except Exception: frappe.db.rollback(); db_set(status,Error); log_error(...)
# so an exception there should have left status=Error. Pending means it broke
# EARLIER -- before the try -- i.e. in update_mapping_db (:286), ImportFile (:291),
# parse_data_from_template (:293), add_bank_account (:299) or write_files (:300);
# or enqueue(now=True) never actually invoked it.
#
# This segment re-runs those steps by hand, in order, each in its own try, to see
# which one raises and with what.
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg7-why-silent.py

import json

import frappe

SITE = "erx.localhost"
BANK = "V22测试银行"
BANK_ACCT = "V22测试账户 - V22测试银行"
OUT = "/workspace/Spike/V22-out/seg7-why-silent.json"

result = {"segment": "7 find the silent failure in the UI flow"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

rec("errorlog_count", frappe.db.count("Error Log"))
rec("recent_error_logs", frappe.get_all(
    "Error Log", fields=["name", "method", "creation"], order_by="creation desc", limit=5))

# the BSI left behind by segment 6
bsis = frappe.get_all("Bank Statement Import",
                      fields=["name", "status", "import_file", "template_options"],
                      order_by="creation desc")
rec("all_bsi", bsis)
target = next((b for b in bsis if "uiflow" in (b.import_file or "")), None)
rec("uiflow_bsi", target)
if not target:
    rec("ABORT", "no uiflow BSI found")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    raise SystemExit(0)

# is enqueue(now=True) genuinely synchronous here?
import inspect

from frappe.utils.background_jobs import enqueue

src = inspect.getsource(enqueue)
rec("enqueue_now_branch", [ln.strip() for ln in src.splitlines()
                           if "now" in ln or "execute_job" in ln or "frappe.call" in ln])

# Replay the module-level start_import body step by step.
from frappe.core.doctype.data_import.importer import ImportFile, Importer
from erpnext.accounts.doctype.bank_statement_import.bank_statement_import import (
    add_bank_account,
    parse_data_from_template,
    update_mapping_db,
    write_files,
)

name = target["name"]
template_options = target["template_options"]
import_file_path = target["import_file"]

step = "update_mapping_db"
try:
    update_mapping_db(BANK, template_options)
    rec(f"step_{step}", "ok")
    rec("mapping_rows_now", [(d.file_field, d.bank_transaction_field)
                            for d in frappe.get_doc("Bank", BANK).bank_transaction_mapping])
except Exception:
    rec(f"step_{step}_TRACEBACK", frappe.get_traceback())

di = frappe.get_doc("Bank Statement Import", name)

step = "ImportFile"
try:
    imp_file = ImportFile("Bank Transaction", file=import_file_path,
                          import_type="Insert New Records")
    rec(f"step_{step}", "ok")
    rec("raw_data_header", imp_file.raw_data[0] if imp_file.raw_data else None)
    rec("raw_data_rows", len(imp_file.raw_data or []))
    # NOTE: line 291 constructs ImportFile WITHOUT template_options, so the column
    # map is empty here no matter what the BSI holds.
    rec("NOTE_line291_no_template_options",
        "bank_statement_import.py:291 calls ImportFile(... file=file, "
        "import_type=...) with NO template_options argument, so column_to_field_map "
        "is empty in this object")
except Exception:
    rec(f"step_{step}_TRACEBACK", frappe.get_traceback())
    imp_file = None

if imp_file:
    step = "parse_data_from_template"
    try:
        data = parse_data_from_template(imp_file.raw_data)
        rec(f"step_{step}", f"ok, {len(data)} rows incl header")
    except Exception:
        rec(f"step_{step}_TRACEBACK", frappe.get_traceback())
        data = None

    if data:
        step = "add_bank_account"
        try:
            add_bank_account(data, BANK_ACCT)
            rec(f"step_{step}_header_after", data[0])
            rec(f"step_{step}_row1_after", data[1])
        except Exception:
            rec(f"step_{step}_TRACEBACK", frappe.get_traceback())

        step = "write_files"
        try:
            write_files(imp_file, data)
            rec(f"step_{step}", "ok")
        except Exception:
            rec(f"step_{step}_TRACEBACK", frappe.get_traceback())

    step = "Importer.import_data"
    try:
        di.reload()
        if not di.get("payload_count"):
            di.payload_count = len(data) - 1
        i = Importer(di.reference_doctype, data_import=di)
        rec("importer_columns_resolved",
            [(c.header_title, c.df.fieldname if c.df else None, c.skip_import)
             for c in i.import_file.columns])
        i.import_data()
        rec(f"step_{step}", "ok")
    except Exception:
        rec(f"step_{step}_TRACEBACK", frappe.get_traceback())

frappe.db.commit()
rec("bt_count_now", frappe.db.count("Bank Transaction"))
rec("bt_uiflow_rows", frappe.get_all(
    "Bank Transaction", filters={"reference_number": ["like", "V22REF202609250%"]},
    fields=["name", "date", "status", "deposit", "withdrawal", "description",
            "reference_number", "bank_account", "currency"]))
rec("import_logs", frappe.get_all(
    "Data Import Log", filters={"data_import": name},
    fields=["success", "docname", "exception"], order_by="log_index"))
rec("errorlog_count_end", frappe.db.count("Error Log"))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
