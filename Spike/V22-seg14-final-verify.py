# V-22 segment 14: finish removing the V22 GL account, then verify the cleanup by
# RE-COUNTING against the segment-0 baseline.
#
# Segment 13 could not delete V22测试银行存款 - HDS: Account.on_trash refuses while
# any GL Entry still names it. Deleting the Payment Entries left their CANCELLED
# GL Entries behind (is_cancelled=1), which still count as existing transactions.
# So: remove those orphaned GL Entry rows first, then the Account.
#
# Baseline to return to (from V22-out/seg0-baseline.json):
#   Bank Transaction 0 | Payment Entry 2 | Bank Account 0 | Bank 0 | Error Log 1
#   Bank Statement Import 0 | Data Import Log 0 | File 2 | GL Entry 22
#   and ACC-PAY-2026-00006 / 00007 both with clearance_date = None
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg14-final-verify.py

import json

import frappe

SITE = "erx.localhost"
ACC = "V22测试银行存款 - HDS"
COMPANY = "华东弹簧"
OUT = "/workspace/Spike/V22-out/seg14-final-verify.json"

BASELINE = {
    "Bank Transaction": 0, "Payment Entry": 2, "Bank Account": 0, "Bank": 0,
    "Error Log": 1, "Bank Statement Import": 0, "Data Import Log": 0,
    "File": 2, "GL Entry": 22,
}

result = {"segment": "14 final cleanup + verification vs baseline"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
frappe.flags.ignore_links = True

# ---------------------------------------------- orphaned GL entries on the V22 account
orphans = frappe.get_all("GL Entry", filters={"account": ACC},
                         fields=["name", "voucher_type", "voucher_no", "debit", "credit",
                                 "is_cancelled"])
rec("gl_entries_on_V22_account", orphans)
rec("their_vouchers_still_exist",
    {o.voucher_no: bool(frappe.db.exists(o.voucher_type, o.voucher_no)) for o in orphans})

for o in orphans:
    # only safe because the parent Payment Entry is already gone (asserted above)
    if not frappe.db.exists(o.voucher_type, o.voucher_no):
        frappe.db.delete("GL Entry", {"name": o.name})
        print(f"  .. deleted orphan GL Entry {o.name} ({o.voucher_no})", flush=True)
frappe.db.commit()
rec("gl_entries_on_V22_account_after", frappe.db.count("GL Entry", {"account": ACC}))

try:
    if frappe.db.exists("Account", ACC):
        frappe.delete_doc("Account", ACC, force=1, ignore_permissions=True, ignore_missing=True)
        frappe.db.commit()
        print(f"  .. deleted Account {ACC}", flush=True)
except Exception:
    rec("account_delete_TRACEBACK", frappe.get_traceback(with_context=False)[-600:])

# ------------------------------------------------------------------ verification
rec("V22_accounts_left", frappe.get_all("Account", filters={"account_name": ["like", "V22%"]},
                                        fields=["name"]))
rec("V22_files_left", frappe.get_all("File", filters={"file_name": ["like", "V22%"]},
                                     fields=["name", "file_name"]))
rec("V22_payment_entries_left", frappe.get_all(
    "Payment Entry", filters={"reference_no": ["like", "V22REF%"]}, fields=["name"]))
rec("banks_left", frappe.get_all("Bank", fields=["name"]))
rec("bank_accounts_left", frappe.get_all("Bank Account", fields=["name"]))
rec("bank_transaction_mapping_rows_left", frappe.db.count("Bank Transaction Mapping"))
rec("bank_transaction_payments_left", frappe.db.count("Bank Transaction Payments"))

counts = {}
for dt in BASELINE:
    counts[dt] = frappe.db.count(dt)
rec("counts_now", counts)
delta = {dt: counts[dt] - BASELINE[dt] for dt in BASELINE}
rec("delta_vs_baseline", delta)
rec("RESIDUE", {dt: d for dt, d in delta.items() if d != 0} or "NONE -- every count back to baseline")

# the demo's own vouchers must be exactly as segment 0 found them
demo = frappe.get_all("Payment Entry",
                      filters={"name": ["in", ["ACC-PAY-2026-00006", "ACC-PAY-2026-00007"]]},
                      fields=["name", "payment_type", "party", "paid_amount", "posting_date",
                              "clearance_date", "docstatus", "paid_from", "paid_to"],
                      order_by="name")
rec("demo_payment_entries_final", demo)
rec("demo_untouched",
    all(d["clearance_date"] is None and d["docstatus"] == 1 for d in demo) and len(demo) == 2)

rec("demo_gl_entry_count", frappe.db.count("GL Entry", {"company": COMPANY, "is_cancelled": 0}))
rec("demo_sle_count", frappe.db.count("Stock Ledger Entry"))
rec("demo_accounts_count", frappe.db.count("Account", {"company": COMPANY}))
rec("demo_sales_orders", frappe.db.count("Sales Order"))
rec("demo_boms", frappe.db.count("BOM"))
rec("demo_warehouses", frappe.db.count("Warehouse", {"company": COMPANY}))
rec("companies", frappe.get_all("Company", fields=["name", "abbr"]))
rec("error_logs_final", frappe.get_all("Error Log", fields=["name", "method", "creation"],
                                       order_by="creation desc"))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
