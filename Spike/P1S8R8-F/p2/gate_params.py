"""片2 小门：load_scenario 只读解析与六类校验（不写库）。临时 yaml 写在本目录，结束删除。"""
import json, os, re
from datetime import date, timedelta
import frappe
frappe.init(site="s8verify.localhost", sites_path="/workspace/frappe-bench/sites"); frappe.connect()
from frappe_debug.scenario.params import load_scenario
here = os.path.dirname(os.path.abspath(__file__))
src = open("/workspace/frappe-bench/apps/frappe_debug/frappe_debug/data/scenario.yaml", encoding="utf-8").read()
out = {}
sc = load_scenario(end=date(2026, 10, 20))
out["E=2026-10-20"] = {k: str(getattr(sc, k)) for k in ("S", "D1", "D2", "E")} | {"rules": {k: str(v) for k, v in sc.rule_dates.items()}, "segments": [[str(a), str(b)] for a, b in sc.segments]}
sc2 = load_scenario(end=date(2026, 6, 15))
out["E=2026-06-15"] = {"S": str(sc2.S), "S_weekday": sc2.S.strftime("%A"), "periodic_from": str(sc2.rule_dates["periodic"]),
    "review_days_hit_weekdays": sorted({(sc2.S + timedelta(days=14 * n)).strftime("%A") for n in range(30)})}
cases = {
  "missing_key": src.replace("shortage:\n", "shortage_x:\n", 1),
  "rules_reversed": src.replace("rule_eoq_from: +4m", "rule_eoq_from: +9m"),
  "loss_out_of_range": src.replace("cn_process_loss_percentage: 3,", "cn_process_loss_percentage: 120,", 1),
  "anomaly_outside": src.replace("anomaly: {from: +5m-10d", "anomaly: {from: +13m"),
}
for name, text in cases.items():
    path = os.path.join(here, f"tmp_{name}.yaml")
    open(path, "w", encoding="utf-8").write(text)
    try:
        load_scenario(path=path, end=date(2026, 10, 20)); out[name] = "NO ERROR"
    except frappe.ValidationError as e:
        out[name] = re.sub("<br>", " | ", str(e))[:300]
    finally:
        os.unlink(path)
try:
    load_scenario(end=date.today() + timedelta(days=1)); out["future_E"] = "NO ERROR"
except frappe.ValidationError as e:
    out["future_E"] = str(e)[:200]
print(json.dumps(out, ensure_ascii=False, indent=1))
frappe.db.rollback(); frappe.destroy()
