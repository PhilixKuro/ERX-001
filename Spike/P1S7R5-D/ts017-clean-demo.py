"""Remove the exact earlier TS-010 browser fixture, using normal link validation."""
import frappe

assert frappe.local.site == "erx.localhost"
name = "_FCT_TS010_UI_1792088513074"
if frappe.db.exists("Item", name):
    assert not frappe.db.count("Stock Ledger Entry", {"item_code": name})
    batches = frappe.get_all("Batch", filters={"item": name}, pluck="name")
    print("Exact fixture batches:", batches, flush=True)
    for batch in batches:
        assert batch.startswith("_FCT-TS010-")
        frappe.delete_doc("Batch", batch)
    frappe.delete_doc("Item", name)
    frappe.db.commit()
assert frappe.db.count("Item") == 0
print("Exact TS-010 residue removed; Item, Batch and stock ledger checked")
