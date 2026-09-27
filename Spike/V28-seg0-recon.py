# V-28 seg0 RECON (read-only): is there already multi-month GL on this site?
#
# V-26 established that the PROFIT-AND-LOSS GL all sits in 2026-09, which is why
# it could not test multi-month cumulative arithmetic. But V-26 only summed
# root_type in (Income, Expense). This recon asks the wider question: across ALL
# accounts, which months carry postings, and are there accounts with postings in
# two or more distinct months?
#
# If yes -> V-28 can be run with NO synthetic GL at all (least invasive).
# If no  -> V-28 must create a second month of postings inside a transaction.
#
# Also records the safety baseline and the engine's opening-balance preconditions.
#
# READ ONLY. No insert, no commit. rollback() in finally as hygiene.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V28-seg0-recon.py

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
OUTDIR = "/workspace/Spike/V28-out"
OUT = OUTDIR + "/seg0-recon.json"

result = {"probe": "V-28 seg0 recon: existing multi-month GL + safety baseline"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2500], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    # ---------- 1. safety baseline BEFORE anything ----------
    baseline = {}
    for dt in ["GL Entry", "Stock Ledger Entry", "Account", "Company",
               "Financial Report Template", "Fiscal Year", "Journal Entry",
               "Period Closing Voucher", "Account Closing Balance"]:
        baseline[dt] = frappe.db.count(dt)
    rec("baseline_counts", baseline)
    rec("fiscal_years", [r.name for r in frappe.get_all("Fiscal Year", fields=["name"])])

    # ---------- 2. engine preconditions (affect which opening-balance path runs) ----------
    rec("accounts_settings_flags", {
        "ignore_account_closing_balance": frappe.get_single_value(
            "Accounts Settings", "ignore_account_closing_balance"),
        "ignore_is_opening_check_for_reporting": frappe.get_single_value(
            "Accounts Settings", "ignore_is_opening_check_for_reporting"),
    })

    # ---------- 3. EVERY GL entry on the site, by month and by account ----------
    gl = frappe.get_all(
        "GL Entry",
        filters={"company": COMPANY, "is_cancelled": 0},
        fields=["name", "account", "posting_date", "debit", "credit", "is_opening",
                "voucher_type", "voucher_no"],
        order_by="posting_date asc")
    rec("gl_entry_rows_total", len(gl))

    months_all = {}
    per_account_months = {}
    for r in gl:
        m = str(r.posting_date)[:7]
        months_all[m] = months_all.get(m, 0) + 1
        per_account_months.setdefault(r.account, {})
        per_account_months[r.account][m] = round(
            per_account_months[r.account].get(m, 0.0) + (r.debit or 0.0) - (r.credit or 0.0), 4)
    rec("gl_row_count_by_month", months_all)
    rec("distinct_posting_months", sorted(months_all.keys()))

    multi = {a: v for a, v in per_account_months.items() if len(v) > 1}
    rec("accounts_with_postings_in_2plus_months", multi)
    rec("accounts_with_postings_in_2plus_months_count", len(multi))

    # root_type of every account that carries GL -- matters because the engine's
    # Closing Balance for PL vs BS behaves the same but the template report_type differs
    acc_names = sorted(per_account_months.keys())
    acc_meta = frappe.get_all("Account", filters={"name": ["in", acc_names]},
                              fields=["name", "root_type", "account_type", "is_group"])
    rec("accounts_carrying_gl", [
        {"account": a.name, "root_type": a.root_type, "is_group": a.is_group,
         "months": per_account_months.get(a.name)} for a in acc_meta])

    # ---------- 4. per-month movement by root_type (independent raw sums) ----------
    rt_of = {a.name: a.root_type for a in acc_meta}
    by_rt_month = {}
    for r in gl:
        m = str(r.posting_date)[:7]
        rt = rt_of.get(r.account, "?")
        by_rt_month.setdefault(rt, {})
        by_rt_month[rt][m] = round(
            by_rt_month[rt].get(m, 0.0) + (r.debit or 0.0) - (r.credit or 0.0), 4)
    rec("raw_movement_by_roottype_by_month", by_rt_month)

    # ---------- 5. voucher inventory (what made this GL) ----------
    vt = {}
    for r in gl:
        vt[r.voucher_type] = vt.get(r.voucher_type, 0) + 1
    rec("gl_by_voucher_type", vt)

    # ---------- 6. does an exported-template stray already exist? ----------
    import glob
    d = frappe.get_app_path("erpnext", "accounts", "financial_report_template")
    rec("financial_report_template_dir_listing",
        sorted(os.path.basename(p) for p in glob.glob(d + "/*")) if os.path.isdir(d) else "DIR_ABSENT")

    rec("existing_templates", [r.name for r in frappe.get_all(
        "Financial Report Template", fields=["name"])])

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-2500:]})

finally:
    frappe.db.rollback()
    if not os.path.isdir(OUTDIR):
        os.makedirs(OUTDIR)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
