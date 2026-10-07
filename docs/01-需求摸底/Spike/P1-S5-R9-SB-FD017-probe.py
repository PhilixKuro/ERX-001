"""FD-017 复验：站上有写类工具、CRM 设置有待改字段时，报错退出前不得写任何东西。只在测试站跑。

用法（容器内，工作目录 sites/）：python P1-S5-R9-SB-FD017-probe.py <被测脚本路径>
setup 与 teardown 各自提交；被测脚本的 main() 期间记录 Document.save 与 sql_ddl 调用。
"""
import importlib.util
import sys

import frappe
from frappe.model.document import Document

SITE = "test.localhost"
TOOL = "_fct_probe_delete"


def connect():
	frappe.init(site=SITE, sites_path=".")
	frappe.connect()
	frappe.set_user("Administrator")


def setup():
	connect()
	try:
		frappe.get_doc(
			{
				"doctype": "Raven AI Function",
				"function_name": TOOL,
				"type": "Delete Document",
				"reference_doctype": "ToDo",
				"description": "probe",
			}
		).insert(ignore_permissions=True)
		before = frappe.db.get_single_value("ERPNext CRM Settings", "sync_products")
		frappe.db.set_single_value("ERPNext CRM Settings", "sync_products", 0)
		frappe.db.commit()
		print(f"setup: 建写类工具 {TOOL}；sync_products {before} → 0")
	finally:
		frappe.destroy()


def teardown():
	connect()
	try:
		sync = frappe.db.get_single_value("ERPNext CRM Settings", "sync_products")
		print(f"after main: sync_products = {sync}")
		frappe.delete_doc("Raven AI Function", TOOL, ignore_permissions=True)
		frappe.db.set_single_value("ERPNext CRM Settings", "sync_products", 1)
		frappe.db.commit()
		print("teardown: 删写类工具；sync_products 恢复 1")
		return sync
	finally:
		frappe.destroy()


def run(path):
	spec = importlib.util.spec_from_file_location("configure_under_test", path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	saves, ddls = [], []
	orig_save = Document.save

	def save(self, *args, **kwargs):
		saves.append(f"{self.doctype}:{self.name}")
		return orig_save(self, *args, **kwargs)

	Document.save = save
	try:
		import frappe.database.database as dbmod

		orig_ddl = dbmod.Database.sql_ddl

		def sql_ddl(self, query, *args, **kwargs):
			ddls.append(query[:60])
			return orig_ddl(self, query, *args, **kwargs)

		dbmod.Database.sql_ddl = sql_ddl
		try:
			rc = module.main(["--site", SITE])
		finally:
			dbmod.Database.sql_ddl = orig_ddl
	finally:
		Document.save = orig_save
	print(f"main rc = {rc}")
	print(f"Document.save 调用 {len(saves)} 次：{saves}")
	print(f"sql_ddl 调用 {len(ddls)} 次")
	return rc, saves


if __name__ == "__main__":
	setup()
	try:
		rc, saves = run(sys.argv[1])
	finally:
		sync = teardown()
	verdict = rc == 1 and not saves and sync == 0
	print("判定：", "通过（报错前零写入）" if verdict else "不通过")
