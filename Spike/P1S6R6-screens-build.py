"""TS-022 第 3 步：生成 Spike/P1S6R6-screens.json 与 Spike/P1S6R6-screens-map.md（宿主 python -I -X utf8 跑）。

来源：R4 的 Spike/P1S6R4-screens-forms.json（55 屏）与 Spike/P1S6R4-screens.json（独立前端 6 屏），在其上：
  ① 新建单据补「保存后」态（DEC-032），保存后屏打开造数脚本建好的那张单据（{{占位}}，值取 values.json）；
  ② 由上游「创建」生成的单据补「预填」态：打开上游单据、点「创建」菜单项（state=prefilled，不用 set_route）；
  ③ 补 §4.9 表一里 R4 没有的屏（仓库新建对话框、工序命名对话框、工单列表、生产任务单列表、开始计时对话框、
     销售订单状态菜单、发票列表徽标、结转生成／取消对话框、现金流量底稿表单、开账跳转到总账）；
  ④ 末尾 15 个可提交单据类型各一张提交确认框、一张取消确认框（A22）。
占位名与 Spike/P1S6R6-closed-loop.py 的状态键同名，故状态文件直接作 values.json。
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R4_FORMS = json.loads((ROOT / "Spike/P1S6R4-screens-forms.json").read_text(encoding="utf-8"))
R4_APPS = json.loads((ROOT / "Spike/P1S6R4-screens.json").read_text(encoding="utf-8"))
BF = "Business Flow"


def form_ready(doctype: str) -> str:
	return f'window.cur_frm?.doctype==={json.dumps(doctype)} && !!cur_frm.fields_dict && !frappe.dom.freeze_count'


def list_ready(doctype: str) -> str:
	return f"cur_list?.doctype==={json.dumps(doctype)} && !!document.querySelector('.list-row-container, .no-result')"


def slug(doctype: str) -> str:
	return doctype.lower().replace(" ", "-")


def saved(sid: str, stage: str, doctype: str, var: str) -> dict:
	return {"id": sid, "stage": stage, "state": "saved", "route": f"desk/{slug(doctype)}/{{{{{var}}}}}",
		"wait_for": form_ready(doctype), "sidebar": BF}


def prefilled(sid: str, stage: str, src_doctype: str, src_var: str, item: str | list, doctype: str) -> dict:
	return {"id": sid, "stage": stage, "state": "prefilled", "route": f"desk/{slug(src_doctype)}/{{{{{src_var}}}}}",
		"wait_for": form_ready(src_doctype), "sidebar": BF,
		"steps": [{"menu": ["Create", "创建"], "item": item, "wait_for": f"window.cur_frm?.doctype==={json.dumps(doctype)} && cur_frm.is_new()", "timeout": 60000}],
		"ready": form_ready(doctype)}


screens: list[dict] = []
mapping: dict[str, list[str]] = {}


def add(row: str, screen: dict) -> None:
	screens.append(screen)
	mapping.setdefault(row, []).append(screen["id"])


# ---------- 沿用 R4 的 55 屏（新建态＝blank，列表／报表／树另定 state；步骤 selector 改为 click） ----------
R4_ROW = {
	"01": "环节1", "02": "环节2", "03": "环节3", "04": "环节4", "05": "环节5", "06": "环节6", "07": "环节7",
	"08": "环节8", "09": "环节9", "10": "环节10", "11": "环节11", "13": "环节13", "14": "环节14", "15": "环节15",
	"16": "环节16", "17": "环节17", "18": "环节18", "19": "环节19", "21": "环节21", "22": "环节22",
}
for raw in R4_FORMS["screens"]:
	s = copy.deepcopy(raw)
	s["steps"] = [{"click": st["selector"], "wait_for": "!frappe.dom.freeze_count"} if "selector" in st else st for st in s.get("steps", [])]
	sid = s["id"]
	if sid.startswith("report-"):
		s["state"] = "report"
		name = sid[len("report-"):]
		row = {"Stock Balance": "环节12", "Stock Ledger": "环节12", "Stock and Account Value Comparison": "环节12",
			"General Ledger": "环节13", "BOM Variance Report": "环节20"}.get(name, "环节23")
	elif sid.startswith("s4-"):
		s["state"] = "list" if sid.endswith("-list") else "blank"
		row = "S4 自有功能"
	elif sid in ("home",) or sid.startswith("sidebar-"):
		s["state"] = "list"
		row = "首页与侧栏"
	else:
		route = s.get("route", "")
		s["state"] = "blank" if "/new-" in route else ("list" if route.count("/") <= 1 or "/view/" in route else "saved")
		row = R4_ROW.get(sid[:2], "环节1")
	if "route" in s and s["route"].startswith("desk/company/%E5%8D%8E"):
		s["route"] = "desk/company/{{company}}"
	if s["id"] == "06-bom-new-costing":  # 新建 BOM 不显示「成本核算」页签，改在已保存的 BOM 上核
		s["route"] = "desk/bom/{{bom}}"; s["state"] = "saved"
	if not s.get("wait_for") or s["wait_for"] == "!!document.body":
		s["wait_for"] = "!!document.body.innerText.trim()"
	add(row, s)

# ---------- ① 新建单据的保存后态 ----------
SAVED = [
	("04-item-saved", "环节4", "Item", "fg"), ("04-item-price-saved", "环节4", "Item Price", "price"),
	("05-workstation-saved", "环节5", "Workstation", "workstation"), ("05-operation-saved", "环节5", "Operation", "op1"),
	("05-routing-saved", "环节5", "Routing", "routing"),
	("06-bom-saved", "环节6", "BOM", "bom_draft"), ("06-bom-submitted", "环节6", "BOM", "bom"),
	("07-supplier-saved", "环节7", "Supplier", "supplier"), ("07-customer-saved", "环节7", "Customer", "customer"),
	("08-purchase-order-saved", "环节8", "Purchase Order", "po_draft"), ("08-purchase-order-submitted", "环节8", "Purchase Order", "purchase_order"),
	("09-purchase-receipt-saved", "环节9", "Purchase Receipt", "purchase_receipt"),
	("10-purchase-invoice-saved", "环节10", "Purchase Invoice", "purchase_invoice"),
	("11-payment-entry-saved", "环节11", "Payment Entry", "purchase_payment"),
	("13-journal-entry-saved", "环节13", "Journal Entry", "opening"),
	("14-quotation-saved", "环节14", "Quotation", "quotation"),
	("15-sales-order-saved", "环节15", "Sales Order", "sales_order"),
	("16-production-plan-saved", "环节16", "Production Plan", "production_plan"),
	("17-work-order-saved", "环节17", "Work Order", "work_order"),
	("18-stock-entry-saved", "环节18", "Stock Entry", "transfer"),
	("19-job-card-saved", "环节19", "Job Card", "job_card_1"), ("19-employee-saved", "环节19", "Employee", "employee"),
	("20-stock-entry-manufacture", "环节20", "Stock Entry", "manufacture"),
	("21-delivery-note-saved", "环节21", "Delivery Note", "delivery_note"),
	("22-sales-invoice-saved", "环节22", "Sales Invoice", "sales_invoice"),
	("22-payment-entry-receive", "环节22", "Payment Entry", "sales_payment"),
	("s4-month-end-saved", "S4 自有功能", "Month End Closing Voucher", "mecv"),
	("s4-cash-flow-saved", "S4 自有功能", "Cash Flow Worksheet", "cfw"),
]
for sid, row, dt, var in SAVED:
	add(row, saved(sid, row, dt, var))

# ---------- ② 由上游「创建」生成的预填态 ----------
PREFILLED = [
	("09-purchase-receipt-prefilled", "环节9", "Purchase Order", "po_fresh", ["采购入库", "Purchase Receipt"], "Purchase Receipt"),
	("10-purchase-invoice-prefilled", "环节10", "Purchase Receipt", "pr_fresh", ["采购发票", "Purchase Invoice"], "Purchase Invoice"),
	("11-payment-entry-prefilled", "环节11", "Purchase Invoice", "pi_fresh", ["收付款", "Payment"], "Payment Entry"),
	("15-sales-order-prefilled", "环节15", "Quotation", "qtn_open", ["销售订单", "Sales Order"], "Sales Order"),
	("21-delivery-note-prefilled", "环节21", "Sales Order", "so2", ["销售出库", "Delivery Note"], "Delivery Note"),
	("22-sales-invoice-prefilled", "环节22", "Delivery Note", "dn_open", ["销售发票", "Sales Invoice"], "Sales Invoice"),
	("22-payment-entry-prefilled", "环节22", "Sales Invoice", "si_open", ["收付款", "Payment"], "Payment Entry"),
]
for args in PREFILLED:
	add(args[1], prefilled(*args))

# ---------- ③ §4.9 表一里 R4 没有的屏 ----------
EXTRA = [
	("环节2", {"id": "02-warehouse-new-dialog", "stage": "环节2", "state": "dialog", "route": "desk/warehouse/view/tree",
		"wait_for": "!!document.querySelector('.tree-node')", "sidebar": BF,
		"steps": [{"click": ".page-actions .primary-action", "wait_for": "!!document.querySelector('.modal.show')"}],
		"extract_root": ".modal.show", "after": [{"dialog_close": True}]}),
	("环节5", {"id": "05-operation-naming-dialog", "stage": "环节5", "state": "dialog", "route": "desk/operation/new-operation-1",
		"wait_for": form_ready("Operation"), "sidebar": BF,
		"steps": [{"primary": ["保存", "Save"], "wait_for": "!!document.querySelector('.modal.show')"}],
		"extract_root": ".modal.show", "after": [{"dialog_close": True}]}),
	("环节17", {"id": "17-work-order-list", "stage": "环节17", "state": "list", "route": "desk/work-order",
		"wait_for": list_ready("Work Order"), "sidebar": BF}),
	("环节19", {"id": "19-job-card-list", "stage": "环节19", "state": "list", "route": "desk/job-card",
		"wait_for": list_ready("Job Card"), "sidebar": BF}),
	("环节19", {"id": "19-job-card-start-dialog", "stage": "环节19", "state": "dialog", "route": "desk/job-card/{{jc_open}}",
		"wait_for": form_ready("Job Card"), "sidebar": BF,
		"steps": [{"click": ".jcd-btn-start, .btn-start", "wait_for": "!!document.querySelector('.modal.show')"}],
		"extract_root": ".modal.show", "after": [{"dialog_close": True}]}),
	("环节21", {"id": "21-sales-order-status-menu", "stage": "环节21", "state": "saved", "route": "desk/sales-order/{{so2}}",
		"wait_for": form_ready("Sales Order"), "sidebar": BF, "steps": [{"open_menu": ["Status", "状态"]}]}),
	("环节22", {"id": "22-sales-invoice-list", "stage": "环节22", "state": "list", "route": "desk/sales-invoice",
		"wait_for": list_ready("Sales Invoice"), "sidebar": BF,
		"include_selectors": [{"selector": ".list-row .indicator-pill", "reason": "列表状态徽标是界面文案（§4.2.6 出路 1）"}]}),
	("S4 自有功能", {"id": "s4-month-end-generate-dialog", "stage": "S4", "state": "dialog", "route": "desk/month-end-closing-voucher",
		"wait_for": "cur_list?.doctype==='Month End Closing Voucher'", "sidebar": BF,
		"steps": [{"click": ".page-actions .btn", "text": ["生成月末结转", "Generate Month End Closing"], "wait_for": "!!document.querySelector('.modal.show')"}],
		"extract_root": ".modal.show", "after": [{"dialog_close": True}]}),
	("S4 自有功能", {"id": "s4-month-end-cancel-dialog", "stage": "S4", "state": "dialog", "route": "desk/month-end-closing-voucher",
		"wait_for": "cur_list?.doctype==='Month End Closing Voucher'", "sidebar": BF,
		"steps": [{"click": ".page-actions .btn", "text": ["取消月末结转", "Cancel Month End Closing"], "wait_for": "!!document.querySelector('.modal.show')"}],
		"extract_root": ".modal.show", "after": [{"dialog_close": True}]}),
	("S4 自有功能", {"id": "s4-cash-flow-draft", "stage": "S4", "state": "saved", "route": "desk/cash-flow-worksheet/{{cfw_draft}}",
		"wait_for": form_ready("Cash Flow Worksheet"), "sidebar": BF}),
	("环节13", {"id": "13-opening-to-ledger", "stage": "环节13", "state": "report", "route": "desk/journal-entry/{{opening}}",
		"wait_for": form_ready("Journal Entry"), "sidebar": BF,
		"steps": [{"menu": ["View", "查看"], "item": ["会计账簿", "Ledger"], "wait_for": "!!window.frappe?.query_report?.filters && !frappe.dom.freeze_count", "timeout": 60000}]}),
]
for row, s in EXTRA:
	add(row, s)

# ---------- 独立前端（表二） ----------
for raw in R4_APPS["screens"]:
	if "url" not in raw:
		continue
	s = copy.deepcopy(raw)
	s["url"] = s["url"].replace("http://erx.localhost:8000", "")
	s["state"] = "list"
	s["wait_for"] = "!!document.body.innerText.trim() && !document.querySelector('.animate-spin, .loading-indicator')"
	add({"crm": "表二 /crm", "raven": "表二 /raven", "insights": "表二 /insights"}[raw["stage"].lower()] if raw["stage"].lower() in ("crm", "raven", "insights") else "表二", s)
add("表二 /crm", {"id": "crm-lead-detail", "stage": "CRM", "state": "saved", "url": "/crm/leads/{{crm_lead}}",
	"wait_for": "!!document.body.innerText.trim() && !document.querySelector('.animate-spin')"})
add("表二 /crm", {"id": "crm-deal-detail", "stage": "CRM", "state": "saved", "url": "/crm/deals/{{crm_deal}}",
	"wait_for": "!!document.body.innerText.trim() && !document.querySelector('.animate-spin')"})

# ---------- ④ 确认框（A22）：15 个可提交单据类型，提交（草稿）＋取消（已提交）各一 ----------
CONFIRM = [
	("BOM", "bom_draft", "bom"), ("Purchase Order", "po_draft", "po_fresh"),
	("Purchase Receipt", "pr_draft", "pr_fresh"), ("Purchase Invoice", "pi_draft", "pi_fresh"),
	("Payment Entry", "pe_draft", "purchase_payment"), ("Quotation", "qtn_draft", "qtn_open"),
	("Sales Order", "so_draft", "so2"), ("Production Plan", "pp_draft", "production_plan"),
	("Work Order", "wo_draft", "work_order"), ("Stock Entry", "se_draft", "transfer"),
	("Job Card", "jc_open", "job_card_1"), ("Delivery Note", "dn_draft", "dn_open"),
	("Sales Invoice", "si_draft", "si_open"), ("Month End Closing Voucher", None, "mecv"),
	("Cash Flow Worksheet", "cfw_draft", "cfw"),
]
for dt, draft, done in CONFIRM:
	for action, var in (("submit", draft), ("cancel", done)):
		if var is None:
			continue  # 结转凭证只由「生成月末结转」建、建即提交，没有草稿
		add("确认框（A22）", {"id": f"confirm-{action}-{slug(dt)}", "stage": "确认框", "state": "dialog",
			"route": f"desk/{slug(dt)}/{{{{{var}}}}}", "sidebar": BF,
			"dialog": {"action": action, "doctype": dt, "name": f"{{{{{var}}}}}"}})

# ---------- 输出 ----------
variables = {}
for s in screens:
	for name in __import__("re").findall(r"\{\{(\w+)\}\}", json.dumps(s, ensure_ascii=False)):
		variables[name] = {"from": "Spike/P1S6R6-closed-loop-<site>.json 同名键（造数脚本写入；作 values.json 传入）"}
spec = {
	"note": "R6 TS-022 生成；生成脚本 Spike/P1S6R6-screens-build.py。占位值由 values.json（造数状态文件）提供",
	"allow": R4_FORMS["allow"],
	"data_selectors": R4_FORMS["data_selectors"],
	"data_patterns": [
		{"pattern": r"\b(?:[A-Z]{2,}-)+(?:[A-Z0-9]+-)*\d{3,}(?:-\d+)?\b", "reason": "单据编号（编号规则生成，用户数据）"},
		{"pattern": r"\bPO-JOB\d+\b|\bBOM-\S+", "reason": "生产任务单与物料清单编号（用户数据）"},
		{"pattern": r"_?S6R6?\S*", "reason": "本轮造数前缀与测试公司简称（用户数据）"},
	],
	"default_data": {},
	"trad_chars_file": "P1S6R6-trad-chars.json",
	"variables": variables,
	"screens": screens,
}
(ROOT / "Spike/P1S6R6-screens.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")

TABLE1 = ["环节1", "环节2", "环节3", "环节4", "环节5", "环节6", "环节7", "环节8", "环节9", "环节10", "环节11", "环节12",
	"环节13", "环节14", "环节15", "环节16", "环节17", "环节18", "环节19", "环节20", "环节21", "环节22", "环节23",
	"首页与侧栏", "S4 自有功能"]
TABLE2 = ["表二 /crm", "表二 /raven", "表二 /insights"]
from collections import Counter
by_state = Counter(s["state"] for s in screens)
lines = ["# P1-S6-R6 逐屏核屏清单映射（需求 §4.9 行 → 屏 id）", "",
	f"生成：`Spike/P1S6R6-screens-build.py`。屏总数 **{len(screens)}**；按状态：" + "、".join(f"{k} {v}" for k, v in sorted(by_state.items())), "",
	"| §4.9 行 | 屏数 | 屏 id |", "|---|---|---|"]
empty = []
for row in TABLE1 + TABLE2 + ["确认框（A22）"]:
	ids = mapping.get(row, [])
	if not ids:
		empty.append(row)
	lines.append(f"| {row} | {len(ids)} | {'、'.join(f'`{i}`' for i in ids) or '**空**'} |")
lines += ["", f"空映射：{'、'.join(empty) if empty else '无'}"]
(ROOT / "Spike/P1S6R6-screens-map.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps({"screens": len(screens), "by_state": by_state, "empty_rows": empty, "variables": sorted(variables)}, ensure_ascii=False))
