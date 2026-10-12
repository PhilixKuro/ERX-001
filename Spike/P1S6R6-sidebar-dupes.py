"""S6 R6 方案 TS-023 第 6 步（R3 Part4 接口契约签名）：查同一侧栏里有无两个同名的中文分节（AC-002 前半）。只读。

脚本不在 app 里，`bench execute` 取不到，按 Spike 惯例以 env/bin/python 直连（只读，不清缓存）：
    /workspace/frappe-bench/env/bin/python /workspace/Spike/P1S6R6-sidebar-dupes.py <site>
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter


def run(site_lang: str = "zh") -> dict[str, list[str]]:
	"""对站上全部 Workspace Sidebar：按 boot.get_sidebar_items 的同一取法取 Section Break 的 label，
	以 zh 译后分组，返回 {侧栏名: [重名的中文分节]}；空字典即通过。"""
	import frappe
	from frappe import _
	from frappe.desk.doctype.workspace_sidebar.workspace_sidebar import auto_generate_sidebar_from_module

	frappe.local.lang = site_lang
	sidebars = [(row.name, frappe.get_doc("Workspace Sidebar", row.name)) for row in frappe.get_all("Workspace Sidebar", fields=["name"])]
	sidebars += [(doc.title, doc) for doc in auto_generate_sidebar_from_module()]  # boot.py:449 同取
	result = {}
	for title, doc in sidebars:
		labels = Counter(_(item.label) for item in doc.items if item.type == "Section Break" and item.label)
		dupes = sorted(label for label, count in labels.items() if count > 1)
		if dupes:
			result[title] = dupes
	return result


def main() -> None:
	import frappe

	site = sys.argv[1]
	os.chdir("/workspace/frappe-bench/sites")
	frappe.init(site=site, sites_path=".")
	frappe.connect()
	try:
		result = run()
		print(json.dumps({"site": site, "dupes": result, "pass": result == {}}, ensure_ascii=False, indent=1))
	finally:
		frappe.db.rollback()
		frappe.destroy()


if __name__ == "__main__":
	main()
