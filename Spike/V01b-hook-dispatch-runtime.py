# V-01 补充探针：验证 allow_regional 的**运行时分派**真会走到外部 app 的函数。
# 做法：把"某 app 声明了 China 的 regional_overrides"注入 frappe hooks 缓存，
#      被覆盖函数放在 /tmp 下的临时模块里（模拟外部 app，不碰 apps/）。
# 只读 + 内存内改 hooks 缓存，不落库、不改 apps/ 下任何文件。
#
# 注意：不要 import erpnext.tests.* —— 那会触发 ERPNext 测试数据 bootstrap 并写库。

import frappe


def run():
    import os
    import sys
    import textwrap

    import erpnext
    from erpnext.controllers import taxes_and_totals as tt

    out = []

    # ---- 造一个"外部 app 模块"，落 /tmp，不进 apps/ ----
    tmpdir = "/tmp/erx_cn_spike_mod"
    os.makedirs(tmpdir, exist_ok=True)
    with open(os.path.join(tmpdir, "cn_l10n_probe.py"), "w") as f:
        f.write(textwrap.dedent('''
            HITS = []

            def cn_update_itemised_tax_data(doc):
                HITS.append(("first", getattr(doc, "doctype", None)))
                return "CN-OVERRIDE-RAN"

            def cn_second_app(doc):
                HITS.append(("second", getattr(doc, "doctype", None)))
                return "SECOND-APP-WON"
        '''))
    if tmpdir not in sys.path:
        sys.path.insert(0, tmpdir)
    import cn_l10n_probe

    target = "erpnext.controllers.taxes_and_totals.update_itemised_tax_data"
    p1 = "cn_l10n_probe.cn_update_itemised_tax_data"
    p2 = "cn_l10n_probe.cn_second_app"

    frappe.flags.country = "China"
    frappe.local.flags.company = None
    doc = frappe._dict({"doctype": "Sales Invoice"})

    # frappe.get_attr 会拦"模块所属 app 未安装"（frappe/__init__.py:1129-1133）。
    # 真实场景里 app 是装上的，这里置 in_install 绕过该门禁，只测分派链路本身。
    # 这条门禁本身也是 V-01 的结论之一：覆盖函数必须住在一个真装上的 app 里。
    frappe.local.flags.in_install = True

    out.append("get_region() = %r" % erpnext.get_region())

    # ---- A. 覆盖前：跑 erpnext 原函数 ----
    out.append("[A] 覆盖前 regional_overrides.China = %r"
               % frappe.get_hooks("regional_overrides", {}).get("China"))
    r0 = tt.update_itemised_tax_data(doc)
    out.append("    update_itemised_tax_data() -> %r ; app 侧命中=%s" % (r0, cn_l10n_probe.HITS))

    # ---- B. 注入"装了一个声明 China 覆盖的 app" ----
    hooks = frappe.get_hooks()
    hooks.setdefault("regional_overrides", {})
    hooks["regional_overrides"]["China"] = {target: [p1]}
    frappe.local.cache["hooks"] = hooks
    out.append("[B] 注入后 regional_overrides.China = %r"
               % frappe.get_hooks("regional_overrides", {}).get("China"))
    cn_l10n_probe.HITS.clear()
    r1 = tt.update_itemised_tax_data(doc)
    out.append("    update_itemised_tax_data() -> %r ; app 侧命中=%s"
               % (r1, cn_l10n_probe.HITS))

    # ---- C. 两个 app 都声明同一 target：allow_regional 取 [-1] ----
    hooks["regional_overrides"]["China"] = {target: [p1, p2]}
    frappe.local.cache["hooks"] = hooks
    cn_l10n_probe.HITS.clear()
    r2 = tt.update_itemised_tax_data(doc)
    out.append("[C] 两 app 同 target -> %r ; 命中=%s（末位胜出）" % (r2, cn_l10n_probe.HITS))

    # ---- D. 换国家：覆盖按 get_region() 隔离 ----
    frappe.flags.country = "Italy"
    cn_l10n_probe.HITS.clear()
    r3 = tt.update_itemised_tax_data(doc)
    out.append("[D] get_region()=Italy -> %r ; 命中=%s（China 覆盖不生效）"
               % (r3, cn_l10n_probe.HITS))
    frappe.flags.country = "China"

    # ---- E. 另一个 target：GL 分录级覆盖也走同一机制 ----
    from erpnext.accounts.doctype.sales_invoice import sales_invoice as si_mod
    with open(os.path.join(tmpdir, "cn_gl_probe.py"), "w") as f:
        f.write("def make_regional_gl_entries(gl_entries, doc):\n"
                "    return ['CN-GL-HOOKED'] + list(gl_entries or [])\n")
    import cn_gl_probe  # noqa
    t2 = ("erpnext.accounts.doctype.sales_invoice.sales_invoice"
          ".make_regional_gl_entries")
    hooks["regional_overrides"]["China"] = {t2: ["cn_gl_probe.make_regional_gl_entries"]}
    frappe.local.cache["hooks"] = hooks
    r4 = si_mod.make_regional_gl_entries([], frappe._dict({"doctype": "Sales Invoice"}))
    out.append("[E] sales_invoice.make_regional_gl_entries 覆盖后 -> %r" % r4)

    # ---- F. 清理内存缓存 ----
    frappe.local.cache.pop("hooks", None)
    frappe.flags.country = None
    frappe.local.flags.in_install = False
    out.append("[F] 已清 hooks 内存缓存；本探针未写库、未改 apps/")

    print("\n".join(out))


run()
