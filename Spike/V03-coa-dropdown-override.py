# V-03 探针：自有 app 能否让自制科目表出现在建公司时的科目表下拉里。
# 建公司表单的下拉来自 frappe.call("...get_charts_for_country")（company.js:264）。
# 该调用经 handler.execute_cmd -> frappe.override_whitelisted_method 解析（handler.py:66），
# 所以 app 用 override_whitelisted_methods 就能换掉它，无需改 erpnext 源码。
# 只读 + 内存内改 hooks 缓存。

import frappe


def run():
    import os
    import sys
    import textwrap

    from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa

    out = []
    orig = ("erpnext.accounts.doctype.account.chart_of_accounts"
            ".chart_of_accounts.get_charts_for_country")

    # ---- 1. 原生下拉内容 ----
    out.append("[1] 原生 get_charts_for_country('China') = %s" % coa.get_charts_for_country("China"))
    out.append("    -> cn_l10n_chart_china.json 在 unverified/，默认扫不到")

    # ---- 2. 解析路径：未装 override 时 ----
    out.append("[2] override_whitelisted_method() 未装 app 时 -> %s"
               % frappe.override_whitelisted_method(orig))

    # ---- 3. 造一个"外部 app 的 override 函数" ----
    tmpdir = "/tmp/erx_cn_spike_mod"
    os.makedirs(tmpdir, exist_ok=True)
    with open(os.path.join(tmpdir, "cn_coa_probe.py"), "w") as f:
        f.write(textwrap.dedent('''
            import frappe

            @frappe.whitelist()
            def get_charts_for_country(country, with_standard=False):
                from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import (
                    get_charts_for_country as original,
                )
                charts = list(original(country, with_standard=with_standard))
                if country == "China":
                    charts = ["ERX 中国科目表（自有 app 提供）"] + charts
                return charts
        '''))
    if tmpdir not in sys.path:
        sys.path.insert(0, tmpdir)
    import cn_coa_probe

    # ---- 4. 注入 override_whitelisted_methods ----
    hooks = frappe.get_hooks()
    hooks.setdefault("override_whitelisted_methods", {})
    hooks["override_whitelisted_methods"][orig] = ["cn_coa_probe.get_charts_for_country"]
    frappe.local.cache["hooks"] = hooks

    resolved = frappe.override_whitelisted_method(orig)
    out.append("[3] 注入 app 的 override 后 -> %s" % resolved)
    out.append("    解析到 app 侧：%s" % (resolved == "cn_coa_probe.get_charts_for_country"))

    # ---- 5. 走 app 侧函数实际取下拉 ----
    out.append("[4] app 侧 get_charts_for_country('China') = %s"
               % cn_coa_probe.get_charts_for_country("China"))

    # ---- 6. 另一条路：不覆盖方法，只投放 verified/ 同级的 app 目录？测一下扫描范围 ----
    import inspect
    src = inspect.getsource(coa.get_charts_for_country)
    out.append("[5] get_charts_for_country 扫描目录写法：")
    for l in src.splitlines():
        if "path" in l or "folder" in l or "listdir" in l:
            out.append("      " + l.strip())
    out.append("    -> 目录固定为 os.path.dirname(__file__) 下的 verified/unverified，")
    out.append("       不扫 installed_apps，故「把 json 放自己 app 里」这条路走不通；")
    out.append("       可行路径是覆盖 whitelisted 方法（上面第 3-4 步已实测）。")

    # ---- 7. 还有一条：allow_unverified_charts 标志 ----
    frappe.local.flags.allow_unverified_charts = True
    out.append("[6] allow_unverified_charts=True 时原生返回 = %s"
               % coa.get_charts_for_country("China"))
    frappe.local.flags.allow_unverified_charts = False
    out.append("    -> 该 flag 是 frappe.local.flags，app 可在自己的 override/hook 里置位")

    # ---- 8. 建公司真正取 tree 的函数是 get_chart()，也要能拿到自制模板 ----
    out.append("[7] Company.create_default_accounts 用 get_chart(chart_name)：")
    src2 = inspect.getsource(coa.get_chart)
    out.append("      扫描目录同样固定：%s"
               % [l.strip() for l in src2.splitlines() if "folder" in l or "dirname" in l])
    out.append("    -> 下拉能塞进去，但选中后 get_chart() 仍需能返回 tree；")
    out.append("       get_chart 未走 hook，app 若要提供自有 json 需连同 get_chart 一起覆盖，")
    out.append("       或改用 Chart of Accounts Importer / 建公司后用 fixtures 建科目。")

    frappe.local.cache.pop("hooks", None)
    out.append("[8] 已清 hooks 内存缓存")

    print("\n".join(out))


run()
