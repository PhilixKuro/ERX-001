# V-22 segment 17: correct segment 16's note and remove the last residue.
#
# Segment 16's note was WRONG about the numbers. What tabSeries actually shows:
#   ACC-PAY-2026- = 7  -- i.e. EXACTLY the baseline. frappe's revert_series_if_last
#                         walked it back 10 -> 9 -> 8 -> 7 because the throwaway
#                         payment entries were deleted newest-first.
#   ACC-BTN-2026- = 11 -- a row that did NOT exist at baseline (Bank Transaction
#                         count was 0 and there was no Bank Account at all, so no
#                         Bank Transaction had ever been named on this site).
#                         It reverted 12 -> 11 on the last delete only.
#
# Bank Transaction count is 0, so dropping this unused series row returns the site
# to baseline exactly; frappe recreates it on first use, starting at 00001, which
# is the baseline behaviour. Guarded: refuses if any Bank Transaction exists.
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg17-series-cleanup.py

import json

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/V22-out/seg17-series-cleanup.json"

result = {"segment": "17 drop the unused ACC-BTN series row"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()

rec("series_before", frappe.db.sql("select name, current from tabSeries order by name", as_list=True))
n_bt = frappe.db.count("Bank Transaction")
rec("bank_transaction_count", n_bt)

if n_bt == 0 and frappe.db.sql("select 1 from tabSeries where name='ACC-BTN-2026-'"):
    frappe.db.sql("delete from tabSeries where name='ACC-BTN-2026-'")
    frappe.db.commit()
    rec("dropped_ACC_BTN_series", True)
else:
    rec("dropped_ACC_BTN_series", False)
    rec("reason", f"Bank Transaction count = {n_bt}; refusing to touch the series row")

rec("series_after", frappe.db.sql("select name, current from tabSeries order by name", as_list=True))
rec("ACC_PAY_counter", frappe.db.sql(
    "select current from tabSeries where name='ACC-PAY-2026-'", as_list=True))
rec("ACC_BTN_row_exists", bool(frappe.db.sql("select 1 from tabSeries where name='ACC-BTN-2026-'")))

# ------------------------------------------------------------- absolute final state
FINAL = {}
for dt in ("Bank Transaction", "Payment Entry", "Bank Account", "Bank", "Error Log",
           "Bank Statement Import", "Data Import Log", "File", "GL Entry",
           "Bank Transaction Mapping", "Bank Transaction Payments", "Account",
           "Stock Ledger Entry", "Sales Order", "BOM", "Company", "Sales Invoice"):
    FINAL[dt] = frappe.db.count(dt)
rec("FINAL_counts", FINAL)

BASELINE = {"Bank Transaction": 0, "Payment Entry": 2, "Bank Account": 0, "Bank": 0,
            "Error Log": 1, "Bank Statement Import": 0, "Data Import Log": 0, "File": 2,
            "GL Entry": 22, "Bank Transaction Mapping": 0, "Bank Transaction Payments": 0,
            "Account": 95, "Stock Ledger Entry": 12, "Sales Order": 2, "BOM": 1,
            "Company": 1, "Sales Invoice": 1}
rec("delta_vs_baseline", {k: FINAL[k] - BASELINE[k] for k in BASELINE})
rec("RESIDUE_FINAL",
    {k: FINAL[k] - BASELINE[k] for k in BASELINE if FINAL[k] != BASELINE[k]}
    or "NONE -- every tracked count identical to the segment-0 baseline")

rec("demo_payment_entries", frappe.get_all(
    "Payment Entry", fields=["name", "payment_type", "party", "paid_amount", "clearance_date",
                             "docstatus"], order_by="name"))
rec("demo_untouched_clearance_still_null",
    all(p["clearance_date"] is None for p in frappe.get_all("Payment Entry",
                                                            fields=["clearance_date"])))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
