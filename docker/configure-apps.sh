#!/usr/bin/env bash
set -euo pipefail

SITE_NAME="${1:-${SITE_NAME:-erx.localhost}}"
BENCH_DIR="${BENCH_DIR:-/workspace/frappe-bench}"
export FRAPPE_STREAM_LOGGING="${FRAPPE_STREAM_LOGGING:-1}"
cd "$BENCH_DIR"
python="./env/bin/python"
bench_cmd=(bench --site "$SITE_NAME")
die() { printf 'configure-apps: %s\n' "$*" >&2; exit 1; }
set_single() {
  local doctype="$1" field="$2" value="$3"
  "$python" - "$SITE_NAME" "$doctype" "$field" "$value" <<'PY'
import sys
import frappe
site, doctype, field, value = sys.argv[1:]
frappe.init(site=site, sites_path="sites"); frappe.connect()
try:
    if not frappe.db.exists("DocType", doctype) or not frappe.get_meta(doctype).has_field(field): raise SystemExit(0)
    current = frappe.db.get_single_value(doctype, field)
    if str(current if current is not None else "") != value:
        frappe.db.set_single_value(doctype, field, value); print(f"changed {doctype}.{field}")
    else: print(f"unchanged {doctype}.{field}")
    frappe.db.commit()
finally: frappe.destroy()
PY
}
set_single "ERPNext CRM Settings" enabled 1
set_single "ERPNext CRM Settings" is_erpnext_in_different_site 0
set_single "ERPNext CRM Settings" sync_products 1
set_single "ERPNext CRM Settings" create_customer_on_status_change 0
set_single "FCRM Settings" currency CNY
"$python" - "$SITE_NAME" <<'PY'
import sys
import frappe

site = sys.argv[1]
frappe.init(site=site, sites_path="sites"); frappe.connect()
try:
    # Saving the settings runs CRM's validation hooks, which create the
    # cross-app custom fields used by product sync and quotation conversion.
    if frappe.db.exists("DocType", "ERPNext CRM Settings"):
        settings = frappe.get_single("ERPNext CRM Settings")
        if settings.enabled and not settings.is_erpnext_in_different_site:
            settings.save(ignore_permissions=True)
            print("CRM integration validation completed")
    if frappe.db.exists("DocType", "CRM Settings") and "crm" in frappe.get_installed_apps():
        settings = frappe.get_single("CRM Settings")
        settings.enable_frappe_crm_data_synchronization = 1
        settings.save(ignore_permissions=True)
        print("ERPNext CRM synchronization validation completed")
    frappe.db.commit()
finally:
    frappe.destroy()
PY
"$python" - "$SITE_NAME" <<'PY'
import sys
import frappe
site = sys.argv[1]
frappe.init(site=site, sites_path="sites"); frappe.connect()
try:
    doctype = "ERPNext CRM Settings"
    meta = frappe.get_meta(doctype) if frappe.db.exists("DocType", doctype) else None
    if meta and meta.has_field("erpnext_company"):
        companies = frappe.get_all("Company", filters={"country": "China"}, pluck="name", limit_page_length=2)
        company = companies[0] if len(companies) == 1 else None
        if company and frappe.db.get_single_value(doctype, "erpnext_company") != company:
            frappe.db.set_single_value(doctype, "erpnext_company", company)
            print(f"changed {doctype}.erpnext_company")
        elif len(companies) > 1:
            print(f"skipped {doctype}.erpnext_company (multiple China companies; pass an explicit company later)")
    frappe.db.commit()
finally:
    frappe.destroy()
PY

if [[ -n "${RAVEN_LLM_URL:-}" || -n "${RAVEN_LLM_KEY:-}" || -n "${RAVEN_LLM_MODEL:-}" ]]; then
  [[ -n "${RAVEN_LLM_URL:-}" && -n "${RAVEN_LLM_KEY:-}" && -n "${RAVEN_LLM_MODEL:-}" ]] || die "RAVEN_LLM_URL, RAVEN_LLM_KEY and RAVEN_LLM_MODEL are required together"
fi
"$python" - "$SITE_NAME" "${RAVEN_LLM_URL:-}" "${RAVEN_LLM_KEY:-}" "${RAVEN_LLM_MODEL:-}" <<'PY'
import sys
import frappe
site, url, key, model = sys.argv[1:]
frappe.init(site=site, sites_path="sites"); frappe.connect()
try:
    has_llm_config = bool(url and key and model)
    if has_llm_config and frappe.db.exists("DocType", "Raven Settings"):
        doc = frappe.get_single("Raven Settings")
        doc.update({"enable_ai_integration": 1, "enable_local_llm": 1, "local_llm_provider": "OpenAI Compatible", "local_llm_api_url": url, "openai_compatible_api_key": key})
        doc.save(ignore_permissions=True); print("Raven Settings configured (key omitted)")
    if frappe.db.exists("DocType", "Raven AI Function") and frappe.db.exists("DocType", "Raven Bot"):
        tools = [
            ("list_crm_deals", "Get List", "CRM Deal", "List submitted CRM deals with name, organization_name, lead_name, expected_deal_value, probability, and status."),
            ("get_crm_deal", "Get Document", "CRM Deal", "Read one CRM deal and its child rows."),
            ("list_crm_deal_statuses", "Get List", "CRM Deal Status", "List CRM deal statuses, including Won and Lost."),
            ("list_purchase_receipts", "Get List", "Purchase Receipt", "List submitted purchase receipts with supplier, posting_date, and docstatus."),
            ("get_purchase_receipt", "Get Document", "Purchase Receipt", "Read one purchase receipt, including received_qty, rejected_qty, qty, and rate."),
            ("list_suppliers", "Get List", "Supplier", "List suppliers used for purchase analysis."),
            ("list_items", "Get List", "Item", "List items used in purchase, sales, and BOM analysis."),
            ("get_item", "Get Document", "Item", "Read one item and its purchasing and sales fields."),
            ("list_sales_orders", "Get List", "Sales Order", "List submitted sales orders with customer, transaction_date, grand_total, and docstatus."),
            ("get_sales_order", "Get Document", "Sales Order", "Read one sales order, including its item rows."),
            ("list_boms", "Get List", "BOM", "List active BOMs with item, is_active, total_cost, and quantity."),
            ("get_bom", "Get Document", "BOM", "Read one BOM and its item rows."),
            ("list_customers", "Get List", "Customer", "List customers for follow-up analysis."),
            ("get_supplier", "Get Document", "Supplier", "Read one supplier and its purchasing fields."),
            ("run_report", "Custom Function", None, "Run one of the approved read-only reports with report_name and filters."),
        ]
        names = []
        changed_functions = []
        for name, kind, ref, description in tools:
            exists = frappe.db.exists("Raven AI Function", name)
            doc = frappe.get_doc("Raven AI Function", name) if exists else frappe.new_doc("Raven AI Function")
            function_path = "frappe_china.ai.queries.run_report" if kind == "Custom Function" else None
            reference_doctype = ref if kind != "Custom Function" else None
            params = '{"type":"object","properties":{"report_name":{"type":"string"},"filters":{"type":"object"}},"required":["report_name","filters"]}' if name == "run_report" else None
            changed = not exists or any(
                str(doc.get(field) if doc.get(field) is not None else "") != str(value if value is not None else "")
                for field, value in {
                    "function_name": name,
                    "type": kind,
                    "description": description,
                    "reference_doctype": reference_doctype,
                    "function_path": function_path,
                    "requires_write_permissions": 0,
                    "strict": 0,
                }.items()
            )
            if name == "run_report":
                import json
                changed = changed or json.loads(doc.params or "{}") != json.loads(params)
            if changed:
                doc.function_name = name; doc.type = kind; doc.description = description
                doc.reference_doctype = reference_doctype
                doc.function_path = function_path
                doc.requires_write_permissions = 0; doc.strict = 0
                if name == "run_report":
                    doc.pass_parameters_as_json = 0
                    doc.params = params
                doc.save(ignore_permissions=True); changed_functions.append(name)
            names.append(name)
        write_types = {
            "Create Document", "Create Multiple Documents", "Update Document", "Update Multiple Documents",
            "Delete Document", "Delete Multiple Documents", "Submit Document", "Cancel Document",
            "Set Value", "Send Message", "Attach File to Document",
        }
        write_functions = frappe.get_all(
            "Raven AI Function",
            filters={"type": ["in", list(write_types)]},
            pluck="function_name",
        )
        unexpected_writes = sorted(set(write_functions) - set(names))
        if unexpected_writes:
            raise RuntimeError("write-capable Raven AI Functions already exist: " + ", ".join(unexpected_writes))
        bot_name = "ERX 分析助手"
        bot_exists = frappe.db.exists("Raven Bot", bot_name)
        bot = frappe.get_doc("Raven Bot", bot_name) if bot_exists else frappe.new_doc("Raven Bot")
        instruction = "你是华东弹簧有限公司的经营分析助手，只读，不修改任何数据。回答任何问题前，先用工具取数，不凭记忆回答。只统计已提交的单据（docstatus = 1），草稿与已取消的单据不算。回答的最后一段列出你用到的单据号或报表名。金额保留两位小数，百分比保留一位小数。用中文回答。"
        current_functions = [row.function for row in bot.get("bot_functions") or []]
        bot_changed = not bot_exists or any(
            str(bot.get(field) if bot.get(field) is not None else "") != str(value if value is not None else "")
            for field, value in {
                "is_ai_bot": 1,
                "model_provider": "Local LLM",
                "model": model,
                "instruction": instruction,
                "enable_code_interpreter": 0,
                "enable_file_search": 0,
                "debug_mode": 1,
                "allow_bot_to_write_documents": 0,
            }.items()
        ) or current_functions != names
        if bot_changed:
            bot.bot_name = bot_name; bot.is_ai_bot = 1; bot.model_provider = "Local LLM"; bot.model = model
            bot.instruction = instruction
            bot.enable_code_interpreter = 0; bot.enable_file_search = 0; bot.debug_mode = 1; bot.allow_bot_to_write_documents = 0
            bot.set("bot_functions", [{"function": n} for n in names]); bot.save(ignore_permissions=True)
        if changed_functions or bot_changed:
            print(f"Raven read-only bot configured with {len(names)} tools")
        else:
            print(f"Raven tools and bot unchanged ({len(names)} tools)")
    frappe.db.commit()
finally: frappe.destroy()
PY
if [[ -z "${RAVEN_LLM_URL:-}" && -z "${RAVEN_LLM_KEY:-}" && -z "${RAVEN_LLM_MODEL:-}" ]]; then
  printf 'configure-apps: Raven tools and bot structure configured; LiteLLM connection skipped (RAVEN_LLM_* not configured)\n'
fi
"${bench_cmd[@]}" execute frappe_china.install.reorder_installed_apps
"${bench_cmd[@]}" clear-cache
