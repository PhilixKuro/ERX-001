# R13 F p2：在宿主上用桩 frappe 跑 s6_rename_cash_flow_worksheet 的两条守卫与两条用例，
# 对补丁打变异（删守卫 1／删守卫 2／两条都删），看 FD-016 ① 改后的用例是否都能变红。
# 只读仓库内文件，不改任何受管文件。
import re, sys, types
from pathlib import Path

SRC = Path(sys.argv[1]) / "frappe-bench/apps/frappe_china/frappe_china/patches/s6_rename_cash_flow_worksheet.py"
body = SRC.read_text(encoding="utf-8")

GUARD1 = 'not frappe.db.table_exists("Cash Flow")'
GUARD2 = 'frappe.db.exists("DocType", "Cash Flow Worksheet")'


def make_execute(code):
	frappe = types.SimpleNamespace()
	calls = {"rename": 0, "reload": 0}
	state = {}

	frappe.db = types.SimpleNamespace(
		table_exists=lambda *a, **k: state["table_exists"],
		exists=lambda *a, **k: state["exists"],
	)
	frappe.rename_doc = lambda *a, **k: calls.__setitem__("rename", calls["rename"] + 1)
	frappe.reload_doc = lambda *a, **k: calls.__setitem__("reload", calls["reload"] + 1)
	ns = {"frappe": frappe}
	exec(code.replace("import frappe\n", "", 1), ns)
	return ns["execute"], calls, state


def run_cases(code):
	"""返回两条用例的结果：True=通过（rename 未被调用）"""
	results = {}
	for name, te, ex in (("new_install", False, False), ("already_renamed", True, True)):
		execute, calls, state = make_execute(code)
		state["table_exists"] = te
		state["exists"] = ex
		execute()
		results[name] = calls["rename"] == 0
	return results


print("基线", run_cases(body))
for label, mutated in (
	("删守卫1（旧表不存在）", body.replace(GUARD1 + " or ", "")),
	("删守卫2（新表已存在）", body.replace(" or " + GUARD2, "")),
	("两条守卫都删", re.sub(r"\tif .*?:\n\t\treturn\n", "", body.replace("    ", "\t"), count=1)),
):
	assert mutated != body, label
	r = run_cases(mutated)
	red = [k for k, v in r.items() if not v]
	print(f"{'[杀死]' if red else '[存活]'} {label}: {r} 变红的用例={red}")
