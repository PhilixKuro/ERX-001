"""V33 probe (a): mechanics of update_gl_dict_with_app_based_fields.

Verdict targets:
  - does it iterate ALL registered methods, or take [-1]?
  - is there any country/region gating?
  - does registering it consume the regional_overrides slot?
  - who are the internal users (apps registering against it)?
  - verified count of @allow_regional occurrences.

Read-only. No document is saved. Still wrapped in rollback for safety.
"""

import ast
import inspect
import json
import os
import sys
import types

import frappe

OUT = "/workspace/Spike/V33-out"
RESULT = {"probe": "a", "steps": []}


def rec(name, **kw):
    kw["step"] = name
    RESULT["steps"].append(kw)
    print("[%s] %s" % (name, json.dumps(kw, default=str, ensure_ascii=False)))


def make_fake_app_module(modname, funcname, marker, keys):
    """Register a fake module in sys.modules so frappe.get_attr can resolve it."""
    mod = types.ModuleType(modname)

    def fn(doc, gl_dict, _marker=marker, _keys=keys):
        ORDER.append(_marker)
        for k, v in _keys.items():
            gl_dict[k] = v

    setattr(mod, funcname, fn)
    sys.modules[modname] = mod
    return "%s.%s" % (modname, funcname)


ORDER = []


def main():
    frappe.init(site="erx.localhost")
    frappe.connect()

    from erpnext.controllers import accounts_controller as ac

    # ---- 1. internal users on the REAL site -------------------------------
    real = frappe.get_hooks("update_gl_dict_with_app_based_fields", default=[])
    rec("real_registered_methods", value=list(real), count=len(real),
        installed_apps=frappe.get_installed_apps())

    # ---- 2. source of the dispatcher (code reading, labelled as such) -----
    src = inspect.getsource(ac.update_gl_dict_with_app_based_fields)
    rec("dispatcher_source", source=src,
        has_minus_one="[-1]" in src,
        mentions_country=("country" in src.lower() or "region" in src.lower()))

    # ---- 3. is it wrapped by allow_regional? ------------------------------
    fn = ac.update_gl_dict_with_app_based_fields
    rec("dispatcher_is_allow_regional_wrapped",
        has_wrapped_attr=hasattr(fn, "__wrapped__"),
        qualname=fn.__qualname__,
        module=fn.__module__)

    # compare with a known allow_regional function
    rfn = ac.update_gl_dict_with_regional_fields
    rec("regional_twin_is_wrapped",
        has_wrapped_attr=hasattr(rfn, "__wrapped__"),
        qualname=rfn.__qualname__)

    # ---- 4. does the name appear anywhere in regional_overrides? ----------
    ro = frappe.get_hooks("regional_overrides", {})
    flat = []
    for country, mapping in (ro or {}).items():
        if isinstance(mapping, dict):
            for k, v in mapping.items():
                flat.append({"country": country, "slot": k, "impl": v})
    rec("regional_overrides_table", countries=sorted((ro or {}).keys()),
        entry_count=len(flat), entries=flat,
        app_based_hook_appears_as_slot=any(
            "update_gl_dict_with_app_based_fields" in e["slot"] for e in flat),
        china_present=("China" in (ro or {})))

    # ---- 5. RUNTIME: register 3 competing methods, observe iteration ------
    # NOTE: frappe.get_attr (frappe/__init__.py:1130) rejects a method string
    # whose FIRST dotted segment is not an installed app. So fake modules must
    # be rooted under an installed app namespace (erpnext.*), not a novel one.
    m1 = make_fake_app_module("erpnext.v33_fake_one", "hook_one", "one", {"v33_one": 1})
    m2 = make_fake_app_module("erpnext.v33_fake_two", "hook_two", "two", {"v33_two": 2})
    m3 = make_fake_app_module("erpnext.v33_fake_three", "hook_three", "three", {"v33_three": 3})
    injected = [m1, m2, m3]
    rec("get_attr_app_name_gate",
        note="method string root segment must be an installed app",
        installed=frappe.get_installed_apps(),
        using_namespace="erpnext.*")

    orig_get_hooks = frappe.get_hooks

    def patched(hook=None, default="_KEEP_DEFAULT_LIST", app_name=None):
        if hook == "update_gl_dict_with_app_based_fields":
            return list(injected)
        return orig_get_hooks(hook, default, app_name) if hook is not None else orig_get_hooks()

    frappe.get_hooks = patched
    try:
        del ORDER[:]
        gl = frappe._dict({"company": "SENTINEL", "debit": 0})
        ac.update_gl_dict_with_app_based_fields(None, gl)
        rec("runtime_all_methods_ran",
            registered=injected,
            execution_order=list(ORDER),
            ran_count=len(ORDER),
            all_three_ran=(len(ORDER) == 3),
            only_last_ran=(ORDER == ["three"]),
            gl_dict_after=dict(gl))

        # ---- 6. region independence: same call under 3 different regions --
        per_region = {}
        for country in ["China", "United Arab Emirates", "India", "France"]:
            del ORDER[:]
            gl2 = frappe._dict({})
            frappe.flags.company = None
            frappe.local.flags.company = None
            frappe.flags.country = country
            ac.update_gl_dict_with_app_based_fields(None, gl2)
            per_region[country] = {"ran": list(ORDER), "gl_keys": sorted(gl2.keys())}
        rec("runtime_region_gating", per_region=per_region,
            identical_across_regions=(len(set(
                json.dumps(v, sort_keys=True) for v in per_region.values())) == 1))
    finally:
        frappe.get_hooks = orig_get_hooks
        frappe.flags.country = None
        for m in ["erpnext.v33_fake_one", "erpnext.v33_fake_two", "erpnext.v33_fake_three"]:
            sys.modules.pop(m, None)

    # ---- 7. NEGATIVE CONTROL: the regional twin DOES take [-1] -----------
    # register two impls for the same regional slot, observe only one runs.
    n1 = make_fake_app_module("erpnext.v33_reg_one", "impl", "reg-one", {"v33_reg": "one"})
    n2 = make_fake_app_module("erpnext.v33_reg_two", "impl", "reg-two", {"v33_reg": "two"})
    slot = "erpnext.controllers.accounts_controller.update_gl_dict_with_regional_fields"
    orig_get_hooks2 = frappe.get_hooks

    def patched2(hook=None, default="_KEEP_DEFAULT_LIST", app_name=None):
        if hook == "regional_overrides":
            return {"China": {slot: [n1, n2]}}
        return orig_get_hooks2(hook, default, app_name) if hook is not None else orig_get_hooks2()

    frappe.get_hooks = patched2
    try:
        del ORDER[:]
        frappe.flags.company = None
        frappe.local.flags.company = None
        frappe.flags.country = "China"
        gl3 = frappe._dict({})
        ac.update_gl_dict_with_regional_fields(None, gl3)
        rec("regional_slot_takes_last_only",
            registered=[n1, n2],
            execution_order=list(ORDER),
            ran_count=len(ORDER),
            gl_dict_after=dict(gl3),
            only_last_ran=(ORDER == ["reg-two"]))
    finally:
        frappe.get_hooks = orig_get_hooks2
        frappe.flags.country = None
        sys.modules.pop("erpnext.v33_reg_one", None)
        sys.modules.pop("erpnext.v33_reg_two", None)

    # ---- 8. count @allow_regional by AST over the real tree ---------------
    root = "/workspace/frappe-bench/apps/erpnext/erpnext"
    hits = []
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(dirpath, f)
            try:
                tree = ast.parse(open(p, encoding="utf-8").read())
            except Exception:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for d in node.decorator_list:
                    nm = None
                    if isinstance(d, ast.Attribute):
                        nm = d.attr
                    elif isinstance(d, ast.Name):
                        nm = d.id
                    if nm == "allow_regional":
                        hits.append({
                            "file": p.replace(root, "erpnext"),
                            "line": node.lineno,
                            "func": node.name,
                            "is_test": ("/tests/" in p or f.startswith("test_")),
                        })
    prod = [h for h in hits if not h["is_test"]]
    gl_stage = [h for h in prod if h["func"] in (
        "make_regional_gl_entries", "update_regional_gl_entries",
        "add_regional_gl_entries", "update_gl_dict_with_regional_fields")]
    rec("allow_regional_ast_count",
        total_decorated=len(hits),
        production_decorated=len(prod),
        test_decorated=len(hits) - len(prod),
        gl_assembly_stage_count=len(gl_stage),
        gl_assembly_stage=gl_stage,
        production_list=prod)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "a-hookmechanics.json"), "w", encoding="utf-8") as fh:
        json.dump(RESULT, fh, indent=2, ensure_ascii=False, default=str)
    print("WROTE", os.path.join(OUT, "a-hookmechanics.json"))


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            frappe.db.rollback()
            print("ROLLED BACK")
        except Exception as e:
            print("rollback skipped:", e)
        frappe.destroy()
