"""Create the planned DocType definitions; run with host Python, no site writes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "frappe-bench/apps/frappe_china/frappe_china/production_plus/doctype"


def field(name, kind, label, **kwargs):
    return dict(fieldname=name, fieldtype=kind, label=label, **kwargs)


def write(name, fields, **kwargs):
    slug = name.lower().replace(" ", "_")
    doc = dict(doctype="DocType", name=name, module="Production Plus", engine="InnoDB",
               modified="2026-10-16 16:10:00.000000", field_order=[f["fieldname"] for f in fields], fields=fields, **kwargs)
    (ROOT / slug / (slug + ".json")).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


write("Piece Rate Summary", [
    field("naming_series", "Select", "Naming Series", options="PRS-.YYYY.-.#####", default="PRS-.YYYY.-.#####", reqd=1),
    field("employee", "Link", "Employee", options="Employee", reqd=1, in_list_view=1),
    field("employee_name", "Data", "Employee Name", fetch_from="employee.employee_name", read_only=1),
    field("company", "Link", "Company", options="Company", reqd=1, in_standard_filter=1),
    field("from_date", "Date", "From Date", reqd=1, in_list_view=1),
    field("to_date", "Date", "To Date", reqd=1, in_list_view=1),
    field("currency", "Link", "Currency", options="Currency", read_only=1),
    field("total_amount", "Currency", "Total Amount", options="currency", read_only=1, in_list_view=1),
    field("additional_salary", "Link", "Additional Salary", options="Additional Salary", read_only=1),
    field("items", "Table", "Piece Rate Entries", options="Piece Rate Summary Item", read_only=1),
    field("amended_from", "Link", "Amended From", options="Piece Rate Summary", read_only=1, no_copy=1),
], autoname="naming_series:", is_submittable=1, permissions=[
    dict(role=role, read=1, write=1, create=1, submit=1, cancel=1, amend=1, delete=1, report=1, export=1, print=1)
    for role in ("HR Manager", "System Manager")])

write("Piece Rate Summary Item", [
    field("job_card", "Link", "Job Card", options="Job Card", in_list_view=1),
    field("work_order", "Link", "Work Order", options="Work Order"),
    field("operation", "Link", "Operation", options="Operation", in_list_view=1),
    field("log_date", "Date", "Log Date"),
    field("completed_qty", "Float", "Completed Qty", in_list_view=1),
    field("rate", "Currency", "Piece Rate", in_list_view=1),
    field("rate_source", "Select", "Piece Rate Source", options="BOM Operation\nOperation\nNo Piece Rate"),
    field("amount", "Currency", "Amount", in_list_view=1),
], istable=1, permissions=[])
