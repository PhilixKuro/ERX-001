"""S8 R8 SB FD-012 edit script: two-layer guard against installing frappe_debug on a customer site."""

import os

ROOT = "d:/ERX-001"


def edit(rel, pairs):
	path = os.path.join(ROOT, rel)
	# text mode: CRLF files read as LF and are written back as CRLF on Windows
	with open(path, encoding="utf-8") as handle:
		text = handle.read()
	for old, new in pairs:
		if new in text:
			continue
		assert text.count(old) == 1, (rel, old[:80])
		text = text.replace(old, new)
	with open(path, "w", encoding="utf-8") as handle:
		handle.write(text)


edit(
	"frappe-bench/apps/frappe_debug/frappe_debug/hooks.py",
	[
		(
			'''required_apps = ["frappe_china"]
''',
			'''required_apps = ["frappe_china"]
# FD-012: refuse to install unless the site config sets frappe_debug_allowed=1
before_install = "frappe_debug.install.before_install"
''',
		)
	],
)

edit(
	"docker/apps.json",
	[
		(
			'''    "commit": "dfc5ffb6eae5d2c92f402dc83179049df54be66a",
    "app_name": "frappe_debug"
  }''',
			'''    "commit": "dfc5ffb6eae5d2c92f402dc83179049df54be66a",
    "app_name": "frappe_debug",
    "demo_only": true
  }''',
		)
	],
)

edit(
	"docker/scripts/setup.sh",
	[
		(
			'''SITE_NAME="${SITE_NAME:-erx.localhost}"
BENCH_NAME="${BENCH_NAME:-frappe-bench}"''',
			'''SITE_NAME="${SITE_NAME:-erx.localhost}"
# 1＝演示站或开发站：装 apps.json 里标 demo_only 的 app（frappe_debug）。缺省 0，客户正式库不装（FD-012）
DEMO_SITE="${DEMO_SITE:-0}"
BENCH_NAME="${BENCH_NAME:-frappe-bench}"''',
		),
		(
			'''        a.get("app_name") or "-",
        "1" if a.get("official") else "0",
        sep="\\t",''',
			'''        a.get("app_name") or "-",
        "1" if a.get("official") else "0",
        "1" if a.get("demo_only") else "0",
        sep="\\t",''',
		),
		(
			'''while IFS=$'\\t' read -r app_url app_ref app_commit app_name app_official; do
  [ -z "$app_url" ] && continue
  if [ "$app_url" = "-" ]; then''',
			'''while IFS=$'\\t' read -r app_url app_ref app_commit app_name app_official _app_demo_only; do
  [ -z "$app_url" ] && continue
  if [ "$app_url" = "-" ]; then''',
		),
		(
			'''while IFS=$'\\t' read -r app_url app_ref app_commit app_name app_official; do
  [ -z "$app_name" ] || [ "$app_name" = "-" ] && continue
  # 没有 url 的条目第 3 段已跳过并警告''',
			'''while IFS=$'\\t' read -r app_url app_ref app_commit app_name app_official app_demo_only; do
  [ -z "$app_name" ] || [ "$app_name" = "-" ] && continue
  # 没有 url 的条目第 3 段已跳过并警告''',
		),
		(
			'''  [ "$app_name" = "frappe" ] && continue   # frappe 随建站自动装
''',
			'''  [ "$app_name" = "frappe" ] && continue   # frappe 随建站自动装
  # 演示专用 app 只装演示站／开发站；装前写站点许可标记，app 自身的 before_install 认它（FD-012）
  if [ "$app_demo_only" = "1" ]; then
    if [ "$DEMO_SITE" != "1" ]; then
      ok "$app_name 是演示专用 app，DEMO_SITE 不为 1，不装（客户正式库不装）"
      continue
    fi
    bench --site "$SITE_NAME" set-config -p frappe_debug_allowed 1
  fi
''',
		),
	],
)

edit(
	"docker/up.sh",
	[
		(
			'''  -e SITE_NAME="${SITE_NAME:-erx.localhost}" \\
''',
			'''  -e SITE_NAME="${SITE_NAME:-erx.localhost}" \\
  -e DEMO_SITE="${DEMO_SITE:-0}" \\
''',
		)
	],
)

edit(
	"docker/.env.example",
	[
		(
			'''SITE_NAME=erx.localhost
BENCH_NAME=frappe-bench
''',
			'''SITE_NAME=erx.localhost
BENCH_NAME=frappe-bench
# 1＝本站是演示站或开发站：up.sh 装演示专用的 frappe_debug，configure-apps.sh 才可带 --demo。
# 客户正式库保持 0（frappe_debug 自身也会在站点配置没有 frappe_debug_allowed=1 时拒装）
DEMO_SITE=0
''',
		)
	],
)

edit(
	"docker/scripts/configure_apps.py",
	[
		(
			'''    parser.add_argument(
        "--company",
        default=None,
        help="CRM 生成报价单用的公司；缺省取站上唯一一家中式公司",
    )
    args = parser.parse_args(argv)''',
			'''    parser.add_argument(
        "--company",
        default=None,
        help="CRM 生成报价单用的公司；缺省取站上唯一一家中式公司",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="演示站前置（改 Administrator 显示名、开批号全局开关等）；客户正式库不加（FD-012）",
    )
    args = parser.parse_args(argv)''',
		),
		(
			'''        for target, fields in configure_demo_prerequisites(notes).items():
            changes.setdefault(target, {}).update(fields)''',
			'''        if args.demo:
            for target, fields in configure_demo_prerequisites(notes).items():
                changes.setdefault(target, {}).update(fields)
        else:
            notes.append("未带 --demo：跳过演示前置（Administrator 显示名、批号开关、性别与称呼）")''',
		),
	],
)

edit(
	"docker/configure-apps.sh",
	[
		(
			'''#   docker/configure-apps.sh --site erx.localhost --company 华东弹簧有限公司
#''',
			'''#   docker/configure-apps.sh --site erx.localhost --company 华东弹簧有限公司 --demo
#
# --demo：演示站前置（Administrator 显示名、批号开关、性别与称呼），只对演示站／开发站加，客户正式库不加。''',
		),
		(
			'''company=""
while [ $# -gt 0 ]; do
  case "$1" in
    --site) site="${2:?--site 需要一个值}"; shift 2 ;;
    --company) company="${2:?--company 需要一个值}"; shift 2 ;;''',
			'''company=""
demo=""
while [ $# -gt 0 ]; do
  case "$1" in
    --site) site="${2:?--site 需要一个值}"; shift 2 ;;
    --company) company="${2:?--company 需要一个值}"; shift 2 ;;
    --demo) demo=1; shift ;;''',
		),
		(
			'''[ -n "$company" ] && args+=(--company "$company")
''',
			'''[ -n "$company" ] && args+=(--company "$company")
[ -n "$demo" ] && args+=(--demo)
''',
		),
	],
)

edit(
	"docker/README.md",
	[
		(
			'''docker/configure-apps.sh --site erx.localhost --company 华东弹簧有限公司
```
''',
			'''docker/configure-apps.sh --site erx.localhost --company 华东弹簧有限公司 --demo
```

- `--demo` 才跑演示前置（性别与称呼原生清单、批号全局开关、Administrator 显示名改「演示管理员」）。只对演示站、开发站加；客户正式库不加（S8 R8 FD-012）。
''',
		),
		(
			'''## 配置四个 App
''',
			'''## 演示专用 app 与客户正式库

`apps.json` 里标 `"demo_only": true` 的条目（现为 `frappe_debug`）只装演示站和开发站，两层把关（S8 R8 FD-012，依据 ADR-0013）：

- `setup.sh` 只在 `DEMO_SITE=1`（`docker/.env`，缺省 0）时装它，装前写站点配置 `frappe_debug_allowed=1`；缺省时跳过并打一行说明。代码照样克隆进 `apps/`，只是不装到站点上。
- `frappe_debug` 自身的 `before_install` 在站点配置没有 `frappe_debug_allowed=1` 时拒装。手工 `bench install-app` 前须先 `bench --site <站点> set-config -p frappe_debug_allowed 1`，确认不是客户正式库再做。
- 已装好的站不受影响：守卫只在安装时检查。

## 配置四个 App
''',
		),
	],
)
print("ok")
