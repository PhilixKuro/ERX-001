#!/usr/bin/env bash
# 设界面语言与默认公司。在容器内跑——用宿主机的 docker/set-locale.sh 调用。
set -euo pipefail

SITE_NAME="${SITE_NAME:-erx.localhost}"
BENCH_DIR="/workspace/${BENCH_NAME:-frappe-bench}"
LANG_CODE="${UI_LANGUAGE:-zh}"
DEFAULT_COMPANY="${DEFAULT_COMPANY:-}"

log() { printf '\n\033[36m==> %s\033[0m\n' "$*"; }
ok()  { printf '\033[32m    %s\033[0m\n' "$*"; }

cd "$BENCH_DIR/sites"

log "设置界面语言为 $LANG_CODE，并对齐默认公司"
../env/bin/python <<PY
import frappe
frappe.init(site="$SITE_NAME"); frappe.connect()

lang = "$LANG_CODE"
if not frappe.db.exists("Language", lang):
    raise SystemExit(f"语言 {lang} 不存在。可用：" +
        ", ".join(frappe.db.get_all("Language", pluck="name", limit=200)))

# 系统级语言 + Administrator 个人语言（个人设置会覆盖系统设置）
ss = frappe.get_single("System Settings")
ss.language = lang
ss.save(ignore_permissions=True)
frappe.db.set_value("User", "Administrator", "language", lang)

# 默认公司对齐到演示数据所在的那家——否则打开演示单据会报无权限
target = "$DEFAULT_COMPANY"
if not target:
    # 优先取 demo_company（演示数据建在它名下），否则取第一家
    target = frappe.db.get_single_value("Global Defaults", "demo_company") \
             or (frappe.db.get_all("Company", pluck="name") or [None])[0]

if target:
    frappe.db.set_single_value("Global Defaults", "default_company", target)
    frappe.db.set_default("company", target)
    print(f"    默认公司: {target}")

frappe.db.commit()

# 校验
assert frappe.db.get_single_value("System Settings", "language") == lang, "语言未写入"
print(f"    语言: {frappe.db.get_value('Language', lang, 'language_name')} ({lang})")
PY

log "清缓存"
cd "$BENCH_DIR"
bench --site "$SITE_NAME" clear-cache
bench --site "$SITE_NAME" clear-website-cache
ok "完成"

cat <<EOF

\033[32m已生效。\033[0m 浏览器按 Ctrl-Shift-R 强制刷新。

语言想改回英文：UI_LANGUAGE=en docker/set-locale.sh
EOF
