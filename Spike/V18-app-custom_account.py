# V-18 probe payload: the FOUR `override_whitelisted_methods` targets, copied
# from zelin (Reference/zelin-tech-erpnext_china/erpnext_china/chart_of_accounts/
# custom_accounts/custom_account.py, MIT) with only the app name changed
# erpnext_china -> erx_v18 in the on-disk chart paths.
#
# Deliberately NOT copied: `erpnext_china_create_charts`.  That function is
# zelin's *bypass* of the native creation path, and decision 5 option B
# proposes doing without it.  Including it here would let the probe accidentally
# prove the wrong thing.

import json
import os

import frappe
from frappe import _
from frappe.utils import cstr
from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import (
    get_chart as original_get_chart,
    get_account_tree_from_existing_company,
)


@frappe.whitelist()
def get_coa(doctype, parent, is_root=None, chart=None):
    from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import (
        build_tree_from_json,
    )

    chart = chart if chart else frappe.flags.chart
    frappe.flags.chart = chart
    chart_data = get_chart(chart)
    parent = None if parent == _("All Accounts") else parent
    accounts = build_tree_from_json(chart, chart_data)
    accounts = [d for d in accounts if d["parent_account"] == parent]
    return accounts


@frappe.whitelist()
def get_chart(chart_template, existing_company=None):
    if chart_template in ["Standard", "Standard with Numbers"]:
        return original_get_chart(chart_template, existing_company)

    chart = {}
    if existing_company:
        return get_account_tree_from_existing_company(existing_company)

    bench_dir = frappe.utils.get_bench_path()
    erpnext_charts_path = os.path.join(
        bench_dir, "apps", "erpnext", "erpnext", "accounts", "doctype",
        "account", "chart_of_accounts",
    )

    folders = ("verified",)
    if frappe.local.flags.allow_unverified_charts:
        folders = ("verified", "unverified")
    for folder in folders:
        path = os.path.join(erpnext_charts_path, folder)
        for fname in os.listdir(path):
            fname = frappe.as_unicode(fname)
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(path, fname)) as f:
                        chart = f.read()
                        if chart and json.loads(chart).get("name") == chart_template:
                            return json.loads(chart).get("tree")
                except Exception as e:
                    frappe.log_error(
                        f"Error reading chart file in get_chart: {e}",
                        title="Chart File Read Error",
                    )

    custom_path = os.path.join(
        bench_dir, "apps", "erx_v18", "erx_v18", "chart_of_accounts", "custom_accounts"
    )
    custom_folders = ("chart_of_accounts", "custom_of_accounts")
    for custom_folder in custom_folders:
        custom_charts_path = os.path.join(custom_path, custom_folder)
        if os.path.exists(custom_charts_path):
            for fname1 in os.listdir(custom_charts_path):
                fname1 = frappe.as_unicode(fname1)
                if fname1.endswith(".json"):
                    try:
                        with open(os.path.join(custom_charts_path, fname1)) as f1:
                            chart1 = f1.read()
                            if chart1 and json.loads(chart1).get("name") == chart_template:
                                return json.loads(chart1).get("tree")
                    except Exception as e:
                        frappe.log_error(
                            f"Error reading custom chart file in get_chart: {e}",
                            title="Custom Chart File Read Error",
                        )

    return chart


@frappe.whitelist()
def get_charts_for_country(country, with_standard=False):
    charts = []
    bench_dir = frappe.utils.get_bench_path()

    def _get_chart_name(content):
        if content:
            try:
                content = json.loads(content)
                if (
                    content and content.get("disabled", "No") == "No"
                ) or frappe.local.flags.allow_unverified_charts:
                    charts.append(content["name"])
            except Exception as e:
                frappe.log_error(
                    f"Error parsing chart content in get_charts_for_country: {e}",
                    title="Chart Content Parse Error",
                )

    country_code = frappe.get_cached_value("Country", country, "code")
    if country_code:
        folders = ("verified",)
        if frappe.local.flags.allow_unverified_charts:
            folders = ("verified", "unverified")

        erpnext_charts_path = os.path.join(
            bench_dir, "apps", "erpnext", "erpnext", "accounts", "doctype",
            "account", "chart_of_accounts",
        )
        for folder in folders:
            path = os.path.join(erpnext_charts_path, folder)
            if os.path.exists(path):
                for fname in os.listdir(path):
                    fname = frappe.as_unicode(fname)
                    if (
                        fname.startswith(country_code) or fname.startswith(country)
                    ) and fname.endswith(".json"):
                        try:
                            with open(os.path.join(path, fname)) as f:
                                _get_chart_name(f.read())
                        except Exception as e:
                            frappe.log_error(
                                f"Error reading country chart file: {e}",
                                title="Country Chart File Read Error",
                            )

    if len(charts) != 1 or with_standard:
        charts += ["Standard", "Standard with Numbers"]

    custom_path = os.path.join(
        bench_dir, "apps", "erx_v18", "erx_v18", "chart_of_accounts", "custom_accounts"
    )
    custom_folders = ("chart_of_accounts", "custom_of_accounts")
    for custom_folder in custom_folders:
        custom_charts_path = os.path.join(custom_path, custom_folder)
        if os.path.exists(custom_charts_path):
            for fname1 in os.listdir(custom_charts_path):
                fname1 = frappe.as_unicode(fname1)
                if (
                    fname1.startswith(country_code) or fname1.startswith(country)
                ) and fname1.endswith(".json"):
                    try:
                        with open(os.path.join(custom_charts_path, fname1)) as f1:
                            _get_chart_name(f1.read())
                    except Exception as e:
                        frappe.log_error(
                            f"Error reading custom country chart file: {e}",
                            title="Custom Country Chart File Read Error",
                        )

    return charts


@frappe.whitelist()
def get_all_nodes(doctype, label, parent, tree_method, **filters):
    from frappe.desk.treeview import get_all_nodes as original_get_all_nodes

    tree_method = frappe.override_whitelisted_method(tree_method)

    return original_get_all_nodes(doctype, label, parent, tree_method, **filters)
