# 只读：演示站上分别以默认语言（同 bench execute）与 zh 跑 find_problems；最后 rollback，不 commit
import os
os.chdir("/workspace/frappe-bench/sites")
import frappe
frappe.init("erx.localhost"); frappe.connect()
try:
    from frappe_china.translation_check import find_problems
    print("default lang:", frappe.local.lang, "->", find_problems())
    frappe.local.lang = "zh"
    print("zh ->", find_problems())
finally:
    frappe.db.rollback(); frappe.destroy()
