# 纯 Python 函数级变异：不碰被审文件。用假 frappe 模拟测试站状态（新 DocType 已存在），
# 复现 test_cash_flow_rename 两个用例在「删第一道守卫」「删第二道守卫」两种变异下是否变红。
from unittest.mock import MagicMock


def make_execute(variant):
    def execute(frappe):
        if variant == "orig":
            cond = not frappe.db.table_exists("Cash Flow") or frappe.db.exists("DocType", "Cash Flow Worksheet")
        elif variant == "no_guard1":
            cond = frappe.db.exists("DocType", "Cash Flow Worksheet")
        elif variant == "no_guard2":
            cond = not frappe.db.table_exists("Cash Flow")
        if cond:
            return
        frappe.rename_doc("DocType", "Cash Flow", "Cash Flow Worksheet", force=True)
    return execute


def site():
    frappe = MagicMock()
    frappe.db.exists.return_value = True  # 测试站：DocType Cash Flow Worksheet 已存在（真实状态，用例未 patch）
    return frappe


for variant in ("orig", "no_guard1", "no_guard2"):
    ex = make_execute(variant)
    # 用例 1：只 patch table_exists=False
    f = site(); f.db.table_exists.return_value = False; ex(f)
    t1 = "GREEN" if not f.rename_doc.called else "RED"
    # 用例 2：table_exists=True、exists=True
    f = site(); f.db.table_exists.return_value = True; f.db.exists.return_value = True; ex(f)
    t2 = "GREEN" if not f.rename_doc.called else "RED"
    print(f"{variant}: test_new_install_without_old_table_returns={t1}  test_already_renamed_site_returns={t2}")
