# V-01 探针：验证 erpnext/regional/ 的接入点是否全部可被"外部 app + hook"使用
# 运行：docker compose exec -T -w /workspace/frappe-bench frappe \
#         bench --site erx.localhost execute <path>  或用 console 粘贴
# 本脚本只读，不写任何数据。
import inspect

import frappe


def run():
    import inspect, json, os

    import frappe
    out = []

    # ---- 1. regional_overrides：是 hook，多 app 可叠加，末位 app 胜出 ----
    import erpnext
    src = inspect.getsource(erpnext.allow_regional)
    out.append("[1] allow_regional 源码读取 hook：%s" % ("frappe.get_hooks" in src))
    out.append("    overrides 取法：%s" % [l.strip() for l in src.splitlines() if "get_hooks" in l])
    hooks = frappe.get_hooks("regional_overrides", {})
    out.append("    当前站点 regional_overrides 国家键：%s" % sorted(hooks.keys()))
    out.append("    China 键是否存在：%s" % ("China" in hooks))

    # ---- 2. get_region()：由 Company.country 决定，无需改源码 ----
    out.append("[2] get_region() 取值来源：Company.country / System Settings.country")
    out.append("    系统 country=%r" % frappe.get_system_settings("country"))

    # ---- 3. doc_events：是 hook ----
    si_hooks = frappe.get_hooks("doc_events", {}).get("Sales Invoice", {})
    out.append("[3] doc_events['Sales Invoice'] 可叠加，当前 on_submit=%s" % si_hooks.get("on_submit"))

    # ---- 4. install_country_fixtures：硬编码模块路径，非 hook ----
    from erpnext.setup.doctype.company import company as company_mod
    icf = inspect.getsource(company_mod.install_country_fixtures)
    out.append("[4] install_country_fixtures 源码：")
    for l in icf.splitlines():
        out.append("      " + l)
    out.append("    -> 是否走 hook：%s（硬编码 erpnext.regional.<country>.setup.setup）"
               % ("get_hooks" in icf))

    # ---- 5. 但 Company 的 doc_events 可补偿 ----
    co_hooks = frappe.get_hooks("doc_events", {}).get("Company", {})
    out.append("[5] doc_events['Company'] 现有：%s" % co_hooks)
    out.append("    -> 外部 app 可挂 Company.after_insert/on_update 自行做 fixtures")

    # ---- 6. Custom Field / Property Setter / Print Format / Report：都是数据层 ----
    out.append("[6] italy/south_africa/uae setup() 用的 create_custom_fields/add_permission"
               " 全是公开 API，任何 app 可调")

    # ---- 7. country_wise_tax.json：China 已有，但只有 17% 单档 ----
    import json, os
    from erpnext.setup.setup_wizard.operations import taxes_setup
    p = os.path.join(os.path.dirname(taxes_setup.__file__), "..", "data", "country_wise_tax.json")
    d = json.load(open(p, encoding="utf-8"))
    out.append("[7] country_wise_tax.json China=%s" % json.dumps(d.get("China"), ensure_ascii=False))
    src2 = inspect.getsource(taxes_setup.setup_taxes_and_charges)
    out.append("    setup_taxes_and_charges 是否走 hook：%s（读死文件）" % ("get_hooks" in src2))
    out.append("    update_regional_tax_settings 路径：%s"
               % [l.strip() for l in inspect.getsource(taxes_setup.update_regional_tax_settings).splitlines()
                  if "module_name" in l])

    # ---- 8. financial_report_template：按 installed_apps 扫描，app 可投放 ----
    from erpnext.accounts.doctype.financial_report_template import financial_report_template as frt
    s3 = inspect.getsource(frt.sync_financial_report_templates)
    out.append("[8] sync_financial_report_templates 扫 installed_apps：%s"
               % ("get_installed_apps" in s3))
    out.append("    支持 COA 里 disable_default_financial_report_template 关掉 erpnext 自带模板：%s"
               % ("disable_default_financial_report_template" in s3))

    # ---- 9. get_charts_for_country：whitelisted，可被 override_whitelisted_methods 换掉 ----
    from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa
    wl = frappe.whitelisted
    is_wl = coa.get_charts_for_country in wl or getattr(
        coa.get_charts_for_country, "__func__", None) in wl
    out.append("[9] get_charts_for_country 在 frappe.whitelisted 集合中：%s" % bool(is_wl))
    orig = "erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country"
    out.append("    override_whitelisted_method(%s)\n      -> %s"
               % (orig.split(".")[-1], frappe.override_whitelisted_method(orig)))
    out.append("    -> 未装 override 时返回原路径；装了则返回 app 侧路径")

    # ---- 10. 实测：China 下拉里有什么 ----
    out.append("[10] get_charts_for_country('China') = %s" % coa.get_charts_for_country("China"))
    frappe.local.flags.allow_unverified_charts = True
    out.append("     allow_unverified_charts=True 时 = %s" % coa.get_charts_for_country("China"))
    frappe.local.flags.allow_unverified_charts = False

    print("\n".join(out))


run()
