"""SL-012 ②：抽 5 个被删的覆盖官方键，clear-cache 后经 get_all_translations("zh") 取到官方译文（HT-019）。
bench --site test.localhost execute 不便传参，故用 env/bin/python 直连站点。"""
import csv, json, os, random, subprocess, sys, types
os.chdir("/workspace/frappe-bench/sites")
import frappe
frappe.init(site="test.localhost"); frappe.connect()
from frappe.translate import clear_cache, get_all_translations, get_translations_from_apps
src = subprocess.run(["git", "-C", "/workspace/frappe-bench/apps/frappe_china", "show",
                      "af015fa:frappe_china/tests/translation_overrides.py"], check=True, capture_output=True, text=True).stdout
mod = types.ModuleType("orig"); exec(src, mod.__dict__)
from frappe_china.tests.translation_overrides import OVERRIDES
removed = sorted(set(mod.OVERRIDES) - set(OVERRIDES))
import re
cjk = [k for k in removed if re.search(r"[一-鿿]", mod.OVERRIDES[k].official)]
# 随机 5 个全是官方＝源词的符号／品牌键，区分不了「回落官方」与「无译文」；故改为全量核 + 另列官方为中文的键
pick = removed
frappe.local.lang = "zh"; clear_cache()
merged = get_all_translations("zh")
official = get_translations_from_apps("zh", apps=["frappe", "erpnext", "crm", "hrms", "insights", "raven"])
rows = [{"key": k, "old_ours": mod.OVERRIDES[k].ours, "official": official.get(k), "merged": merged.get(k),
         "ok": merged.get(k) == official.get(k)} for k in pick]
print(json.dumps({"removed": len(rows), "all_ok": all(r["ok"] for r in rows),
                  "not_ok": [r for r in rows if not r["ok"]],
                  "official_is_chinese": [r for r in rows if r["key"] in cjk]}, ensure_ascii=False, indent=1)); frappe.destroy()
