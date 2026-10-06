"""P1-S5-R5 SB IT-017：CRM 链路脚本化验证（代替 R3 Part3 TS-010 的 /crm 界面实点，用户裁决）。

按 TS-010 第 1～8 步，调用界面背后的同一批服务端方法：
  /crm 转商机        → crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal
  Deal 页生成报价单  → erpnext_crm_settings.get_quotation_url（返回预填参数）＋ prefill_quotation_items（报价单表单预填脚本调用）
  报价单创建销售订单 → erpnext.selling.doctype.quotation.quotation.make_sales_order
  看板               → crm.api.dashboard.get_forecasted_revenue／get_funnel_conversion
逐步打印关键值，最后清理并按 _FCT 前缀查残留。

容器内运行（工作目录 sites/）：
    /workspace/frappe-bench/env/bin/python <本文件> --site test.localhost
"""

import argparse
import sys
from urllib.parse import parse_qsl, urlparse

import frappe
from frappe.utils import add_days, flt, get_last_day, getdate, nowdate

ITEM = "_FCT CRM 演示簧"
ORG = "_FCT 客户 CRM"
FIRST_NAME = "_FCT 联系人"
CRM = "crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings"

failures = []
created = {}


def check(label, actual, expected):
	ok = actual == expected
	print(f"[{'通过' if ok else '失败'}] {label}：实得 {actual!r}，应为 {expected!r}")
	if not ok:
		failures.append(label)


def step(title):
	print(f"\n== {title} ==")


def run():
	settings = frappe.get_single("ERPNext CRM Settings")
	company = settings.erpnext_company
	step("前置")
	print(f"erpnext_company={company!r} enabled={settings.enabled} sync_products={settings.sync_products}")
	print(f"全局默认币种={frappe.db.get_default('currency')!r}；FCRM Settings.currency={frappe.db.get_single_value('FCRM Settings', 'currency')!r}")

	step("1 建临时物料与标准售价，核产品同步")
	item = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": ITEM,
			"item_name": ITEM,
			"item_group": "Products",
			"stock_uom": "支",
			"is_stock_item": 1,
		}
	).insert()
	created["Item"] = item.name
	price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
	price = frappe.get_doc(
		{"doctype": "Item Price", "item_code": ITEM, "price_list": price_list, "price_list_rate": 2.5}
	).insert()
	created["Item Price"] = price.name
	item.reload()
	item.save()  # 触发 on_update，把售价同步进 CRM Product
	product = frappe.db.get_value("CRM Product", {"erpnext_item_code": ITEM}, ["name", "standard_rate"], as_dict=True)
	print(f"价目表={price_list!r}；CRM Product={product}")
	check("CRM Product 已由同步建出", bool(product), True)
	created["CRM Product"] = product.name if product else None

	step("2 建 Lead → 转 Deal，填金额、概率、预计成交日与产品")
	lead = frappe.get_doc(
		{
			"doctype": "CRM Lead",
			"first_name": FIRST_NAME,
			"organization": ORG,
			"mobile_no": "13800000000",
		}
	).insert()
	created["CRM Lead"] = lead.name
	from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

	deal_name = convert_to_deal(lead=lead.name)
	created["CRM Deal"] = deal_name
	deal = frappe.get_doc("CRM Deal", deal_name)
	closure = get_last_day(nowdate())
	deal.expected_deal_value = 100000
	deal.probability = 50
	deal.expected_closure_date = closure
	deal.append("products", {"product_code": product.name, "product_name": ITEM, "qty": 40000, "rate": 2.5})
	deal.save()
	deal.reload()
	print(
		f"Lead={lead.name} 状态={frappe.db.get_value('CRM Lead', lead.name, ['status', 'converted'])}；"
		f"Deal={deal.name} organization={deal.organization!r} contacts={[c.contact for c in deal.contacts]}"
	)
	created["CRM Organization"] = deal.organization
	created["Contact"] = [c.contact for c in deal.contacts]
	check("Deal.currency（HT-005）", deal.currency, "CNY")
	check("Deal.expected_deal_value", flt(deal.expected_deal_value), 100000.0)
	check("Deal.probability", flt(deal.probability), 50.0)
	check("Deal.status（新建）", deal.status, "Qualification")

	step("3 推进两档")
	for status in ("Demo/Making", "Proposal/Quotation"):
		deal.status = status
		deal.save()
	deal.reload()
	log = [(r.get("from"), r.to) for r in deal.status_change_log]
	print(f"status_change_log={log}")
	check("Deal.status（推进后）", deal.status, "Proposal/Quotation")
	check("推进后 probability 未被状态默认值覆盖", flt(deal.probability), 50.0)

	step("4 Deal 页生成报价单（取界面按钮返回的预填参数）")
	from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import (
		can_create_quotations,
		get_quotation_url,
		prefill_quotation_items,
	)

	check("生成报价单入口可见（can_create_quotations）", can_create_quotations(), True)
	url = get_quotation_url(crm_deal=deal.name, organization=deal.organization)
	params = dict(parse_qsl(urlparse(url).query))
	print(f"url 路径={urlparse(url).path}；参数={params}")
	check("报价单 company 预填", params.get("company"), company)
	check("报价单 quotation_to 预填", params.get("quotation_to"), "CRM Deal")
	check("报价单 party_name 预填", params.get("party_name"), deal.name)
	check("报价单 contact_person 预填", params.get("contact_person"), deal.contacts[0].contact)
	items = prefill_quotation_items(crm_deal=deal.name)
	print(f"明细预填={items}")
	check("明细预填物料", [i["item_code"] for i in items], [ITEM])

	quotation = frappe.new_doc("Quotation")
	quotation.update({k: v for k, v in params.items()})
	quotation.transaction_date = nowdate()
	quotation.valid_till = add_days(nowdate(), 30)
	for row in items:
		quotation.append("items", row)
	quotation.insert()
	quotation.submit()
	created["Quotation"] = quotation.name
	print(
		f"Quotation={quotation.name} docstatus={quotation.docstatus} customer_name={quotation.customer_name!r} "
		f"crm_deal={quotation.crm_deal!r} grand_total={quotation.grand_total} currency={quotation.currency} "
		f"conversion_rate={quotation.conversion_rate}"
	)
	check("报价单已提交", quotation.docstatus, 1)
	check("报价单 currency", quotation.currency, "CNY")
	check("报价单 conversion_rate", flt(quotation.conversion_rate), 1.0)
	check("提交前站上无该 Deal 的客户", frappe.db.exists("Customer", {"crm_deal": deal.name}), None)

	step("5 报价单 → 销售订单，核自动建客户（LG-085）")
	from erpnext.selling.doctype.quotation.quotation import make_sales_order

	so = make_sales_order(quotation.name)
	print(f"make_sales_order 返回时 customer={so.customer!r}")
	so.delivery_date = add_days(nowdate(), 14)
	# 库存物料须有出库仓；测试站该公司无默认仓，界面上同样要手选（首跑报 WarehouseRequired）
	so.set_warehouse = frappe.db.get_value("Warehouse", {"company": company, "warehouse_name": "成品"})
	for row in so.items:
		row.delivery_date = so.delivery_date
		row.warehouse = so.set_warehouse
	so.insert()
	created["Sales Order"] = so.name
	customer = frappe.db.get_value("Customer", {"crm_deal": deal.name}, ["name", "customer_name", "default_currency"], as_dict=True)
	created["Customer"] = customer.name if customer else None
	print(f"Sales Order={so.name} customer={so.customer!r} currency={so.currency} conversion_rate={so.conversion_rate}；客户={customer}")
	check("站上新增客户，crm_deal 指向该 Deal", bool(customer), True)
	check("销售订单 customer 即该客户", so.customer, customer.name if customer else None)
	check("客户名取组织名", customer.customer_name if customer else None, ORG)
	check("销售订单 currency", so.currency, "CNY")
	check("销售订单 conversion_rate", flt(so.conversion_rate), 1.0)
	print(f"客户联系人={frappe.get_all('Dynamic Link', filters={'link_doctype': 'Customer', 'link_name': so.customer, 'parenttype': 'Contact'}, pluck='parent')}")

	step("6 看板：预测收入与转化")
	from crm.api.dashboard import get_forecasted_revenue, get_funnel_conversion

	month = getdate(closure).strftime("%Y-%m-01")
	revenue = {r["month"]: r for r in get_forecasted_revenue()["data"]}
	print(f"预测收入本月={revenue.get(month)}")
	check("预测收入本月值（100000×50÷100×1）", flt((revenue.get(month) or {}).get("forecasted")), 50000.0)
	funnel = {r["stage"]: r["count"] for r in get_funnel_conversion()["data"]}
	print(f"转化={funnel}")
	for stage in ("Demo/Making", "Proposal/Quotation"):
		check(f"转化含 {stage}", funnel.get(stage, 0) >= 1, True)

	step("7 异常路径：集成关闭")
	frappe.db.set_single_value("ERPNext CRM Settings", "enabled", 0)
	frappe.clear_document_cache("ERPNext CRM Settings", "ERPNext CRM Settings")
	check("关闭后生成报价单入口不可见（can_create_quotations）", can_create_quotations(), False)
	try:
		get_quotation_url(crm_deal=deal.name, organization=deal.organization)
		message = None
	except frappe.ValidationError as error:
		message = str(error)
	check("关闭后点生成报价单报错", message, "ERPNext is not integrated with the CRM")
	frappe.db.set_single_value("ERPNext CRM Settings", "enabled", 1)
	frappe.clear_document_cache("ERPNext CRM Settings", "ERPNext CRM Settings")
	check("已恢复 enabled", frappe.db.get_single_value("ERPNext CRM Settings", "enabled"), 1)


def cleanup():
	step("8 清理（逆序）")
	frappe.db.rollback()  # 丢掉失败时未提交的半截状态；已提交的逐个删
	# 按名字前缀找回，中断后单跑 --cleanup-only 也能清
	for so in frappe.get_all("Sales Order", filters={"customer_name": ORG}, pluck="name"):
		frappe.delete_doc("Sales Order", so)  # 未提交，直接删
	for name in frappe.get_all("Quotation", filters={"customer_name": ORG}, pluck="name"):
		doc = frappe.get_doc("Quotation", name)
		if doc.docstatus == 1:
			doc.cancel()
		frappe.delete_doc("Quotation", name)
	contacts = set(created.get("Contact") or []) | set(
		frappe.get_all("Contact", filters={"first_name": FIRST_NAME}, pluck="name")
	)
	# Deal 先于客户删：删客户会连带删只挂它的联系人，而联系人还被 Deal 的 contacts 引用（首跑报 LinkExistsError）
	for deal in frappe.get_all("CRM Deal", filters={"organization": ORG}, pluck="name"):
		frappe.delete_doc("CRM Deal", deal)
	for customer in frappe.get_all("Customer", filters={"customer_name": ORG}, pluck="name"):
		frappe.delete_doc("Customer", customer)
	for contact in contacts:
		if frappe.db.exists("Contact", contact):
			frappe.delete_doc("Contact", contact)
	for lead in frappe.get_all("CRM Lead", filters={"first_name": FIRST_NAME}, pluck="name"):
		frappe.delete_doc("CRM Lead", lead)
	if frappe.db.exists("CRM Organization", ORG):
		frappe.delete_doc("CRM Organization", ORG)
	for price in frappe.get_all("Item Price", filters={"item_code": ITEM}, pluck="name"):
		frappe.delete_doc("Item Price", price)
	if frappe.db.exists("Item", ITEM):
		frappe.delete_doc("Item", ITEM)  # CRM 的 Item.on_trash 同步删 CRM Product
	product = frappe.db.get_value("CRM Product", {"erpnext_item_code": ITEM})
	if product:
		frappe.delete_doc("CRM Product", product)
	frappe.db.commit()

	residue = {}
	for doctype, field in (
		("Item", "name"),
		("Item Price", "item_code"),
		("CRM Product", "product_code"),
		("CRM Lead", "first_name"),
		("CRM Deal", "organization"),
		("CRM Organization", "name"),
		("Contact", "first_name"),
		("Customer", "customer_name"),
		("Quotation", "customer_name"),
		("Sales Order", "customer_name"),
	):
		rows = frappe.get_all(doctype, filters={field: ["like", "_FCT%"]}, pluck="name")
		if rows:
			residue[doctype] = rows
	print(f"_FCT 前缀残留={residue or '无'}")
	check("清理后无残留", residue, {})


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--site", required=True)
	parser.add_argument("--cleanup-only", action="store_true", help="只清理上次中断留下的 _FCT 记录")
	args = parser.parse_args()
	if args.site != "test.localhost":
		print("本脚本只在测试站跑（R3 Part3 TS-010）", file=sys.stderr)
		return 2
	frappe.init(site=args.site, sites_path=".")
	frappe.connect()
	frappe.set_user("Administrator")
	try:
		try:
			if not args.cleanup_only:
				run()
				frappe.db.commit()
		except Exception:
			import traceback

			traceback.print_exc()
			failures.append("运行中断")
		cleanup()
	finally:
		frappe.destroy()
	print(f"\n结果：失败 {len(failures)} 项{('：' + '、'.join(failures)) if failures else ''}")
	return 1 if failures else 0


if __name__ == "__main__":
	sys.exit(main())
