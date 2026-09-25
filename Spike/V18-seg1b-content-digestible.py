# V-18 segment 1b: isolate CONTENT from DELIVERY.
#
# 1a showed option B as literally stated cannot even *find* the chart: the four
# `override_whitelisted_methods` are consulted only at frappe's 4 whitelist
# dispatch points, while Company.create_default_accounts() does a plain
# `from ...chart_of_accounts import create_charts`, and create_charts() then
# calls its own module-global get_chart() -- which searches only
# apps/erpnext/.../chart_of_accounts/verified/ and returns None.
#
# So "can the NATIVE creation code digest that JSON" is still unanswered.  This
# probe answers it by making delivery succeed artificially: monkeypatch
# coa_mod.get_chart in-process to hand back the app's (zelin's) tree, then run
# the完全 native Company.insert() path -- no doc_events, no
# ignore_chart_of_accounts, native create_charts, native
# sync_financial_report_templates, native create_default_tax_template.
#
# The monkeypatch is PROBE SCAFFOLDING, not a mechanism option B can use.  It
# exists only to separate "content is indigestible" from "content never arrives".
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V18-seg1b-content-digestible.py

import json
import sys
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "V18原生乙"
ABBR = "V18B"
CHART = "小企业会计准则(2024)"
OUT = "/workspace/Spike/V18-out/seg1b-content-digestible.json"

result = {"segment": "1b content digestibility, delivery force-fed by probe scaffold"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

rec("account_count_before", frappe.db.count("Account"))
rec("error_log_count_before", frappe.db.count("Error Log"))
rec("baseline_company_accounts_before", frappe.db.count("Account", {"company": "华东弹簧"}))
rec("sales_templates_before", frappe.db.count("Sales Taxes and Charges Template"))

# ---- monkeypatch: make native lookup resolve to the app's chart -------------
from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa_mod
from erx_v18.chart_of_accounts.custom_accounts import custom_account as app_mod

_native_get_chart = coa_mod.get_chart
_calls = {"n": 0, "args": []}


def patched_get_chart(chart_template, existing_company=None):
    _calls["n"] += 1
    _calls["args"].append((chart_template, existing_company))
    return app_mod.get_chart(chart_template, existing_company)


coa_mod.get_chart = patched_get_chart
rec("scaffold", "coa_mod.get_chart -> erx_v18 app get_chart (probe only)")

tree = app_mod.get_chart(CHART)
rec("chart_toplevel_keys", list(tree.keys()))
rec("chart_toplevel_root_types", {k: v.get("root_type") for k, v in tree.items()})

META = {
    "account_name", "account_number", "account_type", "account_category",
    "root_type", "is_group", "tax_rate", "account_currency",
}


def count_nodes(node):
    n = 0
    for k, v in node.items():
        if k in META:
            continue
        n += 1
        if isinstance(v, dict):
            n += count_nodes(v)
    return n


rec("chart_json_node_count", len(tree) + sum(count_nodes(v) for v in tree.values()))

if frappe.db.exists("Company", COMPANY):
    rec("precondition_ERROR", f"{COMPANY} already exists; aborting")
    frappe.destroy()
    sys.exit(2)

# ---- native company creation ------------------------------------------------
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

rec("flag_ignore_chart_of_accounts_at_insert", frappe.local.flags.get("ignore_chart_of_accounts", "unset"))
rec("hook_doc_events_Company", frappe.get_hooks("doc_events", {}).get("Company", "ABSENT"))

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

rec("get_chart_call_count_during_insert", _calls["n"])
rec("get_chart_call_args", _calls["args"])

coa_mod.get_chart = _native_get_chart

# ---- measure what got built -------------------------------------------------
rec("company_exists_after", bool(frappe.db.exists("Company", COMPANY)))
n_acc = frappe.db.count("Account", {"company": COMPANY})
rec("ACCOUNT_COUNT_for_test_company", n_acc)
rec("account_count_total_after", frappe.db.count("Account"))
rec("baseline_company_accounts_after", frappe.db.count("Account", {"company": "华东弹簧"}))

if n_acc:
    roots = frappe.get_all(
        "Account",
        filters={"company": COMPANY, "parent_account": ("is", "not set")},
        fields=["name", "account_name", "account_number", "root_type", "report_type", "is_group"],
        order_by="account_number",
    )
    rec("ROOT_ACCOUNTS", roots)

    expected_roots = {
        "资产类": "Asset", "负债类": "Liability", "权益类": "Equity",
        "成本类": "Asset", "收入类": "Income", "费用类": "Expense",
    }
    got = {r["account_name"]: r["root_type"] for r in roots}
    rec("ROOT_TYPE_expected", expected_roots)
    rec("ROOT_TYPE_actual", got)
    rec("ROOT_TYPE_all_correct", got == expected_roots)

    # the 20 VAT detail lines 2221001..2221020
    vat = {}
    for i in range(1, 21):
        num = f"22210{i:02d}"
        row = frappe.get_all(
            "Account",
            filters={"company": COMPANY, "account_number": num},
            fields=["name", "account_name", "account_number", "parent_account", "is_group", "account_type", "root_type"],
        )
        vat[num] = row[0] if row else None
    rec("VAT_2221001_to_2221020", vat)
    rec("VAT_present_count", sum(1 for v in vat.values() if v))
    rec("VAT_missing", [k for k, v in vat.items() if not v])

    parent_2221000 = frappe.get_all(
        "Account",
        filters={"company": COMPANY, "account_number": "2221000"},
        fields=["name", "account_name", "is_group", "root_type", "account_type", "lft", "rgt"],
    )
    rec("ACCOUNT_2221000", parent_2221000)
    if parent_2221000:
        kids = frappe.get_all(
            "Account",
            filters={"company": COMPANY, "parent_account": parent_2221000[0]["name"]},
            fields=["account_number", "account_name", "is_group"],
            order_by="account_number",
        )
        rec("children_of_2221000", kids)
        rec("children_of_2221000_count", len(kids))

    p2221 = frappe.get_all(
        "Account", filters={"company": COMPANY, "account_number": "2221"}, fields=["name", "account_name"]
    )
    if p2221:
        kids2 = frappe.get_all(
            "Account",
            filters={"company": COMPANY, "parent_account": p2221[0]["name"]},
            fields=["account_number", "account_name", "is_group"],
            order_by="account_number",
        )
        rec("children_of_2221_count", len(kids2))
        rec("children_of_2221", kids2)

    rec("root_type_histogram", frappe.db.sql(
        "select root_type, count(*) from tabAccount where company=%s group by root_type", COMPANY
    ))
    rec("nsm_broken_lft_rgt", frappe.db.sql(
        "select count(*) from tabAccount where company=%s and (lft is null or rgt is null or lft>=rgt)", COMPANY
    ))
    rec("orphan_nonroot_accounts", frappe.db.sql(
        "select count(*) from tabAccount a where a.company=%s and a.parent_account is not null "
        "and a.parent_account != '' and not exists (select 1 from tabAccount b where b.name=a.parent_account)",
        COMPANY,
    ))
    rec("duplicate_suffixed_names", frappe.get_all(
        "Account", filters={"company": COMPANY, "account_name": ("like", "% 1")},
        fields=["name", "account_name", "account_number"], limit=20,
    ))

# what natively-created tax artifacts appeared (native create_default_tax_template)
rec("sales_templates_after_native", frappe.get_all(
    "Sales Taxes and Charges Template", filters={"company": COMPANY}, fields=["name", "title"]
))
rec("purchase_templates_after_native", frappe.get_all(
    "Purchase Taxes and Charges Template", filters={"company": COMPANY}, fields=["name", "title"]
))
rec("company_defaults", frappe.db.get_value(
    "Company", COMPANY,
    ["default_receivable_account", "default_payable_account", "default_income_account",
     "default_expense_account", "cost_center", "round_off_account"], as_dict=True,
))
rec("warehouse_count", frappe.db.count("Warehouse", {"company": COMPANY}))
rec("error_log_count_after", frappe.db.count("Error Log"))
rec("error_logs_recent", frappe.get_all(
    "Error Log", fields=["name", "method", "creation"], order_by="creation desc", limit=10
))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print(f"\nwrote {OUT}", flush=True)

frappe.destroy()
