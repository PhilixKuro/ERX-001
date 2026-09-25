# V-18 probe payload, segment 2: zelin's `setup_tax_template` copied VERBATIM
# (Reference/zelin-tech-erpnext_china/erpnext_china/chart_of_accounts/
# company_default/utils.py, MIT) -- including the bare `except` and including
# the unmodified tax_template.json with the account-number typos
# (222105 / 22210005 where the chart has 2221005).
#
# The point of segment 2 is to find out what that typo actually does at runtime,
# so NOTHING here is fixed up.  Only the sibling calls that segment 2 does not
# need (set_default_accounts / setup_tax_rule / set_item_group_account /
# set_warehouse_account) are left out, per play-spike discipline 4 (one probe,
# one proposition): they would create Tax Rules and Item Group defaults that
# have nothing to do with the three questions being asked.

import json
import os

import frappe
from erpnext.setup.setup_wizard.operations.taxes_setup import from_detailed_data


def setup_tax_template(company_name):
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'tax_template.json')
        with open(file_path, 'r', encoding='utf-8') as json_file:
            tax_data = json.load(json_file)

        from_detailed_data(company_name, tax_data)
        # 标准功能中未处理含税字段，这里单独处理
        for prefix in ('Purchase', 'Sales'):
            header = frappe.qb.DocType(f"{prefix} Taxes and Charges Template")
            detail = frappe.qb.DocType(f"{prefix} Taxes and Charges")

            frappe.qb.update(detail
                ).join(header
                ).on(header.name == detail.parent
                ).where(header.title.like('%含税%')
                ).set(detail.included_in_print_rate, 1
                ).run()
    except:
        frappe.log_error("china_company_default.utils.setup_tax_template")
