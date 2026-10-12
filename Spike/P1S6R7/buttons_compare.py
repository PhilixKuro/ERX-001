"""TS-020 第 5 步：抽检表定稿列与合并字典逐词比对（容器内 env/bin/python 跑，clear-cache 后经站点合并字典取值）。
输出 Spike/P1S6R7/buttons/compare.json；不一致即非 0 退出。"""
import json, os, sys
os.chdir("/workspace/frappe-bench/sites")
import frappe
frappe.init(site="test.localhost"); frappe.connect()
try:
    from frappe.translate import clear_cache, get_all_translations
    frappe.local.lang = "zh"; clear_cache()
    merged = get_all_translations("zh")
    table = json.load(open("/workspace/Spike/P1S6R7/buttons/buttons.json", encoding="utf-8"))
    rows = [{"source": t["source"], "final": t["final"], "merged": merged.get(t["source"]),
             "match": (merged.get(t["source"]) or "").strip() == (t["final"] or "").strip()} for t in table]
    # Inter Company Invoice 源码未包 __()（purchase_invoice.js:228），csv 无法生效，判为不可改、比对时单列
    not_wrapped = {"Inter Company Invoice"}
    bad = [r for r in rows if not r["match"] and r["source"] not in not_wrapped]
    out = {"total": len(rows), "match": sum(r["match"] for r in rows), "mismatch": bad,
           "not_wrapped": [r for r in rows if r["source"] in not_wrapped]}
    open("/workspace/Spike/P1S6R7/buttons/compare.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: (v if k != "mismatch" else len(v)) for k, v in out.items() if k != "not_wrapped"}, ensure_ascii=False))
    sys.exit(1 if bad else 0)
finally:
    frappe.destroy()
