"""FD-037 复验：推送服务为 Raven、推送配置为空时，设了 URL/KEY 应在写任何东西之前报错。只在测试站跑。

前提：测试站 Raven Settings 的推送服务是 Raven、推送服务器地址／API Key／API Secret 都为空。
推送状态改变后（如按 SH-P1S5006 ⑦ 改成 Frappe Cloud）此探针失效：预检会放行，main 会把假连接写进站点，
故开头核前提，不满足即拒跑（P1-S5-R11 FD-055）。
"""
import importlib.util, os, sys
import frappe
from frappe.model.document import Document

SITE = "test.localhost"
PUSH_FIELDS = ("push_notification_server_url", "push_notification_api_key", "push_notification_api_secret")

def connect():
	frappe.init(site=SITE, sites_path=".")
	frappe.connect()
	frappe.set_user("Administrator")

connect()
try:
	service = frappe.db.get_single_value("Raven Settings", "push_notification_service")
	filled = [f for f in PUSH_FIELDS if frappe.db.get_single_value("Raven Settings", f)]
	if service != "Raven" or filled:
		print(f"拒跑：推送服务为 {service!r}、已填 {filled}，与本探针前提不符（见文件头）")
		sys.exit(2)
	before = frappe.db.get_single_value("ERPNext CRM Settings", "sync_products")
	frappe.db.set_single_value("ERPNext CRM Settings", "sync_products", 0)
	frappe.db.commit()
	print(f"setup: sync_products {before} -> 0（让 CRM 段有待写字段）")
finally:
	frappe.destroy()

spec = importlib.util.spec_from_file_location("cfg", os.environ.get("CFG", "/workspace/docker/scripts/configure_apps.py"))
saves = []
orig = Document.save
def save(self, *a, **k):
	saves.append(f"{self.doctype}:{self.name}")
	return orig(self, *a, **k)
os.environ["RAVEN_LLM_URL"] = "http://example.invalid/v1"
os.environ["RAVEN_LLM_KEY"] = "dummy"
rc, raised = None, None
try:
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)
	Document.save = save
	rc = mod.main(["--site", SITE])
except Exception as error:  # 改前形态：上游 ValidationError 在写 CRM 段之后抛出
	raised = f"{type(error).__name__}: {error}"
finally:
	Document.save = orig
	print(f"main rc = {rc}; 抛出 {raised}; Document.save {len(saves)} 次 {saves}")
	connect()
	try:
		after = frappe.db.get_single_value("ERPNext CRM Settings", "sync_products")
		llm = frappe.db.get_single_value("Raven Settings", "enable_local_llm")
		frappe.db.set_single_value("ERPNext CRM Settings", "sync_products", 1)
		frappe.db.commit()
		print(f"after main: sync_products={after}, Raven enable_local_llm={llm}; teardown: sync_products -> 1")
	finally:
		frappe.destroy()
print("判定：", "通过（报错前零写入）" if rc == 1 and not raised and not saves and after == 0 and not llm else "不通过")
