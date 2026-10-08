"""配置 CRM 集成与 Raven（连接、演示 bot 与只读工具）（P1-S5 开发方案 Part3 TS-009）。

容器内运行，由宿主侧 docker/configure-apps.sh 调用：

    cd /workspace/frappe-bench/sites && /workspace/frappe-bench/env/bin/python /workspace/docker/scripts/configure_apps.py --site <站点> [--company <公司>]

可重复跑：已是目标值的字段不写；整次运行没有改动时只输出「无改动」。
本脚本自己会报错退出的检查都在写任何东西之前做完（preflight）：CRM 段建自定义字段走 DDL、
会隐式提交，之后再报错 rollback 撤不回它（P1-S5-R9 F 审核 FD-017）。已知会拒绝保存的上游校验
也在这里预先查（Raven 推送配置，P1-S5-R10 FD-037）；其余上游 validate 仍可能在写入之后抛错，
那时以 traceback 退出、退出码非 0（FD-045）。
某个 App 没装（对应 DocType 不存在）时跳过该段并打一行说明。
密钥只报「已改／未改」，不出现在任何输出里。
"""

import argparse
import os
import sys

import frappe


BOT_NAME = "ERX 分析助手"
BOT_INSTRUCTION = (
	"你是华东弹簧有限公司的经营分析助手，只读，不修改任何数据。回答任何问题前，先用工具取数，不凭记忆回答。"
	"只统计已提交的单据（docstatus = 1），草稿与已取消的单据不算。回答的最后一段列出你用到的单据号或报表名。"
	"金额保留两位小数，百分比保留一位小数。用中文回答。"
)

# 15 条只读工具，顺序即写进 bot 的顺序（开发方案 TS-009 表）。
# run_report 用 Raven 原生的 Get Report Result 类型，不再指向自写包装（R5 E 确认 IT-014，用户裁决）。
TOOLS = (
	(
		"list_crm_deals",
		"Get List",
		"CRM Deal",
		"列商机（CRM Deal）。常用字段：name、organization、expected_deal_value（预计金额）、probability（成交概率，%）、"
		"expected_closure_date、status、currency。商机不是可提交单据，没有草稿／已提交之分，不要按 docstatus 筛。",
	),
	("get_crm_deal", "Get Document", "CRM Deal", "按商机号取一张商机全文，含产品明细与联系人。"),
	(
		"list_crm_deal_statuses",
		"Get List",
		"CRM Deal Status",
		"列商机状态。常用字段：name、type（Open／Ongoing／On Hold／Won／Lost）、probability、position。判断商机是否已赢单或丢单时用。",
	),
	(
		"list_purchase_receipts",
		"Get List",
		"Purchase Receipt",
		"列采购入库单。常用字段：name、supplier、posting_date、docstatus。明细（收货数、拒收数、单价）不在这里，用 get_purchase_receipt 逐张取。",
	),
	(
		"get_purchase_receipt",
		"Get Document",
		"Purchase Receipt",
		"按单号取一张采购入库单全文，明细行含 item_code、received_qty（收货数）、rejected_qty（拒收数）、qty（合格数）、rate（单价）。",
	),
	("list_suppliers", "Get List", "Supplier", "列供应商。常用字段：name、supplier_name、supplier_group、disabled。"),
	("list_items", "Get List", "Item", "列物料。常用字段：name、item_name、item_group、stock_uom、disabled。"),
	("get_item", "Get Document", "Item", "按物料编码取一个物料全文。"),
	(
		"list_sales_orders",
		"Get List",
		"Sales Order",
		"列销售订单。常用字段：name、customer、transaction_date、grand_total、docstatus。明细单价用 get_sales_order 取。",
	),
	("get_sales_order", "Get Document", "Sales Order", "按单号取一张销售订单全文，明细行含 item_code、qty、rate（单价）。"),
	(
		"list_boms",
		"Get List",
		"BOM",
		"列物料清单（BOM）。常用字段：name、item、is_active、is_default、total_cost（总成本）、quantity（基准数量）、docstatus。"
		"单位成本 = total_cost ÷ quantity。",
	),
	("get_bom", "Get Document", "BOM", "按 BOM 号取一张物料清单全文，含原料明细与成本。"),
	("list_customers", "Get List", "Customer", "列客户。常用字段：name、customer_name、customer_group、territory。"),
	("get_supplier", "Get Document", "Supplier", "按供应商名取一个供应商全文。"),
	(
		"run_report",
		"Get Report Result",
		None,
		"运行一张只读报表，返回列与行。report_name 照写下列英文名，filters 按该报表的过滤键传："
		"Item-wise Purchase History（按物料的采购历史；company、from_date、to_date、item_code、supplier）、"
		"Purchase Analytics（采购分析；company、from_date、to_date、tree_type、range）、"
		"Purchase Receipt Trends（采购入库趋势；company、fiscal_year、period、based_on）、"
		"Supplier Quotation Comparison（供应商报价比较；company、from_date、to_date、item_code）、"
		"BOM Explorer（BOM 展开；bom）、"
		"BOM Stock Analysis（BOM 齐套分析；bom、warehouse、qty_to_make）。",
	),
)

# Raven AI Function 里会写数据的类型（raven_ai_function.py 的 WRITE_PERMISSIONS 加提交、取消两类）
WRITE_TYPES = (
	"Create Document",
	"Create Multiple Documents",
	"Update Document",
	"Update Multiple Documents",
	"Delete Document",
	"Delete Multiple Documents",
	"Submit Document",
	"Cancel Document",
	"Send Message",
	"Attach File to Document",
	"Set Value",
)


class ConfigureError(Exception):
	pass


def _norm(value) -> str:
	return "" if value is None else str(value)


def _apply(doc, values: dict) -> dict:
	"""只改与目标值不同的字段，返回 {字段: (旧值, 新值)}。"""
	changes = {}
	for field, value in values.items():
		current = doc.get(field)
		if _norm(current) != _norm(value):
			changes[field] = (current, value)
			doc.set(field, value)
	return changes


def _has(doctype: str) -> bool:
	return bool(frappe.db.exists("DocType", doctype))


def resolve_company(explicit: str | None) -> str:
	from frappe_china.accounting.chart import CN_CHART_NAME

	if explicit:
		if not frappe.db.exists("Company", explicit):
			raise ConfigureError(f"公司 {explicit} 不存在")
		return explicit
	companies = frappe.get_all("Company", filters={"chart_of_accounts": CN_CHART_NAME}, pluck="name")
	if len(companies) != 1:
		raise ConfigureError(
			f"按科目表「{CN_CHART_NAME}」找到 {len(companies)} 家公司（{', '.join(companies) or '无'}），请用 --company 指定"
		)
	return companies[0]


def configure_crm(company: str | None, notes: list[str]) -> dict:
	changes = {}
	if not _has("FCRM Settings") or not _has("ERPNext CRM Settings"):
		notes.append("CRM 未安装，跳过 CRM 设置")
		return changes

	settings = frappe.get_single("FCRM Settings")
	# currency 设一次后被 CRM 设成只读（fcrm_settings.py make_currency_read_only），已是 CNY 则不写
	changed = _apply(settings, {"currency": "CNY"})
	if changed:
		settings.save(ignore_permissions=True)
		changes["FCRM Settings"] = changed

	settings = frappe.get_single("ERPNext CRM Settings")
	changed = _apply(
		settings,
		{
			"enabled": 1,
			"is_erpnext_in_different_site": 0,
			"sync_products": 1,
			"create_customer_on_status_change": 0,
			"erpnext_company": company,
		},
	)
	if changed:
		# validate 里建跨 app 的自定义字段与报价单预填脚本
		settings.save(ignore_permissions=True)
		changes["ERPNext CRM Settings"] = changed

	# 同站点集成下 CRM 建客户走 erpnext.crm.frappe_crm_api.create_customer，
	# 它先查 CRM Settings 这个开关，不开就报错（frappe_crm_api.py validate_frappe_crm_sync）
	if _has("CRM Settings") and frappe.get_meta("CRM Settings").has_field("enable_frappe_crm_data_synchronization"):
		settings = frappe.get_single("CRM Settings")
		changed = _apply(settings, {"enable_frappe_crm_data_synchronization": 1})
		if changed:
			settings.save(ignore_permissions=True)
			changes["CRM Settings"] = changed
	return changes


def configure_raven(url: str, key: str, notes: list[str]) -> dict:
	changes = {}
	if not _has("Raven Settings"):
		notes.append("Raven 未安装，跳过 Raven 设置")
		return changes
	if not (url or key):
		notes.append("RAVEN_LLM_URL／RAVEN_LLM_KEY 未设，跳过 Raven Settings 的连接字段（见延迟需求 SH-P1S5006）")
		return changes
	# 只设一个的情形已由 preflight 拦下

	settings = frappe.get_single("Raven Settings")
	changed = _apply(
		settings,
		{
			"enable_ai_integration": 1,
			"enable_local_llm": 1,
			"local_llm_provider": "OpenAI Compatible",
			"local_llm_api_url": url,
		},
	)
	current_key = settings.get_password("openai_compatible_api_key", raise_exception=False) if settings.get("openai_compatible_api_key") else None
	if current_key != key:
		settings.openai_compatible_api_key = key
		changed["openai_compatible_api_key"] = ("（密钥）", "（密钥，已改）")
	if changed:
		settings.save(ignore_permissions=True)
		changes["Raven Settings"] = changed
	return changes


def ensure_bot_and_functions(model: str, notes: list[str]) -> dict:
	changes = {}
	if not _has("Raven AI Function") or not _has("Raven Bot"):
		notes.append("Raven 未安装，跳过演示 bot 与只读工具")
		return changes

	names = []
	for name, kind, reference_doctype, description in TOOLS:
		exists = frappe.db.exists("Raven AI Function", name)
		doc = frappe.get_doc("Raven AI Function", name) if exists else frappe.new_doc("Raven AI Function")
		# params 由 Raven 按类型生成（raven_ai_function.py prepare_function_params），不由本脚本写
		changed = _apply(
			doc,
			{
				"function_name": name,
				"type": kind,
				"reference_doctype": reference_doctype,
				"function_path": None,
				"pass_parameters_as_json": 0,
				"description": description,
				"strict": 0,
			},
		)
		if changed:
			doc.save(ignore_permissions=True)
			changes[f"Raven AI Function {name}"] = changed
		names.append(name)

	exists = frappe.db.exists("Raven Bot", BOT_NAME)
	bot = frappe.get_doc("Raven Bot", BOT_NAME) if exists else frappe.new_doc("Raven Bot")
	values = {
		"bot_name": BOT_NAME,
		"is_ai_bot": 1,
		"model_provider": "Local LLM",
		"instruction": BOT_INSTRUCTION,
		"allow_bot_to_write_documents": 0,
		"enable_code_interpreter": 0,
		"enable_file_search": 0,
		# 让报错回复带原因，便于实测；演示前由 S7 关掉
		"debug_mode": 1,
	}
	if model:
		values["model"] = model
	else:
		# Raven 的 model 字段带缺省值 gpt-4o（raven_bot.json），新建时由框架填上（R8 E 确认 IT-029）
		notes.append("RAVEN_LLM_MODEL 未设，bot 的 model 不改（新建时取 Raven 缺省 gpt-4o；接 LiteLLM 时须同时设 RAVEN_LLM_MODEL）")
	changed = _apply(bot, values)
	if [row.function for row in bot.get("bot_functions") or []] != names:
		changed["bot_functions"] = ("…", f"{len(names)} 条只读工具")
		bot.set("bot_functions", [{"function": name} for name in names])
	if changed:
		bot.save(ignore_permissions=True)
		changes[f"Raven Bot {BOT_NAME}"] = changed
	return changes


def preflight(company_arg: str | None, url: str, key: str) -> str | None:
	"""只读：本脚本自己的检查与已知会拒绝保存的上游校验，都在写之前做完；返回 CRM 要用的公司（CRM 没装时为 None）。"""
	company = None
	if _has("FCRM Settings") and _has("ERPNext CRM Settings"):
		company = resolve_company(company_arg)
	if _has("Raven Settings") and (url or key) and not (url and key):
		raise ConfigureError("RAVEN_LLM_URL 与 RAVEN_LLM_KEY 须同时设置")
	if _has("Raven Settings") and url and key:
		# 上游 RavenSettings.validate：推送服务为 Raven（缺省值）时三项推送配置缺一即拒绝保存。
		# 那一步排在 CRM 段写入之后，故在这里先拦（P1-S5-R10 F 复核 FD-037）
		push = {
			field: frappe.db.get_single_value("Raven Settings", field)
			for field in (
				"push_notification_service",
				"push_notification_server_url",
				"push_notification_api_key",
				"push_notification_api_secret",
			)
		}
		if push["push_notification_service"] in (None, "", "Raven") and not all(
			push[field]
			for field in ("push_notification_server_url", "push_notification_api_key", "push_notification_api_secret")
		):
			raise ConfigureError(
				"Raven Settings 的推送服务是 Raven，但推送服务器地址、API Key、API Secret 没填齐，"
				"Raven 会拒绝保存连接字段；先在 Raven Settings 把推送服务改为 Frappe Cloud 或填齐这三项，"
				"再跑本脚本（见延迟需求 SH-P1S5006 ⑦）"
			)
	if _has("Raven AI Function"):
		tool_names = {name for name, *_rest in TOOLS}
		unexpected = sorted(
			set(frappe.get_all("Raven AI Function", filters={"type": ("in", WRITE_TYPES)}, pluck="name")) - tool_names
		)
		if unexpected:
			# 不删别人的记录，交用户处理
			raise ConfigureError("站上已有写数据类的 Raven AI Function：" + "、".join(unexpected) + "；请先处理再跑本脚本")
	return company


def _short(value) -> str:
	text = _norm(value)
	return text if len(text) <= 40 else text[:40] + "…"


def _print_changes(changes: dict) -> None:
	for target, fields in changes.items():
		for field, (old, new) in fields.items():
			print(f"改动 {target}.{field}：{_short(old)!r} → {_short(new)!r}")


def main(argv=None) -> int:
	parser = argparse.ArgumentParser(description="配置 CRM 集成与 Raven")
	parser.add_argument("--site", required=True)
	parser.add_argument("--company", default=None, help="CRM 生成报价单用的公司；缺省取站上唯一一家中式公司")
	args = parser.parse_args(argv)

	# 工作目录须是 sites/：框架日志写 ../logs（frappe/utils/logger.py），同 seed-demo.sh 的跑法
	frappe.init(site=args.site, sites_path=".")
	frappe.connect()
	try:
		url = os.environ.get("RAVEN_LLM_URL", "")
		key = os.environ.get("RAVEN_LLM_KEY", "")
		company = preflight(args.company, url, key)
		notes: list[str] = []
		changes = {}
		changes.update(configure_crm(company, notes))
		changes.update(configure_raven(url, key, notes))
		changes.update(ensure_bot_and_functions(os.environ.get("RAVEN_LLM_MODEL", ""), notes))
		for note in notes:
			print(f"说明：{note}")
		if changes:
			frappe.db.commit()
			frappe.clear_cache()
			_print_changes(changes)
		else:
			print("无改动")
		return 0
	except ConfigureError as error:
		frappe.db.rollback()
		print(f"configure-apps：{error}", file=sys.stderr)
		return 1
	finally:
		frappe.destroy()


if __name__ == "__main__":
	sys.exit(main())
