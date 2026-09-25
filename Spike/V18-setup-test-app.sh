#!/usr/bin/env bash
# V-18 step 1: build a minimal throwaway own-app (erx_v18) carrying ONLY the four
# `override_whitelisted_methods` from zelin plus the chart JSON and the tax
# template JSON.  Deliberately NO Company doc_events and NO
# `ignore_chart_of_accounts` anywhere -- that is precisely what decision 5's
# option B proposes, and what this probe has to falsify or confirm.
#
# Run INSIDE the container:
#   docker exec -i -w /workspace/frappe-bench erx001-frappe-1 bash /workspace/Spike/V18-setup-test-app.sh
#
# Hand-rolled instead of `bench new-app` because this bench has no flit_core, so
# `bench new-app`'s `pip install -e` fails (see Spike/V16-desk-js-override.md).
# Reaches sys.path through a .pth file, the same mechanism frappe/erpnext
# themselves use in this bench.
set -euo pipefail

BENCH=/workspace/frappe-bench
APP=erx_v18
ROOT=$BENCH/apps/$APP
SITE=erx.localhost
ZELIN=/workspace/Reference/zelin-tech-erpnext_china/erpnext_china

echo "== 1. app skeleton =="
mkdir -p "$ROOT/$APP/chart_of_accounts/custom_accounts/chart_of_accounts"
mkdir -p "$ROOT/$APP/chart_of_accounts/company_default"

printf '__version__ = "0.0.1"\n'  > "$ROOT/$APP/__init__.py"
printf 'Erx V18\n'                > "$ROOT/$APP/modules.txt"
: 									> "$ROOT/$APP/patches.txt"
: 									> "$ROOT/$APP/chart_of_accounts/__init__.py"
: 									> "$ROOT/$APP/chart_of_accounts/custom_accounts/__init__.py"
: 									> "$ROOT/$APP/chart_of_accounts/company_default/__init__.py"

echo "== 2. hooks.py -- FOUR overrides only, zero Company doc_events =="
cat > "$ROOT/$APP/hooks.py" <<'EOF'
app_name = "erx_v18"
app_title = "Erx V18"
app_publisher = "ERX-001 spike V-18"
app_description = "throwaway probe app for 待验表 V-18"
app_email = "spike@example.invalid"
app_license = "MIT"

# Decision 5 option B: copy ONLY these four, nothing else.
override_whitelisted_methods = {
	"erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country": "erx_v18.chart_of_accounts.custom_accounts.custom_account.get_charts_for_country",
	"erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_chart": "erx_v18.chart_of_accounts.custom_accounts.custom_account.get_chart",
	"erpnext.accounts.utils.get_coa": "erx_v18.chart_of_accounts.custom_accounts.custom_account.get_coa",
	"frappe.desk.treeview.get_all_nodes": "erx_v18.chart_of_accounts.custom_accounts.custom_account.get_all_nodes",
}

# NOTE, on purpose:
#   no doc_events            -> Company gets no before_insert / on_update / after_insert
#   no after_install          -> nothing pre-seeds accounts behind our back
# so the company we create below runs the *native* erpnext creation path.
EOF

echo "== 3. copy zelin payload verbatim (chart JSON + tax template JSON) =="
cp "$ZELIN/chart_of_accounts/custom_accounts/chart_of_accounts/cn_smes_chart_of_accounts2024.json" \
   "$ROOT/$APP/chart_of_accounts/custom_accounts/chart_of_accounts/"
cp "$ZELIN/chart_of_accounts/company_default/tax_template.json" \
   "$ROOT/$APP/chart_of_accounts/company_default/"
md5sum "$ZELIN/chart_of_accounts/custom_accounts/chart_of_accounts/cn_smes_chart_of_accounts2024.json" \
       "$ROOT/$APP/chart_of_accounts/custom_accounts/chart_of_accounts/cn_smes_chart_of_accounts2024.json"
md5sum "$ZELIN/chart_of_accounts/company_default/tax_template.json" \
       "$ROOT/$APP/chart_of_accounts/company_default/tax_template.json"

echo "== 4. custom_account.py / utils.py are written by the host (see Spike/) =="
cp /workspace/Spike/V18-app-custom_account.py "$ROOT/$APP/chart_of_accounts/custom_accounts/custom_account.py"
cp /workspace/Spike/V18-app-utils.py          "$ROOT/$APP/chart_of_accounts/company_default/utils.py"

echo "== 5. python packaging (pyproject + .pth, no pip) =="
cat > "$ROOT/pyproject.toml" <<'EOF'
[project]
name = "erx_v18"
version = "0.0.1"
description = "throwaway probe app for ERX-001 V-18"
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
./env/bin/python -c "import erx_v18.hooks as h; print('hooks ok, overrides =', len(h.override_whitelisted_methods)); print('has doc_events attr:', hasattr(h,'doc_events'))"

echo "== 8. install on site =="
bench --site "$SITE" install-app "$APP" 2>&1 | tail -6

echo "== 9. installed apps =="
bench --site "$SITE" list-apps 2>&1 | tail -10

echo "SETUP DONE"
