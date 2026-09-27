"""
V-27 seg1: READ-ONLY reconnaissance.

No writes at all. Gathers the runtime facts needed to decide whether a real
PCV submit can be done inside a rolled-back transaction:
  - which on_submit branch the site takes (use_legacy_controller_for_pcv)
  - estimate_count("GL Entry") -- decides enqueue vs direct call in make_gl_entries
  - is_scheduler_inactive() -- relevant only to the non-legacy PPCV path
  - company currency vs reporting_currency -- decides whether
    set_amount_in_reporting_currency() needs a Currency Exchange lookup
    (and possibly an outbound requests.get)
  - Currency Exchange Settings disabled flag
  - baseline row counts
  - raw GL facts (P&L movement by fiscal year) computed independently of the engine
"""

import json
import os

import frappe

OUT_DIR = "/workspace/Spike/V27-out"
SITE = "erx.localhost"
COMPANY = "华东弹簧"

frappe.init(site=SITE)
frappe.connect()

res = {}


def put(k, v):
    res[k] = v
    print("%-46s %s" % (k, json.dumps(v, ensure_ascii=False, default=str)))


# ---------------------------------------------------------------- branch switch
put("accounts_settings.use_legacy_controller_for_pcv",
    frappe.get_single_value("Accounts Settings", "use_legacy_controller_for_pcv"))
put("accounts_settings.ignore_account_closing_balance",
    frappe.get_single_value("Accounts Settings", "ignore_account_closing_balance"))

# ------------------------------------------- enqueue threshold in make_gl_entries
# period_closing_voucher.py:298  if frappe.db.estimate_count("GL Entry") > 100_000
est = frappe.db.estimate_count("GL Entry")
put("db.estimate_count_GL_Entry", est)
put("estimate_count_gt_100000__would_enqueue", bool(est > 100_000))
put("db.count_GL_Entry_exact", frappe.db.count("GL Entry"))

# ------------------------------------------------------- scheduler (PPCV path only)
try:
    from frappe.utils.scheduler import is_scheduler_inactive
    put("is_scheduler_inactive", bool(is_scheduler_inactive(verbose=False)))
except Exception as e:
    put("is_scheduler_inactive__error", str(e))

# ------------------------------------------------ reporting currency / exchange rate
comp = frappe.db.get_value(
    "Company", COMPANY,
    ["default_currency", "reporting_currency", "enable_perpetual_inventory",
     "abbr", "country"],
    as_dict=True,
)
put("company", comp)
put("currency_equal__get_exchange_rate_returns_1_immediately",
    bool(comp and comp.default_currency == comp.reporting_currency))
try:
    put("currency_exchange_settings.disabled",
        frappe.get_single_value("Currency Exchange Settings", "disabled"))
except Exception as e:
    put("currency_exchange_settings.disabled__error", str(e))
put("currency_exchange_row_count", frappe.db.count("Currency Exchange"))

# ---------------------------------------------------------- perpetual inventory
import erpnext
put("is_perpetual_inventory_enabled", bool(erpnext.is_perpetual_inventory_enabled(COMPANY)))
put("count_Stock_Ledger_Entry", frappe.db.count("Stock Ledger Entry"))
put("count_Stock_Closing_Entry", frappe.db.count("Stock Closing Entry"))

# ------------------------------------------------------------------- baseline
BASELINE = {}
for dt in ("GL Entry", "Stock Ledger Entry", "Account", "Company",
           "Financial Report Template", "Fiscal Year",
           "Period Closing Voucher", "Account Closing Balance",
           "Journal Entry", "Error Log"):
    BASELINE[dt] = frappe.db.count(dt)
put("BASELINE_counts", BASELINE)
put("fiscal_years", frappe.db.get_all(
    "Fiscal Year", fields=["name", "year_start_date", "year_end_date", "disabled"],
    order_by="year_start_date"))

# ------------------------------------------ raw GL: P&L movement, independent of engine
rows = frappe.db.sql(
    """
    SELECT gle.posting_date, gle.account, a.root_type, a.report_type,
           gle.debit, gle.credit, gle.voucher_type, gle.voucher_no, gle.is_opening
      FROM `tabGL Entry` gle
      JOIN `tabAccount` a ON a.name = gle.account
     WHERE gle.company = %s AND gle.is_cancelled = 0
     ORDER BY gle.posting_date, gle.account
    """,
    (COMPANY,), as_dict=True)
put("raw_gl_row_count", len(rows))
put("raw_gl_rows", rows)

pl_by_year = {}
pl_by_month = {}
for r in rows:
    if r["report_type"] != "Profit and Loss":
        continue
    y = str(r["posting_date"])[:4]
    m = str(r["posting_date"])[:7]
    pl_by_year[y] = round(pl_by_year.get(y, 0.0) + float(r["debit"]) - float(r["credit"]), 4)
    pl_by_month[m] = round(pl_by_month.get(m, 0.0) + float(r["debit"]) - float(r["credit"]), 4)
put("raw_pl_movement_by_year_debit_minus_credit", pl_by_year)
put("raw_pl_movement_by_month_debit_minus_credit", pl_by_month)

# candidate closing account heads (root_type Liability/Equity, leaf)
put("candidate_closing_accounts", frappe.db.get_all(
    "Account",
    filters={"company": COMPANY, "is_group": 0, "root_type": ["in", ["Liability", "Equity"]]},
    fields=["name", "root_type", "account_currency", "account_type"],
    limit=40))

# existing FRT templates (to know the baseline and find a P&L one to clone)
put("financial_report_templates", frappe.db.get_all(
    "Financial Report Template",
    fields=["name", "report_name", "module", "company", "report_type"]))

# accounting periods / freezing date could block submit
put("count_Accounting_Period", frappe.db.count("Accounting Period"))
put("accounts_settings.acc_frozen_upto",
    frappe.get_single_value("Accounts Settings", "acc_frozen_upto"))
put("accounts_settings.frozen_accounts_modifier",
    frappe.get_single_value("Accounts Settings", "frozen_accounts_modifier"))

os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "seg1-recon.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2, default=str)

# read-only probe: no writes were made, but roll back defensively anyway
frappe.db.rollback()
print("\nWROTE " + os.path.join(OUT_DIR, "seg1-recon.json"))
