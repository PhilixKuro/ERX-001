"""Local, named fixtures for the TS-019 browser acceptance on s8dev only."""
import json
import os
from datetime import datetime

import frappe


def prepare():
	if frappe.local.site != "s8dev.localhost":
		raise RuntimeError("fixture requires s8dev.localhost")
	frappe.set_user("Administrator")
	from frappe_debug.demo.config import get_demo_config
	from frappe_debug.demo.config import CONFIG_PATH, resolve_date, validate_config
	from frappe_debug.scenario.params import load_scenario
	from frappe_debug.scenario.masters import _warehouses

	sc = load_scenario()
	company = sc.raw["company"]["name"]
	stores = _warehouses(frappe.get_doc("Company", company))["stores"]
	bank = frappe.db.get_value("Account", {"company": company, "account_number": "1002", "is_group": 0}, "name")
	customer = frappe.db.get_value("Customer", {}, "name")
	supplier = frappe.db.get_value("Supplier", {"disabled": 0, "prevent_pos": 0, "warn_pos": 0}, "name")
	material = sc.raw["items"]["materials"][0]["code"]
	product = sc.raw["items"]["products"][0]["code"]
	result = {"site": frappe.local.site, "company": company, "warehouse": stores, "bank": bank,
		"customer": customer, "supplier": supplier, "material": material, "product": product,
		"config": get_demo_config()}
	for name in ("warehouse", "bank", "customer", "supplier"):
		if not result[name]:
			raise RuntimeError(f"missing fixture dependency {name}")
	import yaml
	result["marker"] = "_FCT-TS019-" + datetime.now().strftime("%Y%m%d%H%M%S")
	text = (CONFIG_PATH.parent / "demo_selftest.yaml").read_text(encoding="utf-8")
	for key in ("company", "warehouse", "bank", "customer", "supplier", "material", "product", "marker"):
		text = text.replace(f"@{key}@", result[key])
	config = yaml.safe_load(text)
	config["scene_date_fields"] = result["config"]["scene_date_fields"]
	config["dates"] = result["config"]["dates"]
	problems = validate_config(config, config["dates"])
	if problems:
		raise RuntimeError(problems)
	for act in config["acts"]:
		act["scene_date"] = resolve_date(act["date"], config["dates"])
	result["selftest"] = config
	print(json.dumps(result, ensure_ascii=False, default=str))
	return result


if __name__ == "__main__":
	os.chdir("/workspace/frappe-bench/sites")
	frappe.init(site="s8dev.localhost", sites_path="/workspace/frappe-bench/sites")
	frappe.connect()
	try:
		prepare()
	finally:
		frappe.destroy()
