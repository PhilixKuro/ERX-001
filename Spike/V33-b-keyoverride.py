"""V33 probe (b): the gl_dict key-override relationship.

Questions:
  - two methods write the SAME gl_dict key -> last wins / first wins / raise / merge?
  - what is the ordering rule, and how was it determined?
  - can a registered method overwrite a key CORE already set, or only add new keys?

Strategy: call the REAL AccountsController.get_gl_dict() on an UNSAVED, in-memory
Purchase Invoice. No insert, no submit, no commit -> zero rows written.
Includes a POSITIVE CONTROL: we first prove the harness can observe a successful
overwrite, so any "cannot overwrite" result is trustworthy.
"""

import inspect
import json
import os
import sys
import types

import frappe

OUT = "/workspace/Spike/V33-out"
RESULT = {"probe": "b", "steps": []}
ORDER = []


def rec(name, **kw):
    kw["step"] = name
    RESULT["steps"].append(kw)
    print("[%s] %s" % (name, json.dumps(kw, default=str, ensure_ascii=False)))


def reg(modname, funcname, marker, writes=None, raises=False, snapshot_keys=None):
    """Create an in-memory module exposing a hook function."""
    mod = sys.modules.get(modname) or types.ModuleType(modname)

    def fn(doc, gl_dict, _m=marker, _w=writes or {}, _r=raises, _s=snapshot_keys):
        entry = {"marker": _m}
        if _s:
            entry["saw"] = {k: gl_dict.get(k) for k in _s}
        ORDER.append(entry)
        if _r:
            raise ValueError("V33 deliberate failure from %s" % _m)
        for k, v in _w.items():
            gl_dict[k] = v

    setattr(mod, funcname, fn)
    sys.modules[modname] = mod
    return "%s.%s" % (modname, funcname)


class HookPatch:
    """Temporarily force the app-based hook list."""

    def __init__(self, methods):
        self.methods = methods

    def __enter__(self):
        self.orig = frappe.get_hooks

        def patched(hook=None, default="_KEEP_DEFAULT_LIST", app_name=None):
            if hook == "update_gl_dict_with_app_based_fields":
                return list(self.methods)
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

    # ---------- ordering rule: how is the hook list built? -----------------
    import frappe as _f

    rec("ordering_rule_source",
        load_app_hooks=inspect.getsource(_f._load_app_hooks),
        append_hook=inspect.getsource(_f.append_hook),
        installed_apps_in_order=_f.get_installed_apps(),
        note="append_hook uses list.extend in _load_app_hooks' app loop; "
             "so hook list order == get_installed_apps() order")

    # empirical check: pick a hook registered by BOTH apps and compare order
    both = []
    all_hooks = _f.get_hooks()
    for hk, val in all_hooks.items():
        if not isinstance(val, list) or len(val) < 2:
            continue
        roots = [str(v).split(".", 1)[0] for v in val if isinstance(v, str)]
        if "frappe" in roots and "erpnext" in roots:
            both.append({"hook": hk, "value": val,
                         "frappe_first": roots.index("frappe") < roots.index("erpnext")})
    rec("ordering_rule_empirical",
        hooks_registered_by_both_apps=both[:8],
        count=len(both),
        installed_order=_f.get_installed_apps())

    # ---------- build an in-memory Purchase Invoice (never saved) ----------
    acct_debit = frappe.db.get_value(
        "Account", {"company": company, "account_type": "Expense Account",
                    "is_group": 0}, "name")
    if not acct_debit:
        acct_debit = frappe.db.get_value(
            "Account", {"company": company, "is_group": 0}, "name")
    cc = frappe.db.get_value("Cost Center", {"company": company, "is_group": 0}, "name")
    comp_cur = frappe.get_cached_value("Company", company, "default_currency")
    rec("fixtures", company=company, account=acct_debit, cost_center=cc, currency=comp_cur)

    pi = frappe.new_doc("Purchase Invoice")
    pi.company = company
    pi.posting_date = "2026-06-15"
    pi.currency = comp_cur
    pi.conversion_rate = 1
    # NOTE: company_currency is a read-only property on the controller, not a field.
    pi.name = "V33-IN-MEMORY-NOT-SAVED"
    pi.remarks = "V33 core remark"

    base_args = {"account": acct_debit, "cost_center": cc,
                 "debit": 100, "debit_in_account_currency": 100}

    # ---------- 0. BASELINE: no hooks at all ------------------------------
    with HookPatch([]):
        del ORDER[:]
        base = pi.get_gl_dict(dict(base_args))
    baseline_keys = sorted(base.keys())
    rec("baseline_no_hooks", gl_dict=dict(base), keys=baseline_keys,
        hooks_ran=list(ORDER))

    # ---------- 1. POSITIVE CONTROL: hook CAN overwrite a core key --------
    # 'remarks' is set in the base literal (accounts_controller.py:1425) BEFORE
    # the hook at :1447, and is NOT in args -> a hook write must stick.
    h = reg("erpnext.v33_pc", "pc", "positive-control",
            writes={"remarks": "V33 OVERWRITTEN BY HOOK"},
            snapshot_keys=["remarks"])
    with HookPatch([h]):
        del ORDER[:]
        g = pi.get_gl_dict(dict(base_args))
    rec("positive_control_overwrite_core_key",
        key="remarks",
        core_value_before_hook=ORDER[0]["saw"]["remarks"] if ORDER else None,
        value_after=g.get("remarks"),
        overwrite_succeeded=(g.get("remarks") == "V33 OVERWRITTEN BY HOOK"),
        note="proves the instrument can SEE an overwrite; negatives below are meaningful")

    # ---------- 2. TWO methods write the SAME NEW key ---------------------
    h1 = reg("erpnext.v33_c1", "c1", "c1", writes={"v33_shared": "FROM_C1", "v33_only_1": 1},
             snapshot_keys=["v33_shared"])
    h2 = reg("erpnext.v33_c2", "c2", "c2", writes={"v33_shared": "FROM_C2", "v33_only_2": 2},
             snapshot_keys=["v33_shared"])
    with HookPatch([h1, h2]):
        del ORDER[:]
        g12 = pi.get_gl_dict(dict(base_args))
    with HookPatch([h2, h1]):
        del ORDER[:]
        g21 = pi.get_gl_dict(dict(base_args))
        order21 = list(ORDER)
    rec("two_methods_same_new_key",
        order_c1_then_c2={"final": g12.get("v33_shared"),
                          "both_keys_present": ("v33_only_1" in g12 and "v33_only_2" in g12)},
        order_c2_then_c1={"final": g21.get("v33_shared"),
                          "second_saw_first_value": order21[1]["saw"]["v33_shared"] if len(order21) > 1 else None},
        last_writer_wins=(g12.get("v33_shared") == "FROM_C2"
                          and g21.get("v33_shared") == "FROM_C1"),
        raised=False, silent=True,
        note="no exception, no merge: plain dict assignment, later call overwrites")

    # ---------- 3. can a hook overwrite a key passed via args? ------------
    # gl_dict.update(args) runs at accounts_controller.py:1461, AFTER the hook.
    h3 = reg("erpnext.v33_args", "a", "args-fighter",
             writes={"account": "V33-HOOK-ACCOUNT", "debit": 999999,
                     "cost_center": "V33-HOOK-CC"},
             snapshot_keys=["account", "debit"])
    with HookPatch([h3]):
        del ORDER[:]
        ga = pi.get_gl_dict(dict(base_args))
    rec("hook_vs_args_keys",
        hook_saw={"account": ORDER[0]["saw"]["account"] if ORDER else None,
                  "debit": ORDER[0]["saw"]["debit"] if ORDER else None},
        final_account=ga.get("account"),
        final_debit=ga.get("debit"),
        hook_write_survived_account=(ga.get("account") == "V33-HOOK-ACCOUNT"),
        hook_write_survived_debit=(ga.get("debit") == 999999),
        mechanism="gl_dict.update(args) at accounts_controller.py:1461 runs after hook at :1447")

    # ---------- 4. derived keys recomputed after the hook -----------------
    h4 = reg("erpnext.v33_derived", "d", "derived-fighter",
             writes={"debit_in_account_currency": 777777,
                     "fiscal_year": "V33-FAKE-FY",
                     "voucher_subtype": "V33-SUBTYPE",
                     "is_opening": "V33-OPEN",
                     "project": "V33-PROJ"})
    with HookPatch([h4]):
        del ORDER[:]
        gd = pi.get_gl_dict(dict(base_args))
    survived = {}
    for k, want in [("debit_in_account_currency", 777777), ("fiscal_year", "V33-FAKE-FY"),
                    ("voucher_subtype", "V33-SUBTYPE"), ("is_opening", "V33-OPEN"),
                    ("project", "V33-PROJ")]:
        survived[k] = {"final": gd.get(k), "survived": gd.get(k) == want}
    rec("core_key_overwrite_matrix", results=survived,
        note="keys set in the base literal before :1447 survive; "
             "keys in args or recomputed later do not")

    # ---------- 5. new keys reaching the DB layer? ------------------------
    # does a foreign key survive into a GL Entry doc, or get dropped/raise?
    h5 = reg("erpnext.v33_new", "n", "newkey",
             writes={"v33_custom_vat_side": "INPUT", "v33_unknown_col": "X"})
    with HookPatch([h5]):
        del ORDER[:]
        gn = pi.get_gl_dict(dict(base_args))
    gl_meta_fields = set(f.fieldname for f in frappe.get_meta("GL Entry").fields)
    rec("new_keys_vs_gl_entry_schema",
        new_keys_in_gl_dict=[k for k in gn.keys() if k.startswith("v33_")],
        gl_entry_has_field_v33_custom_vat_side=("v33_custom_vat_side" in gl_meta_fields),
        gl_entry_field_count=len(gl_meta_fields),
        note="hook can put ANY key in the dict; persistence needs a real GL Entry custom field")

    # ---------- 6. does a raising hook abort GL assembly? -----------------
    h6a = reg("erpnext.v33_ok", "ok", "ok-before", writes={"v33_before_raise": 1})
    h6b = reg("erpnext.v33_boom", "boom", "raiser", raises=True)
    h6c = reg("erpnext.v33_after", "af", "after-raise", writes={"v33_after_raise": 1})
    with HookPatch([h6a, h6b, h6c]):
        del ORDER[:]
        caught = None
        try:
            pi.get_gl_dict(dict(base_args))
        except Exception as e:
            caught = "%s: %s" % (type(e).__name__, e)
    rec("raising_hook_aborts",
        exception=caught,
        markers_ran=[o["marker"] for o in ORDER],
        later_hook_skipped=("after-raise" not in [o["marker"] for o in ORDER]),
        note="dispatcher has no try/except -> one bad app breaks all GL assembly")

    # ---------- 7. is the hook inside temporary_flag('company')? ----------
    h7 = reg("erpnext.v33_flag", "f", "flagcheck", writes={})

    seen_flag = {}

    def flagfn(doc, gl_dict):
        seen_flag["company_flag"] = frappe.local.flags.get("company")
        seen_flag["region"] = __import__("erpnext").get_region()

    sys.modules["erpnext.v33_flag"].f = flagfn
    with HookPatch([h7]):
        del ORDER[:]
        pi.get_gl_dict(dict(base_args))
    rec("company_flag_visibility_inside_hook",
        observed=seen_flag,
        note="regional twin is wrapped in temporary_flag('company') at :1444-1445; "
             "app-based hook at :1447 is OUTSIDE that block")

    err_after = frappe.db.count("Error Log")
    rec("error_log_after", rows=err_after, delta=err_after - err_before)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "b-keyoverride.json"), "w", encoding="utf-8") as fh:
        json.dump(RESULT, fh, indent=2, ensure_ascii=False, default=str)
    print("WROTE", os.path.join(OUT, "b-keyoverride.json"))


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
