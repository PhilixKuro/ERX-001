#!/usr/bin/env bash
# V-19 step 1: build a minimal throwaway own-app (erx_v19) that carries zelin's
# option A VERBATIM:
#   - the 4 `override_whitelisted_methods` (same as V-18)
#   - PLUS the three Company doc_events (before_insert / on_update / after_insert)
#   - PLUS `erpnext_china_create_charts` and its helpers (_import_accounts /
#     add_suffix_if_duplicate / identify_is_group), which V-18 deliberately left out
#   - PLUS `set_company_default` and its five sub-steps, and the three data files
#     they read (default_accounts.csv / tax_template.json / tax_rule.csv)
#
# Run INSIDE the container:
#   docker exec -i -w /workspace/frappe-bench erx001-frappe-1 bash /workspace/Spike/V19-setup-test-app.sh
#
# Hand-rolled instead of `bench new-app` because this bench has no flit_core, so
# `bench new-app`'s `pip install -e` fails (see Spike/V16-desk-js-override.md).
# Reaches sys.path through a .pth file, the same mechanism frappe/erpnext
# themselves use in this bench.
set -euo pipefail

BENCH=/workspace/frappe-bench
APP=erx_v19
ROOT=$BENCH/apps/$APP
SITE=erx.localhost
ZELIN=/workspace/Reference/zelin-tech-erpnext_china/erpnext_china

echo "== 1. app skeleton =="
mkdir -p "$ROOT/$APP/chart_of_accounts/custom_accounts/chart_of_accounts"
mkdir -p "$ROOT/$APP/chart_of_accounts/company_default"

printf '__version__ = "0.0.1"\n'  > "$ROOT/$APP/__init__.py"
printf 'Erx V19\n'                > "$ROOT/$APP/modules.txt"
:                                 > "$ROOT/$APP/patches.txt"
:                                 > "$ROOT/$APP/chart_of_accounts/__init__.py"
:                                 > "$ROOT/$APP/chart_of_accounts/custom_accounts/__init__.py"
:                                 > "$ROOT/$APP/chart_of_accounts/company_default/__init__.py"

echo "== 2. hooks.py -- 4 overrides AND the 3 Company doc_events (option A) =="
cat > "$ROOT/$APP/hooks.py" <<'EOF'
app_name = "erx_v19"
app_title = "Erx V19"
app_publisher = "ERX-001 spike V-19"
app_description = "throwaway probe app for 待验表 V-19 (option A, zelin verbatim)"
app_email = "spike@example.invalid"
app_license = "MIT"

# zelin hooks.py:30-37 -- unchanged apart from the app name
override_whitelisted_methods = {
	"erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country": "erx_v19.chart_of_accounts.custom_accounts.custom_account.get_charts_for_country",
	"erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_chart": "erx_v19.chart_of_accounts.custom_accounts.custom_account.get_chart",
	"erpnext.accounts.utils.get_coa": "erx_v19.chart_of_accounts.custom_accounts.custom_account.get_coa",
	"frappe.desk.treeview.get_all_nodes": "erx_v19.chart_of_accounts.custom_accounts.custom_account.get_all_nodes",
}

# zelin hooks.py:39-45 -- THIS is what V-18 left out and V-19 is here to test
doc_events = {
	"Company": {
		"before_insert": "erx_v19.doc_events.company_before_insert",
		"on_update": "erx_v19.doc_events.company_on_update",
		"after_insert": "erx_v19.doc_events.company_after_insert",
	}
}

# NOTE, on purpose:
#   no after_install -- zelin runs set_company_default from after_install too, but
#   the company-creation path is what V-19 is about, and V-18 segment 2 already
#   covered the after_install tax-template behaviour.
EOF

echo "== 3. copy zelin payload verbatim (chart JSON + the 3 company_default data files) =="
cp "$ZELIN/chart_of_accounts/custom_accounts/chart_of_accounts/cn_smes_chart_of_accounts2024.json" \
   "$ROOT/$APP/chart_of_accounts/custom_accounts/chart_of_accounts/"
cp "$ZELIN/chart_of_accounts/company_default/tax_template.json" \
   "$ZELIN/chart_of_accounts/company_default/default_accounts.csv" \
   "$ZELIN/chart_of_accounts/company_default/tax_rule.csv" \
   "$ROOT/$APP/chart_of_accounts/company_default/"
md5sum "$ZELIN/chart_of_accounts/custom_accounts/chart_of_accounts/cn_smes_chart_of_accounts2024.json" \
       "$ROOT/$APP/chart_of_accounts/custom_accounts/chart_of_accounts/cn_smes_chart_of_accounts2024.json"
for f in tax_template.json default_accounts.csv tax_rule.csv; do
	md5sum "$ZELIN/chart_of_accounts/company_default/$f" "$ROOT/$APP/chart_of_accounts/company_default/$f"
done

echo "== 4. python code written by the host (see Spike/V19-app-*.py) =="
cp /workspace/Spike/V19-app-custom_account.py "$ROOT/$APP/chart_of_accounts/custom_accounts/custom_account.py"
cp /workspace/Spike/V19-app-utils.py          "$ROOT/$APP/chart_of_accounts/company_default/utils.py"
cp /workspace/Spike/V19-app-doc_events.py     "$ROOT/$APP/doc_events.py"
echo "-- utils.py must be byte-identical to zelin's --"
md5sum "$ZELIN/chart_of_accounts/company_default/utils.py" \
       "$ROOT/$APP/chart_of_accounts/company_default/utils.py"

echo "== 5. python packaging (pyproject + .pth, no pip) =="
cat > "$ROOT/pyproject.toml" <<'EOF'
[project]
name = "erx_v19"
version = "0.0.1"
description = "throwaway probe app for ERX-001 V-19"
requires-python = ">=3.10"
dependencies = []

[build-system]
requires = ["flit_core >=3.4,<4"]
build-backend = "flit_core.buildapi"
EOF

SP=$(ls -d $BENCH/env/lib/python*/site-packages)
echo "$ROOT" > "$SP/$APP.pth"
echo "   .pth -> $SP/$APP.pth"

echo "== 6. register in sites/apps.txt (file has NO trailing newline: rewrite whole) =="
if ! grep -qx "$APP" "$BENCH/sites/apps.txt"; then
	printf 'frappe\nerpnext\n%s\n' "$APP" > "$BENCH/sites/apps.txt"
fi
cat -A "$BENCH/sites/apps.txt"

echo "== 7. import check =="
cd "$BENCH"
./env/bin/python -c "
import erx_v19.hooks as h
print('hooks ok, overrides =', len(h.override_whitelisted_methods))
print('doc_events Company =', h.doc_events['Company'])
import erx_v19.doc_events as de
print('doc_events module ok, china_coa =', de.china_coa)
from erx_v19.chart_of_accounts.custom_accounts.custom_account import erpnext_china_create_charts
print('erpnext_china_create_charts importable:', callable(erpnext_china_create_charts))
from erx_v19.chart_of_accounts.company_default.utils import set_company_default
print('set_company_default importable:', callable(set_company_default))
"

echo "== 8. install on site =="
bench --site "$SITE" install-app "$APP" 2>&1 | tail -8

echo "== 9. installed apps =="
bench --site "$SITE" list-apps 2>&1 | tail -10

echo "SETUP DONE"
