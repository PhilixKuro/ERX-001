"""P1-S5-R5 SB IT-005：演示站接入四个 App 后的验证（R3 Part2 TS-007 第 5～6 步、TS-008 第 3 步）。

只读核对，唯一的写操作是 TS-007 第 5 步要求的「在 zh 下保存一次 HDTH」。
容器内运行（工作目录 sites/）：
    /workspace/frappe-bench/env/bin/python <本文件> --site erx.localhost [--no-save]
"""

import argparse
import json
import sys

import frappe

COMPANY = "华东弹簧有限公司"
APPS = ("crm", "hrms", "insights", "raven")
EMPTY_DOCTYPES = (
	"GL Entry",
	"Stock Ledger Entry",
	"Customer",
	"Supplier",
	"Item",
	"Sales Invoice",
	"Purchase Invoice",
	"Journal Entry",
)

failures = []


def check(label, actual, expected):
	ok = actual == expected
	print(f"[{'通过' if ok else '失败'}] {label}：实得 {actual!r}，应为 {expected!r}")
	if not ok:
		failures.append(label)


def step(title):
	print(f"\n== {title} ==")


def expense_rows():
	from frappe_china.accounting.hr import expense_claim_account_number

	rows = frappe.db.sql(
		"""
		select eca.parent, eca.default_account, acc.account_number
		from `tabExpense Claim Account` eca
		left join `tabAccount` acc on acc.name = eca.default_account
		where eca.company = %s
		order by eca.parent
		""",
		COMPANY,
		as_dict=True,
	)
	types = frappe.get_all("Expense Claim Type", pluck="name", order_by="name")
	print(f"站上报销类型 {len(types)} 个：{types}")
	for row in rows:
		expected = expense_claim_account_number(row.parent)
		print(f"    {row.parent} → {row.default_account}（科目号 {row.account_number}，映射 {expected}）")
		check(f"{row.parent} 科目号与映射一致", row.account_number, expected)
	check("HDTH 的 Expense Claim Account 行数", len(rows), 5)
	check("每个报销类型恰有一行", sorted(r.parent for r in rows), types)


def company_check(label):
	from frappe_china.accounting.selfcheck import check_all_cn_companies

	results = check_all_cn_companies()
	mine = [r for r in results if r["company"] == COMPANY]
	check(f"{label}：中式公司只有 HDTH", [r["company"] for r in results], [COMPANY])
	if mine:
		r = mine[0]
		print(f"    {json.dumps(r, ensure_ascii=False)}")
		check(f"{label}：科目数", r["account_count"], 266)
		check(f"{label}：自检 ok", r["ok"], True)
		check(f"{label}：extra_accounts", r["extra_accounts"], [])
	check(
		f"{label}：无 Expense Claims 科目",
		bool(frappe.db.exists("Account", {"account_name": "Expense Claims"})),
		False,
	)


def config_checks():
	step("SL-005 ① CRM 集成字段")
	crm = frappe.get_single("ERPNext CRM Settings")
	check("ERPNext CRM Settings.enabled", crm.enabled, 1)
	check("ERPNext CRM Settings.is_erpnext_in_different_site", crm.is_erpnext_in_different_site, 0)
	check("ERPNext CRM Settings.sync_products", crm.sync_products, 1)
	check("ERPNext CRM Settings.create_customer_on_status_change", crm.create_customer_on_status_change, 0)
	check("ERPNext CRM Settings.erpnext_company", crm.erpnext_company, COMPANY)
	check("FCRM Settings.currency", frappe.db.get_single_value("FCRM Settings", "currency"), "CNY")

	step("SL-007 ② 演示 bot 与只读工具")
	bot = frappe.get_doc("Raven Bot", "ERX 分析助手")
	check("bot is_ai_bot", bot.is_ai_bot, 1)
	check("bot model_provider", bot.model_provider, "Local LLM")
	check("bot allow_bot_to_write_documents", bot.allow_bot_to_write_documents, 0)
	names = [row.function for row in bot.bot_functions]
	print(f"bot_functions（{len(names)} 条）：{names}")
	check("bot_functions 条数", len(names), 15)
	types = frappe.get_all("Raven AI Function", fields=["name", "type"], order_by="name")
	allowed = {"Get List", "Get Document", "Custom Function", "Get Report Result"}
	bad = [f"{t.name}={t.type}" for t in types if t.type not in allowed]
	print(f"站上 Raven AI Function {len(types)} 条，类型分布：{sorted({t.type for t in types})}")
	check("站上无写类工具", bad, [])
	check("_FCT 前缀公司", frappe.get_all("Company", filters={"name": ["like", "_FCT%"]}, pluck="name"), [])


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--site", required=True)
	parser.add_argument("--no-save", action="store_true", help="跳过保存 HDTH（复核时用）")
	parser.add_argument("--config", action="store_true", help="另核 configure-apps.sh 写下的字段（SL-005 ①、SL-007 ②）")
	args = parser.parse_args()

	frappe.init(site=args.site)
	frappe.connect()
	frappe.set_user("Administrator")
	try:
		step("SL-004 ② 四个 App 已装、frappe_china 归位")
		installed = frappe.get_installed_apps()
		print(f"installed_apps = {installed}")
		for app in APPS:
			check(f"{app} 已装", app in installed, True)

		step("SL-004 ③ HDTH 报销科目（保存前）")
		expense_rows()
		company_check("保存前")

		if not args.no_save:
			step("SL-004 ③ 在 zh 下保存一次 HDTH")
			frappe.local.lang = "zh"
			doc = frappe.get_doc("Company", COMPANY)
			doc.save()
			frappe.db.commit()
			print(f"已保存，modified = {doc.modified}")
			step("SL-004 ③ HDTH 报销科目（保存后）")
			expense_rows()
			company_check("保存后")

		step("SL-004 ⑥ 空账核对")
		for doctype in EMPTY_DOCTYPES:
			check(f"{doctype} 计数", frappe.db.count(doctype), 0)

		step("SL-004 ④ check_app_order（TS-008 第 3 步）")
		from frappe_china.install import check_app_order

		result = check_app_order()
		print(json.dumps(result, ensure_ascii=False, indent=2))
		check("check_app_order ok", result["ok"], True)

		if args.config:
			config_checks()
	finally:
		frappe.destroy()

	print(f"\n结果：{'全部通过' if not failures else '失败 ' + str(len(failures)) + ' 项：' + '；'.join(failures)}")
	sys.exit(1 if failures else 0)


if __name__ == "__main__":
	main()
