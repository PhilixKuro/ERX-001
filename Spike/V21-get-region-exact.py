# V-21: get_region() 在本机站点 erx.localhost 上，对本项目公司是否逐字节返回 China
#
# 只读探针：只做 frappe.init / connect 与 db 读取，不写任何记录、不跑 migrate/build。
#
# 跑法（cwd 必须是 .../sites，否则 frappe logger 会因相对路径报错）:
#   docker exec -i -w /workspace/frappe-bench/sites -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
#     erx001-frappe-1 /workspace/frappe-bench/env/bin/python /workspace/Spike/V21-get-region-exact.py
#
# 公司名用 \u 转义写死，规避 Windows 到容器传输途中的编码歧义（本项目踩过 GBK 坑）。

import json
import os

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"  # 华东弹簧
TARGET = "China"
OUTDIR = "/workspace/Spike/V21-out"
OUT = os.path.join(OUTDIR, "get-region-exact.json")

result = {"probe": "V-21 get_region exact-match check", "site": SITE, "target": TARGET}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v!r}", flush=True)


def forensic(label, value):
    """把一个字符串摊开到码点/字节层面，肉眼同形的字符也能区分出来。"""
    if not isinstance(value, str):
        return {"label": label, "value": value, "type": type(value).__name__, "is_str": False}
    return {
        "label": label,
        "is_str": True,
        "repr": repr(value),
        "len": len(value),
        "eq_target_exact": value == TARGET,
        "codepoints": [hex(ord(c)) for c in value],
        "utf8_bytes_hex": value.encode("utf-8").hex(),
        "utf8_len": len(value.encode("utf-8")),
        "is_ascii": value.isascii(),
        "has_lead_trail_ws": value != value.strip(),
        "casefold_eq_target": value.casefold() == TARGET.casefold(),
    }


frappe.init(site=SITE)
frappe.connect()

import erpnext  # noqa: E402  (必须在 frappe.init 之后 import，否则取不到 site 上下文)
from erpnext import get_region  # noqa: E402

rec("erpnext_module_file", erpnext.__file__)
rec("get_region_defined_at", f"{get_region.__code__.co_filename}:{get_region.__code__.co_firstlineno}")
rec("installed_apps", frappe.get_installed_apps())

# ---- 1. 公司清单：确认 COMPANY 这个名字真的存在，且 abbr 是 HDS ----
companies = frappe.get_all("Company", fields=["name", "abbr", "country", "default_currency"])
rec("companies", companies)
rec("company_target_exists", COMPANY in [c["name"] for c in companies])

# ---- 2. Company.country 的原值（db 直读 与 cached 两路，防缓存偏差）----
country_db = frappe.db.get_value("Company", COMPANY, "country")
country_cached = frappe.get_cached_value("Company", COMPANY, "country")
result["country_db_forensic"] = forensic("frappe.db.get_value(Company,country)", country_db)
result["country_cached_forensic"] = forensic("frappe.get_cached_value(Company,country)", country_cached)
rec("country_db", country_db)
rec("country_cached", country_cached)
rec("country_db_eq_cached", country_db == country_cached)

# ---- 3. get_region 显式传公司 ----
try:
    r_with = get_region(COMPANY)
    result["get_region_with_company"] = forensic("get_region(COMPANY)", r_with)
    rec("get_region_with_company_value", r_with)
except Exception as e:
    result["get_region_with_company"] = {"EXC": f"{type(e).__name__}: {e}"}
    rec("get_region_with_company_value", f"EXC: {type(e).__name__}: {e}")

# ---- 4. get_region 无参（走 frappe.local.flags.company -> flags.country -> System Settings.country）----
rec("flags_company_before", getattr(frappe.local.flags, "company", None))
rec("flags_country_before", getattr(frappe.flags, "country", None))
try:
    r_no = get_region()
    result["get_region_no_arg"] = forensic("get_region() [flags.company unset]", r_no)
    rec("get_region_no_arg_value", r_no)
except Exception as e:
    result["get_region_no_arg"] = {"EXC": f"{type(e).__name__}: {e}"}
    rec("get_region_no_arg_value", f"EXC: {type(e).__name__}: {e}")

# ---- 5. get_region 无参、但按 docstring 设了 flags.company（只改进程内内存，不落库）----
try:
    frappe.local.flags.company = COMPANY
    r_flag = get_region()
    result["get_region_no_arg_with_flag"] = forensic("get_region() [flags.company=COMPANY]", r_flag)
    rec("get_region_no_arg_with_flag_value", r_flag)
finally:
    frappe.local.flags.company = None

# ---- 6. 无参兜底那条路的两个来源值 ----
rec("system_settings_country", frappe.db.get_single_value("System Settings", "country"))
rec("default_company", frappe.db.get_default("company"))
rec("default_country", frappe.db.get_default("country"))

# ---- 7. Country 主数据里 code=cn 的记录名（Company.country 是 Link 到 Country）----
rec("country_doctype_cn_rows", frappe.get_all("Country", filters={"code": "cn"}, fields=["name", "code"]))
rec(
    "country_doctype_like_hina",
    frappe.get_all("Country", filters={"name": ["like", "%hina%"]}, fields=["name", "code"]),
)
meta_country = frappe.get_meta("Company").get_field("country")
rec("company_country_fieldtype", meta_country.fieldtype)
rec("company_country_link_options", meta_country.options)

# ---- 8. hooks 侧：dispatch 的另一半，键里有没有 China ----
hooks = frappe.get_hooks("regional_overrides", {})
rec("regional_override_keys", list(hooks.keys()))
rec("China_key_in_regional_overrides", TARGET in hooks)
region_now = result.get("get_region_with_company", {}).get("repr")
rec("dispatch_lookup_hit", hooks.get(country_db, "NO-MATCH -> falls back to base function"))

# ---- 9. 最终判定 ----
verdict_basis = result.get("get_region_with_company", {})
result["verdict"] = {
    "get_region_with_company_is_exactly_China": verdict_basis.get("eq_target_exact"),
    "note": "hooks key presence is a SEPARATE fact, not part of this proposition",
    "China_key_in_hooks": TARGET in hooks,
}
rec("VERDICT", result["verdict"])

os.makedirs(OUTDIR, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\n[written] {OUT}", flush=True)

frappe.destroy()
