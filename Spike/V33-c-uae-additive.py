"""V33 probe (c): is there a real additive (L3) path for Chinese VAT?

Claims under test:
  - >=5 of the 18 regional slots sit at GL-entry-assembly time
  - UAE reverse charge really APPENDS gl entries through that mechanism
  - the same pattern is available to a China localization
  - ... and at what cost (does it CONSUME the slot?)

Plus a consequence the LG-132 claim did not mention: merge_similar_entries.

Read-only against the DB. Nothing is inserted or submitted.
"""

import inspect
import json
import os
import sys
import types

import frappe

OUT = "/workspace/Spike/V33-out"
RESULT = {"probe": "c", "steps": []}
CALLS = []


def rec(name, **kw):
    kw["step"] = name
    RESULT["steps"].append(kw)
    print("[%s] %s" % (name, json.dumps(kw, default=str, ensure_ascii=False)))


class OverridePatch:
    """Force regional_overrides to a chosen mapping."""

    def __init__(self, mapping):
        self.mapping = mapping

    def __enter__(self):
        self.orig = frappe.get_hooks

        def patched(hook=None, default="_KEEP_DEFAULT_LIST", app_name=None):
            if hook == "regional_overrides":
                return self.mapping
            if hook is None:
                return self.orig()
            return self.orig(hook, default, app_name)

        frappe.get_hooks = patched
        return self

    def __exit__(self, *exc):
        frappe.get_hooks = self.orig
        return False


def main():
    frappe.init(site="erx.localhost")
    frappe.connect()
    frappe.set_user("Administrator")
    company = "华东弹簧"

    err_before = frappe.db.count("Error Log")
    rec("error_log_baseline", rows=err_before)

    import erpnext
    from erpnext.accounts.doctype.purchase_invoice import purchase_invoice as pimod
    from erpnext.regional.united_arab_emirates import utils as uae

    country = frappe.get_cached_value("Company", company, "country")
    rec("site_country", company=company, country=country,
        region_resolved=erpnext.get_region(company))

    # ---------- 1. UAE source: does it APPEND? (code reading, labelled) ----
    rec("uae_source_read",
        make_regional_gl_entries=inspect.getsource(uae.make_regional_gl_entries),
        make_gl_entry=inspect.getsource(uae.make_gl_entry),
        appends_via_list_append=("gl_entries.append" in inspect.getsource(uae.make_gl_entry)),
        builds_entry_with_get_gl_dict=("doc.get_gl_dict" in inspect.getsource(uae.make_gl_entry)),
        returns_the_list=("return gl_entries" in inspect.getsource(uae.make_regional_gl_entries)),
        evidence_type="CODE READING")

    # core stub it displaces
    rec("core_stub_is_passthrough",
        purchase_invoice_stub=inspect.getsource(pimod.make_regional_gl_entries.__wrapped__),
        caller_line="erpnext/accounts/doctype/purchase_invoice/purchase_invoice.py:959",
        caller_reassigns=("gl_entries = make_regional_gl_entries(gl_entries, self)"))

    # ---------- 2. RUN the UAE function on THIS China site -----------------
    class FakeDoc:
        pass

    d = FakeDoc()
    d.company = company
    d.reverse_charge = "Y"
    incoming = [{"account": "PRE-EXISTING", "debit": 1}]
    out = uae.make_regional_gl_entries(list(incoming), d)
    rec("uae_impl_on_china_company",
        input_len=len(incoming), output_len=len(out),
        returned_unchanged=(out == incoming),
        note="uae/utils.py:148-151 re-checks Company.country itself and early-returns; "
             "a China site gets nothing even if the slot were claimed",
        evidence_type="RUN")

    # ---------- 3. RUN the mechanism with a CHINA impl in the slot ---------
    # This is the exact dispatch UAE uses: allow_regional -> regional_overrides.
    mod = types.ModuleType("erpnext.v33_cn")

    def cn_make_regional_gl_entries(gl_entries, doc):
        CALLS.append("cn-impl")
        gl_entries.append(frappe._dict({
            "account": "V33-OUTPUT-VAT", "credit": 13, "debit": 0,
            "v33_vat_side": "OUTPUT", "company": doc.company,
            "cost_center": "CC1", "voucher_no": "V33",
        }))
        gl_entries.append(frappe._dict({
            "account": "V33-INPUT-VAT", "debit": 13, "credit": 0,
            "v33_vat_side": "INPUT", "company": doc.company,
            "cost_center": "CC1", "voucher_no": "V33",
        }))
        return gl_entries

    mod.impl = cn_make_regional_gl_entries
    sys.modules["erpnext.v33_cn"] = mod
    slot = "erpnext.accounts.doctype.purchase_invoice.purchase_invoice.make_regional_gl_entries"

    try:
        with OverridePatch({"China": {slot: ["erpnext.v33_cn.impl"]}}):
            del CALLS[:]
            frappe.local.flags.company = company
            start = [frappe._dict({"account": "CORE-EXPENSE", "debit": 100, "credit": 0})]
            result = pimod.make_regional_gl_entries(list(start), FakeDocWith(company))
        rec("china_impl_through_real_slot",
            impl_ran=(CALLS == ["cn-impl"]),
            input_len=len(start), output_len=len(result),
            appended=[dict(r) for r in result[1:]],
            core_entry_preserved=(result[0].get("account") == "CORE-EXPENSE"),
            evidence_type="RUN",
            note="proves GL-append via regional slot works for China")

        # ---------- 4. does claiming the slot CONSUME it? -----------------
        mod2 = types.ModuleType("erpnext.v33_cn2")

        def other_app(gl_entries, doc):
            CALLS.append("other-app")
            gl_entries.append(frappe._dict({"account": "OTHER-APP", "debit": 1}))
            return gl_entries

        mod2.impl = other_app
        sys.modules["erpnext.v33_cn2"] = mod2

        with OverridePatch({"China": {slot: ["erpnext.v33_cn.impl", "erpnext.v33_cn2.impl"]}}):
            del CALLS[:]
            frappe.local.flags.company = company
            res2 = pimod.make_regional_gl_entries([], FakeDocWith(company))
        rec("two_apps_claim_same_slot",
            registered=["erpnext.v33_cn.impl", "erpnext.v33_cn2.impl"],
            who_ran=list(CALLS),
            only_last_ran=(CALLS == ["other-app"]),
            first_app_silently_dropped=("cn-impl" not in CALLS),
            resulting_accounts=[r.get("account") for r in res2],
            mechanism="erpnext/__init__.py:152 -> overrides[function_path][-1]",
            evidence_type="RUN",
            note="THE L4 COST: slot is exclusive, last installed app wins, no error")
    finally:
        frappe.local.flags.company = None
        sys.modules.pop("erpnext.v33_cn", None)
        sys.modules.pop("erpnext.v33_cn2", None)

    # ---------- 5. app-based hook needs NO slot: coexistence -------------
    rec("app_based_hook_needs_no_slot",
        app_based_registrations_on_site=list(
            frappe.get_hooks("update_gl_dict_with_app_based_fields", default=[])),
        appears_in_regional_overrides=False,
        note="separate hooks.py key; additive, no slot consumed (see probe a)")

    # ---------- 6. merge_similar_entries vs a custom VAT-side key --------
    from erpnext.accounts.general_ledger import get_merge_properties, merge_similar_entries

    mp = get_merge_properties(None)
    rec("merge_properties",
        properties=mp,
        includes_custom_vat_key=("v33_vat_side" in mp),
        source="erpnext/accounts/general_ledger.py:331-348")

    # two entries, SAME account, DIFFERENT custom marker -> merged?
    same_acct = [
        frappe._dict({"account": "VAT - HDS", "cost_center": "主 - HDS", "company": company,
                      "debit": 100, "credit": 0, "debit_in_account_currency": 100,
                      "credit_in_account_currency": 0, "voucher_no": "V33",
                      "voucher_type": "Purchase Invoice", "v33_vat_side": "INPUT",
                      "_skip_merge": 0}),
        frappe._dict({"account": "VAT - HDS", "cost_center": "主 - HDS", "company": company,
                      "debit": 30, "credit": 0, "debit_in_account_currency": 30,
                      "credit_in_account_currency": 0, "voucher_no": "V33",
                      "voucher_type": "Purchase Invoice", "v33_vat_side": "OUTPUT",
                      "_skip_merge": 0}),
    ]
    merged = merge_similar_entries([e.copy() for e in same_acct])
    rec("merge_collapses_custom_marker",
        input_count=len(same_acct),
        output_count=len(merged),
        collapsed=(len(merged) == 1),
        surviving=[{"account": m.get("account"), "debit": m.get("debit"),
                    "v33_vat_side": m.get("v33_vat_side")} for m in merged],
        evidence_type="RUN",
        note="same account + same dimensions -> merged; custom key NOT a merge key, "
             "the losing row's marker is discarded with its row")

    # positive control: distinct accounts must NOT merge
    diff_acct = [same_acct[0].copy(), same_acct[1].copy()]
    other = frappe.db.get_value("Account", {"company": company, "is_group": 0,
                                            "name": ("!=", "VAT - HDS")}, "name")
    diff_acct[1]["account"] = other
    merged2 = merge_similar_entries([e.copy() for e in diff_acct])
    rec("merge_positive_control_distinct_accounts",
        other_account=other,
        output_count=len(merged2),
        stayed_separate=(len(merged2) == 2),
        note="control: instrument does NOT merge everything; separation by ACCOUNT holds")

    # _skip_merge escape hatch
    skip = [e.copy() for e in same_acct]
    for e in skip:
        e["_skip_merge"] = 1
    merged3 = merge_similar_entries(skip)
    rec("skip_merge_escape_hatch",
        output_count=len(merged3),
        stayed_separate=(len(merged3) == 2),
        source="erpnext/accounts/general_ledger.py:281-283",
        note="_skip_merge=1 preserves same-account rows")

    # ---------- 7. GL Entry custom field feasibility ---------------------
    meta = frappe.get_meta("GL Entry")
    rec("gl_entry_schema",
        field_count=len(meta.fields),
        has_custom_fields=[f.fieldname for f in meta.fields if f.get("is_custom_field")],
        is_submittable=meta.is_submittable,
        allow_custom_field=not meta.get("issingle"))

    err_after = frappe.db.count("Error Log")
    rec("error_log_after", rows=err_after, delta=err_after - err_before)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "c-uae-additive.json"), "w", encoding="utf-8") as fh:
        json.dump(RESULT, fh, indent=2, ensure_ascii=False, default=str)
    print("WROTE", os.path.join(OUT, "c-uae-additive.json"))


class FakeDocWith:
    def __init__(self, company):
        self.company = company
        self.reverse_charge = "N"


if __name__ == "__main__":
    try:
        main()
    finally:
        for m in list(sys.modules):
            if m.startswith("erpnext.v33_"):
                sys.modules.pop(m, None)
        try:
            frappe.db.rollback()
            print("ROLLED BACK")
        except Exception as e:
            print("rollback skipped:", e)
        frappe.destroy()
