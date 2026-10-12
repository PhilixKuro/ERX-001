import frappe
def run():
    print(frappe.get_all("Salutation", pluck="name"))
    for dt, f in [("Contact","salutation"),("Lead","salutation"),("Employee","salutation"),("CRM Lead","salutation")]:
        try:
            print(dt, frappe.db.sql(f"select {f}, count(*) from `tab{dt}` group by {f}"))
        except Exception as e:
            print(dt, "ERR", e)
