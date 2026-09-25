# V-18 segment 1a: the proposition exactly as decision 5's option B states it.
#
#   - test app erx_v18 installed, carrying ONLY the 4 override_whitelisted_methods
#   - NO Company doc_events, NO frappe.local.flags.ignore_chart_of_accounts
#   - create a brand-new company with chart_of_accounts = 小企业会计准则(2024)
#
# Everything that happens after `company.insert()` is erpnext's own code.
# If it raises, the full traceback is the deliverable (it is the reason zelin
# bypassed the native path).
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V18-seg1-native-company.py

import json
import sys
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "V18原生甲"
ABBR = "V18A"
CHART = "小企业会计准则(2024)"
OUT = "/workspace/Spike/V18-out/seg1a-native-company.json"

result = {"segment": "1a native company creation, option B as stated"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
frappe.flags.in_test = False

# ---- 0. preconditions -------------------------------------------------------
rec("installed_apps", frappe.get_installed_apps())
rec(
    "hook_override_whitelisted_methods",
    frappe.get_hooks("override_whitelisted_methods", {}),
)
rec("hook_doc_events_Company", frappe.get_hooks("doc_events", {}).get("Company", "ABSENT"))
rec("flag_ignore_chart_of_accounts", frappe.local.flags.get("ignore_chart_of_accounts", "unset"))
rec("account_count_before", frappe.db.count("Account"))
rec("error_log_count_before", frappe.db.count("Error Log"))
rec("baseline_company_untouched_account_count", frappe.db.count("Account", {"company": "华东弹簧"}))

# ---- 1. does the override actually reach the creation path? -----------------
# override_whitelisted_method() is consulted at 4 dispatch points only
# (handler.py / api/v2.py / desk/treeview.py / model/mapper.py).  Record what
# it resolves to, and what a *direct import* (which is what Company uses) sees.
resolved = frappe.override_whitelisted_method(
    "erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_chart"
)
rec("override_resolves_get_chart_to", resolved)

from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa_mod

rec("erpnext_module_get_chart_is", f"{coa_mod.get_chart.__module__}.{coa_mod.get_chart.__name__}")

# what the whitelisted (HTTP) route would return -- i.e. what the desk UI sees
try:
    via_override = frappe.get_attr(resolved)(CHART)
    rec("get_chart_via_override_toplevel_keys", list(via_override.keys()) if via_override else via_override)
except Exception as e:
    rec("get_chart_via_override_ERROR", repr(e))

# what the native, directly-imported get_chart returns -- i.e. what
# create_charts() will actually be handed
try:
    via_native = coa_mod.get_chart(CHART)
    rec("get_chart_native_type", type(via_native).__name__)
    rec(
        "get_chart_native_toplevel_keys",
        list(via_native.keys()) if isinstance(via_native, dict) else repr(via_native),
    )
except Exception as e:
    rec("get_chart_native_ERROR", repr(e))
    rec("get_chart_native_traceback", traceback.format_exc())

# is the chart even offered for the country by the whitelisted route?
try:
    charts = frappe.get_attr(
        frappe.override_whitelisted_method(
            "erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country"
        )
    )("China")
    rec("get_charts_for_country_via_override", charts)
except Exception as e:
    rec("get_charts_for_country_via_override_ERROR", repr(e))

try:
    rec("get_charts_for_country_native", coa_mod.get_charts_for_country("China"))
except Exception as e:
    rec("get_charts_for_country_native_ERROR", repr(e))

# ---- 2. create the company through the fully native path -------------------
if frappe.db.exists("Company", COMPANY):
    rec("precondition_ERROR", f"{COMPANY} already exists; aborting")
    frappe.destroy()
    sys.exit(2)

doc = frappe.get_doc(
    {
        "doctype": "Company",
        "company_name": COMPANY,
        "abbr": ABBR,
        "default_currency": "CNY",
        "country": "China",
        "chart_of_accounts": CHART,
        "create_chart_of_accounts_based_on": "Standard Template",
    }
)

rec("insert_attempt", "starting company.insert()")
try:
    doc.insert()
    frappe.db.commit()
    rec("insert_result", "NO EXCEPTION")
    result["insert_failed"] = False
except Exception as e:
    frappe.db.rollback()
    result["insert_failed"] = True
    rec("insert_result", "RAISED")
    rec("exception_type", type(e).__name__)
    rec("exception_str", str(e))
    tb = traceback.format_exc()
    result["traceback"] = tb
    print("=== TRACEBACK BEGIN ===", flush=True)
    print(tb, flush=True)
    print("=== TRACEBACK END ===", flush=True)

# ---- 3. what state did it leave behind? ------------------------------------
rec("company_exists_after", bool(frappe.db.exists("Company", COMPANY)))
rec("account_count_for_test_company", frappe.db.count("Account", {"company": COMPANY}))
rec("account_count_total_after", frappe.db.count("Account"))
rec("baseline_company_account_count_after", frappe.db.count("Account", {"company": "华东弹簧"}))
rec("error_log_count_after", frappe.db.count("Error Log"))
rec(
    "error_logs_new",
    frappe.get_all(
        "Error Log", fields=["name", "method", "creation"], order_by="creation desc", limit=8
    ),
)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print(f"\nwrote {OUT}", flush=True)

frappe.destroy()
