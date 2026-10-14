# Read-only probe on erx.localhost: no commit, no writes. Run inside container with bench python.
import json, frappe
frappe.init(site="erx.localhost", sites_path="/workspace/frappe-bench/sites")
frappe.connect()
try:
    frappe.set_user("Administrator")
    frappe.local.lang = "zh"
    out = {}
    out["override"] = frappe.get_hooks("override_whitelisted_methods").get("crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections")
    out["resolved"] = frappe.override_whitelisted_method if False else None
    from frappe_china.website_translation import update_website_context
    ctx = frappe._dict(template="www/crm.html", boot={})
    update_website_context(ctx)
    html = frappe.render_template(ctx.template, ctx)
    out["crm_html_tag"] = [l for l in html.splitlines() if l.lstrip().startswith("<html")][:2]
    out["crm_labels_subset"] = {k: ctx.china_labels.get(k) for k in ("of","Load More","Empty","Select","Select {0}...")}
    from frappe.translate import get_all_translations
    m = get_all_translations("zh")
    out["merged"] = {k: m.get(k) for k in ("Available","Available:Raven User","{0} Filter Applied","{0} Filters Applied","(Empty)","Add {0}...","Select {0}...","This field is read only and cannot be edited.","Fetch Timesheet","From Date","To Date","Raven User","Select","Click to sort by {0}")}
    from frappe_china.crm_sidepanel import get_sidepanel_sections
    fields = [f for s in get_sidepanel_sections("CRM Lead") for c in s.get("columns") or [] for f in c.get("fields") or [] if isinstance(f, dict)]
    out["lead_placeholders"] = [(f.get("fieldtype"), f.get("label"), f.get("placeholder"), f.get("tooltip")) for f in fields]
    out["lead_label_raw_vs_zh"] = [(f.get("label"), frappe._(f.get("label") or "")) for f in fields]
    # perm-level read-only fields present?
    out["read_only_fields"] = [f.get("label") for f in fields if f.get("read_only")]
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
finally:
    frappe.db.rollback()
    frappe.destroy()
