# V-22 segment 15: clear the last residue -- 6 orphaned GL Entry rows.
#
# Each of the 3 throwaway Payment Entries wrote 2 GL Entry rows (paid_from
# 应收账款 1 - HDS and paid_to V22测试银行存款 - HDS), and cancelling each wrote 2
# reversals. Segment 14 removed the 6 that named the V22 account (required before
# Account.on_trash would allow the delete). The 6 on 应收账款 1 - HDS survived:
# their parent Payment Entry is gone, so they are orphans.
#
# Deleting an orphan GL row is only safe because its voucher no longer exists,
# which is asserted per-row below. Nothing belonging to a LIVE voucher is touched.
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg15-gl-residue.py

import json

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
OUT = "/workspace/Spike/V22-out/seg15-gl-residue.json"

result = {"segment": "15 clear orphaned GL entries"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
frappe.flags.ignore_links = True

rec("gl_total_before", frappe.db.count("GL Entry"))

allgl = frappe.get_all("GL Entry", fields=["name", "account", "voucher_type", "voucher_no",
                                           "debit", "credit", "is_cancelled", "posting_date"],
                       order_by="creation")
orphans, live = [], []
for g in allgl:
    (live if frappe.db.exists(g.voucher_type, g.voucher_no) else orphans).append(g)

rec("orphan_count", len(orphans))
rec("orphans", orphans)
rec("live_count", len(live))
rec("orphan_vouchers", sorted({g.voucher_no for g in orphans}))
rec("orphan_accounts", sorted({g.account for g in orphans}))

# safety: every orphan must be one of OUR payment entries, and its voucher gone
V22_PES = {"ACC-PAY-2026-00008", "ACC-PAY-2026-00009", "ACC-PAY-2026-00010"}
unexpected = [g for g in orphans if g.voucher_no not in V22_PES]
rec("unexpected_orphans_NOT_deleted", unexpected)

for g in orphans:
    if g.voucher_no in V22_PES and not frappe.db.exists(g.voucher_type, g.voucher_no):
        frappe.db.delete("GL Entry", {"name": g.name})
        print(f"  .. deleted orphan GL Entry {g.name} {g.account} ({g.voucher_no})", flush=True)
frappe.db.commit()

rec("gl_total_after", frappe.db.count("GL Entry"))
rec("gl_for_company_not_cancelled", frappe.db.count("GL Entry", {"company": COMPANY,
                                                                 "is_cancelled": 0}))
rec("gl_cancelled_left", frappe.db.count("GL Entry", {"is_cancelled": 1}))
remaining = frappe.get_all("GL Entry", fields=["name", "voucher_type", "voucher_no"])
rec("any_orphans_left", [g for g in remaining
                        if not frappe.db.exists(g.voucher_type, g.voucher_no)])

# ---------------------------------------------------------------- final re-count
FINAL = {}
for dt in ("Bank Transaction", "Payment Entry", "Bank Account", "Bank", "Error Log",
           "Bank Statement Import", "Data Import Log", "File", "GL Entry",
           "Bank Transaction Mapping", "Bank Transaction Payments", "Stock Ledger Entry",
           "Account", "Sales Order", "BOM", "Company"):
    FINAL[dt] = frappe.db.count(dt)
rec("FINAL_counts", FINAL)

BASELINE_5 = {"Bank Transaction": 0, "Payment Entry": 2, "Bank Account": 0, "Bank": 0,
              "Error Log": 1}
rec("the_5_tracked_counts_match_baseline",
    {k: (FINAL[k], BASELINE_5[k], FINAL[k] == BASELINE_5[k]) for k in BASELINE_5})

rec("demo_payment_entries", frappe.get_all(
    "Payment Entry", fields=["name", "payment_type", "party", "paid_amount", "clearance_date",
                             "docstatus"], order_by="name"))
rec("error_logs", frappe.get_all("Error Log", fields=["name", "method"], order_by="creation desc"))
rec("V22_leftovers_anywhere", {
    "accounts": frappe.get_all("Account", filters={"account_name": ["like", "V22%"]}, pluck="name"),
    "files": frappe.get_all("File", filters={"file_name": ["like", "V22%"]}, pluck="name"),
    "banks": frappe.get_all("Bank", pluck="name"),
    "bank_accounts": frappe.get_all("Bank Account", pluck="name"),
    "pes": frappe.get_all("Payment Entry", filters={"reference_no": ["like", "V22%"]}, pluck="name"),
})

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
