# 只读探针：模拟 bench execute 的 init+connect，看 local.lang 与法定列头检查查的是哪本字典；不 commit
import os, sys
from unittest.mock import patch
os.chdir("/workspace/frappe-bench/sites")
import frappe
frappe.init("erx.localhost"); frappe.connect()
try:
    from frappe import _
    from frappe_china.accounting.statements import labels
    print("local.lang after init+connect:", frappe.local.lang)
    print("_('Account') =", _("Account"), "| _('Cash Flow Worksheet') =", _("Cash Flow Worksheet"))
    import frappe.translate as T
    real = T.get_all_translations
    def fake(lang):
        d = dict(real(lang))
        if lang == "zh":
            d["资产"] = "Assets"   # 内存注入：仅 zh 字典里法定列头被译
        return d
    with patch("frappe.translate.get_all_translations", side_effect=fake):
        print("default lang ->", labels.validate_legal_labels())
        frappe.local.lang = "zh"
        print("lang=zh      ->", labels.validate_legal_labels())
    print("Translation rows by lang:", frappe.db.sql("select language,count(*) from tabTranslation group by language"))
finally:
    frappe.db.rollback(); frappe.destroy()
