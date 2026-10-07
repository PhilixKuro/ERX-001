"""FD-037 复验：推送服务为 Raven、推送配置为空时，设了 URL/KEY 应在写任何东西之前报错。只在测试站跑。"""
import importlib.util, os, sys
import frappe
from frappe.model.document import Document

SITE = "test.localhost"

def connect():
	frappe.init(site=SITE, sites_path=".")
	frappe.connect()
	frappe.set_user("Administrator")

connect()
try:
	before = frappe.db.get_single_value("ERPNext CRM Settings", "sync_products")
	frappe.db.set_single_value("ERPNext CRM Settings", "sync_products", 0)
	frappe.db.commit()
	print(f"setup: sync_products {before} -> 0（让 CRM 段有待写字段）")
finally:
	frappe.destroy()

spec = importlib.util.spec_from_file_location("cfg", os.environ.get("CFG", "/workspace/docker/scripts/configure_apps.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
saves = []
orig = Document.save
def save(self, *a, **k):
	saves.append(f"{self.doctype}:{self.name}")
	return orig(self, *a, **k)
Document.save = save
os.environ["RAVEN_LLM_URL"] = "http://example.invalid/v1"
os.environ["RAVEN_LLM_KEY"] = "dummy"
try:
	rc = mod.main(["--site", SITE])
finally:
	Document.save = orig
print(f"main rc = {rc}; Document.save {len(saves)} 次 {saves}")

connect()
try:
	after = frappe.db.get_single_value("ERPNext CRM Settings", "sync_products")
	llm = frappe.db.get_single_value("Raven Settings", "enable_local_llm")
	frappe.db.set_single_value("ERPNext CRM Settings", "sync_products", 1)
	frappe.db.commit()
	print(f"after main: sync_products={after}, Raven enable_local_llm={llm}; teardown: sync_products -> 1")
finally:
	frappe.destroy()
print("判定：", "通过（报错前零写入）" if rc == 1 and not saves and after == 0 and not llm else "不通过")
