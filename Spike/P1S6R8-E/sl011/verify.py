"""SL-011 E 核对：不 import frappe，以桩模块载入真实 test_translation_quality.py，对当前 zh.csv 跑四守卫与覆盖清单核对。"""
from __future__ import annotations

import ast
import csv
import gettext
import importlib.util
import json
import re
import sys
import types
import unittest
from pathlib import Path

PROJECT = Path(r"D:\ERX-001")
BENCH = PROJECT / "frappe-bench"
APP = BENCH / "apps/frappe_china/frappe_china"
TESTS = APP / "tests"
OUT = Path(__file__).with_name("verify-out.json")
OFFICIAL_APPS = ("frappe", "erpnext", "crm", "hrms", "insights", "raven")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def extract_assign(path, name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return node.value
    raise KeyError(name)


def install_stubs(quality_path=TESTS / "test_translation_quality.py"):
    frappe = types.ModuleType("frappe")
    frappe.get_app_path = lambda app, *parts: str(BENCH / "apps" / app / app / Path(*parts))
    sys.modules["frappe"] = frappe
    for name in ("frappe_china", "frappe_china.tests"):
        sys.modules[name] = types.ModuleType(name)
    tt = types.ModuleType("frappe_china.tests.test_translations")
    node = extract_assign(TESTS / "test_translations.py", "_PLACEHOLDER")
    tt._PLACEHOLDER = eval(compile(ast.Expression(node), "x", "eval"), {"re": re})
    sys.modules["frappe_china.tests.test_translations"] = tt
    utils = types.ModuleType("frappe_china.tests.utils")
    utils.FrappeChinaTestCase = unittest.TestCase
    sys.modules["frappe_china.tests.utils"] = utils
    load("frappe_china.tests.translation_whitelist", TESTS / "translation_whitelist.py")
    return load("frappe_china.tests.test_translation_quality", quality_path)


def frappe_strip(value):
    # frappe.utils.strip(val, chars=None): 去首尾空白与 \ufeff 等；此处按 str.strip 近似并记录差异风险
    return value.strip()


def csv_dict(path):
    result = {}
    with open(path, encoding="utf-8", newline="") as handle:
        for item in csv.reader(handle):
            if len(item) in (2, 3):
                src, tgt = item[0].replace("\\n", "\n"), item[1].replace("\\n", "\n")
                key = src + ":" + item[2] if len(item) == 3 and item[2] else src
                result[key] = frappe_strip(tgt)
    return result


def mo_dict(app):
    path = BENCH / "sites/assets/locale/zh/LC_MESSAGES" / f"{app}.mo"
    if not path.exists():
        return None
    with open(path, "rb") as handle:
        catalog = gettext.GNUTranslations(handle)._catalog
    result = {}
    for key, value in catalog.items():
        if isinstance(key, tuple):
            key = key[0]
            if key in result:
                continue
        if not key:
            continue
        if "\x04" in key:
            ctx, mid = key.split("\x04", 1)
            result[f"{mid}:{ctx}"] = value
        else:
            result[key] = value
    return result


def po_dict(baseline, app):
    result = {}
    for entry in baseline.parse_po(BENCH / "apps" / app / app / "locale/zh.po"):
        if entry["str"]:
            result[baseline.entry_key(entry)] = entry["str"]
    return result


def main():
    report = {}
    q = install_stubs()
    rows = q.csv_rows()
    report["csv_rows"] = len(rows)
    report["full_table"] = {g.__name__: g(rows) for g in q.GUARDS}
    report["full_table_counts"] = {k: len(v) for k, v in report["full_table"].items()}

    # 运行真实 TestTranslationQuality（9 用例）
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(q.TestTranslationQuality)
    result = unittest.TextTestRunner(stream=open(Path(__file__).with_name("quality-unittest.txt"), "w", encoding="utf-8"), verbosity=2).run(suite)
    report["quality_unittest"] = {"run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors)}

    # 自构坏行判别力
    bad = {
        "find_traditional": [["Bank Account", "銀行帳戶"], ["Settings", "設定"], ["Report", "報表"]],
        "find_placeholder": [["Customer", "中文：客户"], ["Name", "名称???"], ["X", "  中文：X"]],
        "find_word_by_word": [["Save the document", "保存 the 文档"], ["Add to Cart", "添加 到 购物车"], ["Go", "前往 for 设置"]],
        "find_mixed": [["Create Invoice", "创建 Invoice"], ["Delivery Note", "发货Note"], ["Sync Leads", "同步 leads"]],
    }
    good = [["Export PDF", "导出 PDF"], ["Row {0}", "第 {0} 行"], ["Account", "账户"], ["Raven Bot", "Raven 机器人"], ["Hello {name}", "你好 {name}"], ["<b>Note</b>", "<b>注意</b>"]]
    report["self_bad"] = {g: {"hits": len(getattr(q, g)(r)), "of": len(r), "reported": getattr(q, g)(r)} for g, r in bad.items()}
    report["self_good"] = q.guard_problems(good)

    # 理由非空
    wl = sys.modules["frappe_china.tests.translation_whitelist"]
    report["table_sizes"] = {"QUALITY_EXCEPTIONS": len(q.QUALITY_EXCEPTIONS), "UNTRANSLATED": len(wl.UNTRANSLATED), "ALLOW": len(q.ALLOW)}
    report["empty_reasons"] = {n: [k for k, v in t.items() if not str(v).strip()] for n, t in
                               (("QUALITY_EXCEPTIONS", q.QUALITY_EXCEPTIONS), ("UNTRANSLATED", wl.UNTRANSLATED), ("ALLOW", q.ALLOW))}
    csvd = csv_dict(TESTS.parent / "translations/zh.csv")
    report["qe_keys_not_in_csv"] = sorted(set(q.QUALITY_EXCEPTIONS) - set(csvd))
    # 每条 QUALITY_EXCEPTIONS 实际命中哪道守卫（若不命中任何守卫，例外是多余的）
    q_saved = dict(q.QUALITY_EXCEPTIONS)
    q.QUALITY_EXCEPTIONS.clear()
    qe_hits = {}
    for key in q_saved:
        if key in csvd:
            src = key
            row = [src, csvd[key]]
            qe_hits[key] = {"ours": csvd[key], "guards": [g.__name__ for g in q.GUARDS if g([row])]}
    q.QUALITY_EXCEPTIONS.update(q_saved)
    report["qe_hits"] = qe_hits
    # ALLOW 每项在 csv 译文里被使用次数
    allow_use = {}
    for word in q.ALLOW:
        pat = re.compile(r"(?<![A-Za-z0-9])" + re.escape(word) + r"(?![A-Za-z0-9])")
        allow_use[word] = sum(1 for v in csvd.values() if q._CJK.search(v) and pat.search(v))
    report["allow_use"] = allow_use

    # 覆盖清单
    ov = load("frappe_china.tests.translation_overrides", TESTS / "translation_overrides.py").OVERRIDES
    basis_node = extract_assign(TESTS / "test_translations.py", "_BASIS_FORM")
    basis_form = eval(compile(ast.Expression(basis_node), "x", "eval"), {"re": re})
    report["overrides_count"] = len(ov)
    report["bad_basis"] = sorted(k for k, o in ov.items() if not basis_form.match(o.basis))
    report["basis_prefix_counts"] = {}
    for k, o in ov.items():
        m = basis_form.match(o.basis)
        p = m.group(1) if m else "BAD"
        report["basis_prefix_counts"][p] = report["basis_prefix_counts"].get(p, 0) + 1
    report["own_source_basis"] = sorted(k for k, o in ov.items() if o.basis.startswith("本 app 自有源词"))
    report["ours_guard_problems"] = q.guard_problems([[k, o.ours] for k, o in ov.items()])
    report["ours_ne_csv"] = sorted(k for k, o in ov.items() if csvd.get(k) != o.ours)

    baseline = load("baseline", PROJECT / "Spike/P1S6R4-baseline.py")
    official_mo, official_po = {}, {}
    mo_missing = []
    for app in OFFICIAL_APPS:
        m = mo_dict(app)
        if m is None:
            mo_missing.append(app)
        else:
            official_mo.update(m)
        official_po.update(po_dict(baseline, app))
    report["mo_missing_apps"] = mo_missing
    report["official_sizes"] = {"mo": len(official_mo), "po": len(official_po)}
    for label, official in (("mo", official_mo), ("po", official_po)):
        inter = set(csvd) & set(official)
        report[f"intersection_{label}"] = {
            "size": len(inter),
            "extra(inter-OVERRIDES)": sorted(inter - set(ov)),
            "missing(OVERRIDES-inter)": sorted(set(ov) - inter),
        }
    report["official_mismatch_mo"] = sorted(k for k, o in ov.items() if official_mo.get(k) != o.official)
    report["mo_vs_po_keydiff"] = {"mo-po": len(set(official_mo) - set(official_po)), "po-mo": len(set(official_po) - set(official_mo))}
    # context 列：csv 中带 context 的行及其是否与官方相交
    ctx_keys = []
    with open(TESTS.parent / "translations/zh.csv", encoding="utf-8", newline="") as handle:
        for item in csv.reader(handle):
            if len(item) == 3 and item[2]:
                ctx_keys.append(item[0] + ":" + item[2])
    report["csv_context_rows"] = len(ctx_keys)
    report["csv_context_in_official"] = sorted(k for k in ctx_keys if k in official_mo)
    report["csv_context_plain_in_official"] = sorted(k for k in ctx_keys if k.rsplit(":", 1)[0] in official_mo and k not in official_mo)[:40]
    report["overrides_basis"] = {k: o.basis for k, o in ov.items()}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    brief = {k: v for k, v in report.items() if k not in ("full_table", "qe_hits", "overrides_basis", "self_bad")}
    print(json.dumps(brief, ensure_ascii=False, indent=1))
    print(json.dumps({g: {"hits": d["hits"], "of": d["of"]} for g, d in report["self_bad"].items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
