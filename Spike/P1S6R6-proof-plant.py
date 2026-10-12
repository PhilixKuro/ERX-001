"""SL-014 ⑥ 造失败／恢复（容器内 env/bin/python 跑，只用于测试站）。用法：proof-plant.py plant-sidebar|plant-trad|restore（三种失败分开造、分开跑，免得繁体译名挡住首页图标入口）
plant：① 自有侧栏 Business Flow 末尾追加一条英文 label 的 Link 条目（frappe.flags.in_import 置真，免得 developer_mode 下写回 app json，LG-105）；
       ② zh.csv 里 Business Flow 的译文改成繁体「業務流程」（原文件先备份）；clear-cache。
restore：删掉该条目、csv 从备份原样还原，clear-cache；核对 csv 哈希与 plant 前一致。"""
import hashlib, os, shutil, sys
os.chdir("/workspace/frappe-bench/sites")
import frappe
frappe.init(site="test.localhost"); frappe.connect(); frappe.set_user("Administrator")
CSV = "/workspace/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv"
BAK = "/workspace/Spike/P1S6R7/proof-zh.csv.bak"
LABEL = "Zzproof Entry"
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
try:
	action = sys.argv[1]
	doc = frappe.get_doc("Workspace Sidebar", "Business Flow")
	frappe.flags.in_import = True
	if action == "plant-sidebar":
		if not any(i.label == LABEL for i in doc.items):
			doc.append("items", {"type": "Link", "label": LABEL, "link_type": "DocType", "link_to": "Company", "child": 1})
			doc.save(ignore_permissions=True)
	elif action == "plant-trad":
		if not os.path.exists(BAK):
			shutil.copyfile(CSV, BAK)
		text = open(CSV, encoding="utf-8").read()
		assert "\nBusiness Flow,业务流程\n" in text
		open(CSV, "w", encoding="utf-8", newline="").write(text.replace("\nBusiness Flow,业务流程\n", "\nBusiness Flow,業務流程\n"))
	elif action == "restore":
		if any(i.label == LABEL for i in doc.items):
			doc.items = [i for i in doc.items if i.label != LABEL]
			doc.save(ignore_permissions=True)
		if os.path.exists(BAK):
			shutil.copyfile(BAK, CSV); os.remove(BAK)
	else:
		raise ValueError(action)
	frappe.db.commit()
	frappe.clear_cache()
	print({"action": action, "sidebar_has_proof": any(i.label == LABEL for i in frappe.get_doc("Workspace Sidebar", "Business Flow").items), "csv_sha256": sha(CSV)})
finally:
	frappe.flags.in_import = False
	frappe.destroy()
