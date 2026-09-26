# V-22 segment 12: (1) what did the GBK csv actually STORE, and (2) full inventory
# of everything this probe created, ready for cleanup.
#
# The GBK run is the sharpest finding of the probe: Bank Statement Import reported
# status = Success, wrote 2 Data Import Log rows with success=1, and created 2
# Bank Transaction docs -- while every Chinese field was mojibake, and the blocking
# Link warning on the Bank Account column ('Bank Account字段不存在以下值:
# V22˛âĘÔŐË»§ - V22˛âĘÔŇřĐĐ') did NOT stop it. So a GBK export silently produces
# garbage rows attached to NO bank account. Confirm precisely what is in the db.
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg12-gbk-inventory.py

import json

import frappe

SITE = "erx.localhost"
BANK = "V22测试银行"
BANK_ACCT = "V22测试账户 - V22测试银行"
OUT = "/workspace/Spike/V22-out/seg12-gbk-inventory.json"

result = {"segment": "12 gbk storage check + cleanup inventory"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

# ------------------------------------------------------------- 1. the GBK rows
gbk = frappe.get_all(
    "Bank Transaction", filters={"name": ["in", ["ACC-BTN-2026-00011", "ACC-BTN-2026-00012"]]},
    fields=["name", "date", "status", "deposit", "withdrawal", "currency", "description",
            "reference_number", "bank_party_name", "bank_account", "company",
            "unallocated_amount", "docstatus"])
rec("gbk_rows_as_stored", gbk)
rec("gbk_bank_account_is_null", [(r["name"], r["bank_account"]) for r in gbk])
rec("gbk_description_mojibake", [(r["name"], r["description"]) for r in gbk])
rec("GBK_VERDICT",
    "Bank Statement Import reported Success and created rows from the GBK file, but the "
    "Chinese text is mojibake AND bank_account came out empty, so the rows are invisible "
    "to get_bank_transactions(bank_account=...) and can never be reconciled. A blocking "
    "Link warning WAS raised at preview time yet the import proceeded anyway.")

# why did it not block? the preview is a separate ImportFile instance from the one
# start_import builds at :291, which gets NO template_options
rec("NOTE_why_not_blocked",
    "start_import (bank_statement_import.py:291) builds its own ImportFile WITHOUT "
    "template_options, then write_files (:300) rewrites the file, and Importer (:303) "
    "re-reads template_options from the doc. The warning seen in the preview is computed "
    "on a DIFFERENT object than the one import_data() checks, so a preview-blocking "
    "warning does not necessarily block the import.")

# ------------------------------------------------------------ 2. full inventory
rec("ALL_bank_transactions", frappe.get_all(
    "Bank Transaction", fields=["name", "date", "status", "bank_account", "reference_number",
                                "allocated_amount", "docstatus"], order_by="name"))
rec("ALL_bank_transaction_payments", frappe.get_all(
    "Bank Transaction Payments",
    fields=["name", "parent", "payment_document", "payment_entry", "allocated_amount"]))
rec("ALL_payment_entries", frappe.get_all(
    "Payment Entry", fields=["name", "reference_no", "paid_amount", "clearance_date",
                             "paid_to", "docstatus"], order_by="name"))
rec("V22_payment_entries", frappe.get_all(
    "Payment Entry", filters={"reference_no": ["like", "V22REF%"]},
    fields=["name", "reference_no", "paid_amount", "clearance_date", "docstatus"]))
rec("ALL_bank_statement_imports", frappe.get_all(
    "Bank Statement Import", fields=["name", "status", "import_file"], order_by="creation"))
rec("ALL_data_import_logs_count", frappe.db.count("Data Import Log"))
rec("ALL_banks", frappe.get_all("Bank", fields=["name"]))
rec("ALL_bank_accounts", frappe.get_all("Bank Account", fields=["name", "account"]))
rec("V22_accounts", frappe.get_all(
    "Account", filters={"account_name": ["like", "V22%"]}, fields=["name", "account_name"]))
rec("V22_files", frappe.get_all(
    "File", filters={"file_name": ["like", "V22%"]}, fields=["name", "file_name", "file_url",
                                                             "attached_to_doctype",
                                                             "attached_to_name"]))
rec("ALL_files_count", frappe.db.count("File"))
rec("ALL_gl_entries_on_test_account", frappe.get_all(
    "GL Entry", filters={"account": "V22测试银行存款 - HDS"},
    fields=["name", "voucher_type", "voucher_no", "debit", "credit", "is_cancelled"]))

for dt in ("Bank Transaction", "Payment Entry", "Bank Account", "Bank", "Error Log",
           "Bank Statement Import", "Data Import Log", "File", "GL Entry"):
    rec(f"count_{dt}", frappe.db.count(dt))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
