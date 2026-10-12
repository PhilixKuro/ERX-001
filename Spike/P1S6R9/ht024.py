"""R9 TS-032 第 2 步（HT-024）：测试站以中文会话取 Raven 页 boot 的翻译字典，看 context 键在不在。
容器内 bench 目录：env/bin/python /workspace/Spike/P1S6R9/ht024.py test.localhost"""
import json
import os
import sys

os.chdir("/workspace/frappe-bench/sites")
import frappe
from frappe.translate import clear_cache

frappe.init(site=sys.argv[1], sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
frappe.local.lang = "zh"
clear_cache()
from frappe.translate import get_messages_for_boot

messages = get_messages_for_boot()
print(json.dumps({key: messages.get(key) for key in ("Available", "Available:Raven User", "Away", "Do not disturb")}, ensure_ascii=False))
frappe.destroy()
