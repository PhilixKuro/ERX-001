"""R9 TS-026：从站点取六个官方 app 的译文（不手抄）。容器内 bench 目录：
../env/bin/python /workspace/Spike/P1S6R9/officials.py <site> <键> [...]"""
import json
import os
import sys

os.chdir("/workspace/frappe-bench/sites")
import frappe
from frappe.translate import get_all_translations, get_translations_from_apps

frappe.init(site=sys.argv[1], sites_path=".")
frappe.connect()
official = get_translations_from_apps("zh", apps=["frappe", "erpnext", "crm", "hrms", "insights", "raven"])
merged = get_all_translations("zh")
print(json.dumps({key: {"official": official.get(key), "merged": merged.get(key)} for key in sys.argv[2:]}, ensure_ascii=False, indent=1))
frappe.destroy()
