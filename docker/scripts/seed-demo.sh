#!/usr/bin/env bash
# 建公司 + 导入 ERPNext 演示数据。在容器内跑——用宿主机的 docker/seed-demo.sh 调用。
#
# 演示数据是假的，日后清理见 docker/seed-demo.sh --clear。
set -euo pipefail

SITE_NAME="${SITE_NAME:-erx.localhost}"
BENCH_DIR="/workspace/${BENCH_NAME:-frappe-bench}"
COMPANY="${COMPANY_NAME:-ERX Demo}"
ABBR="${COMPANY_ABBR:-ERX}"
COUNTRY="${COMPANY_COUNTRY:-China}"
CURRENCY="${COMPANY_CURRENCY:-CNY}"
TIMEZONE="${COMPANY_TIMEZONE:-Asia/Shanghai}"

log() { printf '\n\033[36m==> %s\033[0m\n' "$*"; }
ok()  { printf '\033[32m    %s\033[0m\n' "$*"; }

cd "$BENCH_DIR/sites"

if [ "${1:-}" = "--clear" ]; then
  log "清除演示数据"
  ../env/bin/python <<PY
import frappe
frappe.init(site="$SITE_NAME"); frappe.connect()
frappe.flags.in_demo = True
from erpnext.setup.demo import clear_demo_data
clear_demo_data()
frappe.db.commit()
print("    演示数据已清除")
PY
  exit 0
fi

# ---------- 1. 前置基础数据 ----------
# 与「公司是否已存在」无关，故放在公司判断之前——放进 else 分支会在公司已存在时
# 被整块跳过，而缺这些的站点照样建不出演示数据。两步都自带判据，可重复执行。
log "检查 ERPNext 基础数据"
../env/bin/python <<PY
import frappe
frappe.init(site="$SITE_NAME"); frappe.connect()

# Warehouse Type / UOM / Designation / 地址模板等。v15 的 bench new-site 装了，
# v16 没装——缺 "Warehouse Type: Transit" 时建公司会以 LinkValidationError 失败。
if not frappe.db.exists("Warehouse Type", "Transit"):
    from erpnext.setup.setup_wizard.operations.install_fixtures import install as install_fixtures
    install_fixtures("$COUNTRY")
    frappe.db.commit()
    print("    ERPNext 基础数据已安装")
else:
    print("    ERPNext 基础数据已存在")

# 默认计量单位。演示商品（demo_data/item.json）不带 stock_uom，而该字段 reqd=1，
# 靠 frappe 的全局默认值补。关键是要写进 frappe.defaults（session defaults），
# 不是 Stock Settings 的同名字段——v16 已不引用后者，只设它建商品照样报
# MandatoryError(stock_uom)，且 setup_demo_data() 会把异常吞进 Error Log 不抛出，
# 表现为「跑完了但什么都没建」。
if not frappe.defaults.get_defaults().get("stock_uom"):
    default_uom = "Nos" if frappe.db.exists("UOM", "Nos") else "Unit"
    frappe.db.set_default("stock_uom", default_uom)
    frappe.db.set_single_value("Stock Settings", "stock_uom", default_uom)
    frappe.db.commit()
    frappe.clear_cache()
    print(f"    默认计量单位设为 {default_uom}")
else:
    print("    默认计量单位已设")

# 标准价目表。演示订单不带 selling_price_list，靠全局默认值补，而这些字段 reqd=1。
# v15 由 bench new-site / fixtures 建好并设为默认；v16 两者都不做——Price List 表
# 是空的，建销售订单遂报 MandatoryError(selling_price_list, price_list_currency,
# plc_conversion_rate)。
currency = frappe.db.get_value("Company", {"name": ["!=", ""]}, "default_currency") or "$CURRENCY"
for pl_name, kind in (("Standard Selling", "selling"), ("Standard Buying", "buying")):
    if not frappe.db.exists("Price List", pl_name):
        frappe.get_doc({
            "doctype": "Price List",
            "price_list_name": pl_name,
            "currency": currency,
            "selling": 1 if kind == "selling" else 0,
            "buying": 1 if kind == "buying" else 0,
            "enabled": 1,
        }).insert(ignore_permissions=True)
        print(f"    价目表 {pl_name} 已建立（{currency}）")
    if frappe.defaults.get_defaults().get(f"{kind}_price_list") != pl_name:
        frappe.db.set_default(f"{kind}_price_list", pl_name)

# 全局币种。v16 留着镜像默认的 INR，与公司币种不一致会让单据汇率校验失败。
if frappe.defaults.get_defaults().get("currency") != currency:
    frappe.db.set_default("currency", currency)
    frappe.db.set_single_value("Global Defaults", "default_currency", currency)
    print(f"    全局币种设为 {currency}")

frappe.db.commit()
frappe.clear_cache()
PY

# ---------- 2. 建公司与会计年度 ----------
log "检查公司"
company_count=$(../env/bin/python -c "
import frappe
frappe.init(site='$SITE_NAME'); frappe.connect()
print(frappe.db.count('Company'))
" 2>/dev/null | tail -1)

if [ "$company_count" -gt 0 ]; then
  ok "已有 $company_count 家公司，跳过向导"
else
  log "建立公司与会计年度（$COMPANY / $COUNTRY / $CURRENCY）"
  # 不走 setup_complete()——bench new-site 已把 setup_complete 置为 1，
  # 而该函数开头就 `if frappe.is_setup_complete(): return`，会静默什么都不做。
  # 故直接建 Company 与 Fiscal Year。
  ../env/bin/python <<PY
import frappe
from frappe.utils import getdate
frappe.init(site="$SITE_NAME"); frappe.connect()
frappe.flags.in_setup_wizard = True

# 系统级设置
ss = frappe.get_single("System Settings")
ss.country = "$COUNTRY"
ss.time_zone = "$TIMEZONE"
ss.language = "en"
ss.save(ignore_permissions=True)

# 会计年度（自然年）
today = getdate()
fy_start, fy_end = today.replace(month=1, day=1), today.replace(month=12, day=31)
fy_name = f"{fy_start.year}"
if not frappe.db.exists("Fiscal Year", fy_name):
    frappe.get_doc({
        "doctype": "Fiscal Year",
        "year": fy_name,
        "year_start_date": fy_start,
        "year_end_date": fy_end,
    }).insert(ignore_permissions=True)
    print(f"    会计年度 {fy_name} 已建立")

# 公司（插入时自动生成科目表、仓库、默认账户）
if not frappe.db.exists("Company", "$COMPANY"):
    frappe.get_doc({
        "doctype": "Company",
        "company_name": "$COMPANY",
        "abbr": "$ABBR",
        "default_currency": "$CURRENCY",
        "country": "$COUNTRY",
        "chart_of_accounts": "Standard",
        "create_chart_of_accounts_based_on": "Standard Template",
        "enable_perpetual_inventory": 1,
    }).insert(ignore_permissions=True)
    print("    公司 $COMPANY 已建立")

frappe.db.set_default("company", "$COMPANY")
frappe.db.set_single_value("Global Defaults", "default_company", "$COMPANY")
frappe.db.commit()
# 注：导入演示数据后默认公司需改指 "(Demo)" 副本——演示单据都建在它名下，
# 默认公司不一致时打开那些单据会被报成「没有权限」。见本脚本末尾。

# 校验——不靠 print 断言成功
assert frappe.db.count("Company") > 0, "公司未建成"
assert frappe.db.count("Fiscal Year") > 0, "会计年度未建成"
print("    校验通过：公司与会计年度均已落库")
PY
  ok "公司与会计年度完成"
fi

# ---------- 3. 导入演示数据 ----------
log "检查演示数据"
demo_exists=$(../env/bin/python -c "
import frappe
frappe.init(site='$SITE_NAME'); frappe.connect()
print(1 if frappe.db.get_single_value('Global Defaults','demo_company') else 0)
" 2>/dev/null | tail -1)

if [ "$demo_exists" = "1" ]; then
  ok "演示数据已存在，跳过"
else
  log "导入演示数据（商品、客户、供应商、订单，需几分钟）"
  ../env/bin/python <<PY
import inspect
import frappe
frappe.init(site="$SITE_NAME"); frappe.connect()
frappe.flags.in_demo = True
from erpnext.setup.demo import setup_demo_data

# 签名随版本变化：v15 是 setup_demo_data()（内部取第一家公司），
# v16 改成 setup_demo_data(company_name)。按实参个数分派，两版都能用。
if len(inspect.signature(setup_demo_data).parameters):
    setup_demo_data("$COMPANY")
else:
    setup_demo_data()
frappe.db.commit()

counts = {dt: frappe.db.count(dt) for dt in ("Company", "Item", "Customer", "Supplier", "Sales Order")}
print("    " + ", ".join(f"{k}={v}" for k, v in counts.items()))

# v16 的 setup_demo_data() 用 try/except 把异常写进 Error Log 后就返回，不抛出
# （v15 会 raise）。所以「跑完没报错」不等于成功，须查计数；失败时把日志摘出来，
# 否则线索只留在站点的 Error Log 里。
if not counts["Item"]:
    logs = frappe.db.get_all("Error Log", fields=["error"], order_by="creation desc", limit=1)
    if logs:
        tail = [l for l in logs[0].error.strip().splitlines() if l.strip()][-3:]
        print("    最近的 Error Log：")
        for line in tail:
            print("      " + line.strip()[:200])
    raise SystemExit("演示数据未生成商品——见上方 Error Log 摘要")
PY
  ok "演示数据完成"
fi

# ---------- 4. 默认公司对齐到演示数据所在那家 ----------
# setup_demo_data() 建了一个 "(Demo)" 副本公司并把全部演示单据放在它名下。
# 默认公司若仍指主公司，打开演示单据会被 ERPNext 报成「没有权限」——实际是
# 跨公司数据隔离，不是角色缺失。
log "对齐默认公司"
../env/bin/python <<PY
import frappe
frappe.init(site="$SITE_NAME"); frappe.connect()
demo = frappe.db.get_single_value("Global Defaults", "demo_company")
if demo:
    frappe.db.set_single_value("Global Defaults", "default_company", demo)
    frappe.db.set_default("company", demo)
    frappe.db.commit()
    print(f"    默认公司 -> {demo}")
else:
    print("    无 demo_company，保持不变")
PY
ok "完成"

# ---------- 5. 标记配置完成 ----------
# 否则登录后被强制跳到 /desk/setup-wizard 填表。
# v16 的判据不是 System Settings.setup_complete，而是 Installed Application
# 表里 frappe 与 erpnext 两行的 is_setup_complete 是否都为 1
# （见 apps/frappe/frappe/__init__.py 的 is_setup_complete()）。
# 光设 System Settings 无效——这是 v15 的判据。
log "标记配置完成"
../env/bin/python <<PY
import frappe
frappe.init(site="$SITE_NAME"); frappe.connect()

for row in frappe.get_all("Installed Application", pluck="name"):
    frappe.db.set_value("Installed Application", row, "is_setup_complete", 1)
frappe.db.set_single_value("System Settings", "setup_complete", 1)
# 首页从 setup-wizard 改回工作区
frappe.db.set_default("desktop:home_page", "workspace")
frappe.db.commit()
frappe.clear_cache()

assert frappe.is_setup_complete(), "is_setup_complete() 仍为 False，登录会被跳到向导"
print("    已标记完成，首页为 workspace")
PY
ok "完成"

# ---------- 6. 清缓存 ----------
log "清缓存"
cd "$BENCH_DIR"
bench --site "$SITE_NAME" clear-cache
bench --site "$SITE_NAME" clear-website-cache
ok "完成"

cat <<EOF

\033[32m站点已配置。\033[0m 刷新浏览器（Ctrl-Shift-R 强制刷新）即可看到完整界面。

清除演示数据：docker/seed-demo.sh --clear
EOF
