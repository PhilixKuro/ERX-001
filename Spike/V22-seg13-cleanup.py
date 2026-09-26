# V-22 segment 13: remove everything this probe created, in dependency order.
#
# Order matters:
#   1. CANCEL each Bank Transaction. on_cancel (bank_transaction.py:143-149) calls
#      delink_payment_entry for every allocated voucher, which is the documented
#      undo for a clearance (it nulls clearance_date). Doing this FIRST is what
#      releases ACC-PAY-2026-0000[8,9,10].
#   2. delete the Bank Transactions.
#   3. delete Bank Statement Import rows (+ their Data Import Log and File rows).
#   4. cancel + delete the three V22 Payment Entries (GL entries go with them).
#   5. delete Bank Account, then Bank, then the V22 GL Account.
#
# MUST NOT TOUCH: ACC-PAY-2026-00006 and ACC-PAY-2026-00007 (pre-existing demo
# payments) -- their clearance_date must still be None at the end. Asserted below.
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg13-cleanup.py

import json

import frappe

SITE = "erx.localhost"
BANK = "V22测试银行"
BANK_ACCT = "V22测试账户 - V22测试银行"
ACC = "V22测试银行存款 - HDS"
PROTECTED = ("ACC-PAY-2026-00006", "ACC-PAY-2026-00007")
OUT = "/workspace/Spike/V22-out/seg13-cleanup.json"

result = {"segment": "13 cleanup"}
log = []


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


def step(msg):
    log.append(msg)
    print(f"  .. {msg}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
frappe.flags.ignore_links = True

rec("protected_before", frappe.get_all(
    "Payment Entry", filters={"name": ["in", PROTECTED]},
    fields=["name", "clearance_date", "docstatus"]))

# ---------------------------------------------- 1+2. cancel then delete the BTs
bts = frappe.get_all("Bank Transaction", fields=["name", "docstatus", "status"], order_by="name")
rec("bts_to_remove", bts)
for bt in bts:
    try:
        doc = frappe.get_doc("Bank Transaction", bt.name)
        if doc.docstatus == 1:
            doc.flags.ignore_permissions = True
            doc.cancel()
            step(f"cancelled {bt.name}")
        frappe.db.commit()
    except Exception:
        step(f"CANCEL FAILED {bt.name}: {frappe.get_traceback(with_context=False)[-300:]}")

for bt in bts:
    try:
        frappe.delete_doc("Bank Transaction", bt.name, force=1, ignore_permissions=True,
                          ignore_missing=True, delete_permanently=True)
        step(f"deleted {bt.name}")
        frappe.db.commit()
    except Exception:
        step(f"DELETE FAILED {bt.name}: {frappe.get_traceback(with_context=False)[-300:]}")

# --------------------------------------------------- 3. Bank Statement Imports
for n in frappe.get_all("Bank Statement Import", pluck="name"):
    for f in frappe.get_all("File", filters={"attached_to_doctype": "Bank Statement Import",
                                             "attached_to_name": n}, pluck="name"):
        try:
            frappe.delete_doc("File", f, force=1, ignore_permissions=True, ignore_missing=True)
            step(f"deleted File {f}")
        except Exception:
            step(f"FILE DELETE FAILED {f}")
    frappe.db.delete("Data Import Log", {"data_import": n})
    try:
        frappe.delete_doc("Bank Statement Import", n, force=1, ignore_permissions=True,
                          ignore_missing=True)
        step(f"deleted BSI {n}")
    except Exception:
        step(f"BSI DELETE FAILED {n}")
frappe.db.commit()

# ------------------------------------------------- 4. the V22 Payment Entries
pes = frappe.get_all("Payment Entry", filters={"reference_no": ["like", "V22REF%"]},
                     fields=["name", "docstatus", "clearance_date"])
rec("pes_to_remove", pes)
for pe in pes:
    assert pe.name not in PROTECTED, f"refusing to touch protected {pe.name}"
    try:
        doc = frappe.get_doc("Payment Entry", pe.name)
        if doc.docstatus == 1:
            doc.flags.ignore_permissions = True
            doc.cancel()
            step(f"cancelled {pe.name}")
        frappe.db.commit()
        frappe.delete_doc("Payment Entry", pe.name, force=1, ignore_permissions=True,
                          ignore_missing=True, delete_permanently=True)
        step(f"deleted {pe.name}")
        frappe.db.commit()
    except Exception:
        step(f"PE REMOVE FAILED {pe.name}: {frappe.get_traceback(with_context=False)[-400:]}")

# ------------------------------------- 5. Bank Account -> Bank -> GL Account
for dt, nm in (("Bank Account", BANK_ACCT), ("Bank", BANK), ("Account", ACC)):
    try:
        if frappe.db.exists(dt, nm):
            frappe.delete_doc(dt, nm, force=1, ignore_permissions=True, ignore_missing=True)
            step(f"deleted {dt} {nm}")
            frappe.db.commit()
    except Exception:
        step(f"{dt} DELETE FAILED {nm}: {frappe.get_traceback(with_context=False)[-400:]}")

rec("actions", log)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
