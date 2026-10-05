#!/usr/bin/env bash
set -euo pipefail

SITE_NAME="${1:-${SITE_NAME:-erx.localhost}}"
BENCH_DIR="${BENCH_DIR:-/workspace/frappe-bench}"
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
frappe.init(site=site); frappe.connect()
try:
    if not frappe.db.exists("DocType", doctype) or not frappe.get_meta(doctype).has_field(field): raise SystemExit(0)
    current = frappe.db.get_single_value(doctype, field)
    if str(current or "") != value:
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
if [[ -n "${RAVEN_LLM_URL:-}" || -n "${RAVEN_LLM_KEY:-}" || -n "${RAVEN_LLM_MODEL:-}" ]]; then
  [[ -n "${RAVEN_LLM_URL:-}" && -n "${RAVEN_LLM_KEY:-}" && -n "${RAVEN_LLM_MODEL:-}" ]] || die "RAVEN_LLM_URL, RAVEN_LLM_KEY and RAVEN_LLM_MODEL are required together"
  "$python" - "$SITE_NAME" "$RAVEN_LLM_URL" "$RAVEN_LLM_KEY" "$RAVEN_LLM_MODEL" <<'PY'
import sys
import frappe
site, url, key, model = sys.argv[1:]
frappe.init(site=site); frappe.connect()
try:
    if frappe.db.exists("DocType", "Raven Settings"):
        doc = frappe.get_single("Raven Settings")
        doc.update({"enable_ai_integration": 1, "enable_local_llm": 1, "local_llm_provider": "OpenAI Compatible", "local_llm_api_url": url, "openai_compatible_api_key": key})
        doc.save(ignore_permissions=True); print("Raven Settings configured (key omitted)")
    if frappe.db.exists("DocType", "Raven AI Function") and frappe.db.exists("DocType", "Raven Bot"):
        tools = [
            ("list_crm_deals", "Get List", "CRM Deal", "frappe_china.ai.queries.list_crm_deals"),
            ("list_purchase_receipts", "Get List", "Purchase Receipt", "frappe_china.ai.queries.list_purchase_receipts"),
            ("list_sales_orders", "Get List", "Sales Order", "frappe_china.ai.queries.list_sales_orders"),
            ("list_boms", "Get List", "BOM", "frappe_china.ai.queries.list_boms"),
            ("run_report", "Custom Function", None, "raven.ai.functions.get_report_result"),
        ]
        names = []
        for name, kind, ref, path in tools:
            doc = frappe.get_doc({"doctype": "Raven AI Function", "function_name": name, "type": kind, "reference_doctype": ref, "function_path": path, "description": "Read-only reporting tool"})
            if frappe.db.exists("Raven AI Function", name): doc = frappe.get_doc("Raven AI Function", name)
            doc.save(ignore_permissions=True); names.append(doc.name)
        bot_name = "ERX Read Only Assistant"
        bot = frappe.get_doc("Raven Bot", bot_name) if frappe.db.exists("Raven Bot", bot_name) else frappe.new_doc("Raven Bot")
        bot.bot_name = bot_name; bot.is_ai_bot = 1; bot.model_provider = "Local LLM"; bot.model = model; bot.allow_bot_to_write_documents = 0
        bot.set("bot_functions", [{"function": n, "type": "Custom Function" if n == "run_report" else "Get List"} for n in names]); bot.save(ignore_permissions=True)
        print(f"Raven read-only bot configured with {len(names)} tools")
    frappe.db.commit()
finally: frappe.destroy()
PY
else
  printf 'configure-apps: Raven skipped (RAVEN_LLM_* not configured)\n'
fi
"${bench_cmd[@]}" execute frappe_china.install.reorder_installed_apps
"${bench_cmd[@]}" clear-cache
