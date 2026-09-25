# V-18 segment 9: close the one inference left over from 1a.
#
# In 1a the company insert died at company.py:348 `sync_financial_report_templates`,
# i.e. BEFORE line 349 ever called create_default_accounts().  So 1a never
# actually observed what native create_charts() does when get_chart() hands it
# None -- that was read off the source, not measured.
#
# This closes it with ZERO database writes: create_charts() begins
#   chart = custom_chart or get_chart(chart_template, existing_company)
#   if chart:
# so when get_chart returns None the function returns before touching the
# company argument at all.  Passing a company name that does not exist is
# therefore safe, and proves the branch is silent rather than raising.
#
# Runs with the test app already uninstalled -- neither function depends on it.
# Read-only.  Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V18-seg9-create-charts-none.py

import json
import traceback

import frappe

SITE = "erx.localhost"
CHART = "小企业会计准则(2024)"
FAKE_COMPANY = "不存在的公司V18探针"
OUT = "/workspace/Spike/V18-out/seg9-create-charts-none.json"

result = {"segment": "9 native create_charts when get_chart returns None"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()

rec("installed_apps", frappe.get_installed_apps())
rec("app_uninstalled", "erx_v18" not in frappe.get_installed_apps())

from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa_mod

rec("native_get_chart_returns", repr(coa_mod.get_chart(CHART)))
rec("native_get_charts_for_country_China", coa_mod.get_charts_for_country("China"))

# how many cn* / China charts does erpnext ship?
import os

verified = os.path.join(os.path.dirname(coa_mod.__file__), "verified")
files = sorted(os.listdir(verified))
rec("erpnext_verified_json_count", len([f for f in files if f.endswith(".json")]))
rec("erpnext_verified_cn_or_China_files", [f for f in files if f.startswith("cn") or f.startswith("China")])
rec("unverified_dir_exists", os.path.exists(os.path.join(os.path.dirname(coa_mod.__file__), "unverified")))

acc_before = frappe.db.count("Account")
rec("account_count_before", acc_before)

# the decisive call: does it raise, or silently do nothing?
try:
    ret = coa_mod.create_charts(FAKE_COMPANY, CHART, None)
    rec("create_charts_result", "RETURNED WITHOUT RAISING")
    rec("create_charts_return_value", repr(ret))
except Exception as e:
    rec("create_charts_result", "RAISED")
    rec("create_charts_exception", repr(e))
    result["create_charts_traceback"] = traceback.format_exc()
    print(result["create_charts_traceback"], flush=True)

rec("account_count_after", frappe.db.count("Account"))
rec("accounts_created_by_this_call", frappe.db.count("Account") - acc_before)
rec("accounts_for_fake_company", frappe.db.count("Account", {"company": FAKE_COMPANY}))
rec("fake_company_exists", bool(frappe.db.exists("Company", FAKE_COMPANY)))
rec("baseline_accounts", frappe.db.count("Account", {"company": "华东弹簧"}))

# and confirm the crash site from 1a is exactly this None flowing onward
from erpnext.accounts.doctype.financial_report_template import financial_report_template as frt

import inspect

src = inspect.getsource(frt.sync_financial_report_templates)
rec("sync_financial_report_templates_coa_lines", [
    ln.strip() for ln in src.splitlines() if "get_chart" in ln or "coa.get" in ln])
rec("company_on_update_guard_line", [
    ln.strip() for ln in inspect.getsource(
        frappe.get_attr("erpnext.setup.doctype.company.company.Company").on_update
    ).splitlines()[:12]])

frappe.db.rollback()
rec("rolled_back", True)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print(f"\nwrote {OUT}", flush=True)

frappe.destroy()
