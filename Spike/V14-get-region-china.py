# V14: get_region() 对本机站点返回的字符串是否逐字为 "China"
# 跑法：docker compose exec -T -w /workspace/frappe-bench frappe \
#         bench --site erx.localhost execute 'frappe.utils.safe_exec.safe_exec' 不适用，
#       改用：bench --site erx.localhost console < 本文件   或  bench execute 包装函数
import json

import frappe
from erpnext import get_region

out = {}

# 1. get_region 无参（取默认公司或全局）
try:
    out["get_region_no_arg"] = repr(get_region())
except Exception as e:
    out["get_region_no_arg"] = f"EXC: {type(e).__name__}: {e}"

# 2. get_region 传本项目公司名
try:
    out["get_region_HDS"] = repr(get_region("华东弹簧"))
except Exception as e:
    out["get_region_HDS"] = f"EXC: {type(e).__name__}: {e}"

# 3. 各公司的 country 字段原值
out["companies"] = frappe.get_all("Company", fields=["name", "country", "default_currency"])

# 4. 全局默认
out["global_default_company"] = frappe.db.get_default("company")
out["global_country"] = frappe.db.get_default("country")
out["sys_country"] = frappe.db.get_single_value("System Settings", "country")

# 5. Country 记录里"中国"对应的 name（regional key 实际取的就是 Company.country）
out["country_records_cn"] = frappe.get_all(
    "Country", filters={"name": ["like", "%hina%"]}, fields=["name", "code"]
)

# 6. hooks 侧：当前已注册的 regional_overrides 键有哪些
try:
    out["regional_override_keys"] = list(frappe.get_hooks("regional_overrides", {}).keys())
except Exception as e:
    out["regional_override_keys"] = f"EXC: {e}"

print("===V14-RESULT-BEGIN===")
print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
print("===V14-RESULT-END===")

# 7. 逐字核验: repr 无法区分同形异码字符, 故再看 codepoint / utf8 字节 / 等值判断
_co = frappe.get_all("Company", pluck="name")[0]
_r = get_region(_co)
out2 = {
    "company_probed": _co,
    "value": _r,
    "repr": repr(_r),
    "eq_China_exact": _r == "China",
    "len": len(_r),
    "codepoints": [hex(ord(c)) for c in _r],
    "utf8_bytes": _r.encode("utf-8").hex(),
    "is_ascii": _r.isascii(),
    "China_key_present_in_overrides": "China" in frappe.get_hooks("regional_overrides", {}),
    "installed_apps": frappe.get_installed_apps(),
}
print("===V14-EXACT-BEGIN===")
print(json.dumps(out2, ensure_ascii=False, indent=2, default=str))
print("===V14-EXACT-END===")

# 8. "是否中文名"一问的收口: 站点语言 + Company.country 的字段定义(能否存中文)
_lang = frappe.db.get_single_value("System Settings", "language")
_df = frappe.get_meta("Company").get_field("country")
out3 = {
    "system_settings_language": _lang,
    "country_fieldtype": _df.fieldtype,
    "country_link_options": _df.options,
    "all_country_names_like_cn": frappe.get_all(
        "Country", filters={"code": "cn"}, fields=["name", "code"]
    ),
}
print("===V14-LANG-BEGIN===")
print(json.dumps(out3, ensure_ascii=False, indent=2, default=str))
print("===V14-LANG-END===")
