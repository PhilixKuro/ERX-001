#!/usr/bin/env bash
# V-16 step 1: build a minimal throwaway own-app (erx_spike) that injects a
# probe js into the desk page via app_include_js. Run INSIDE the container:
#   docker exec -w /workspace/frappe-bench erx001-frappe-1 bash /workspace/Spike/V16-setup-test-app.sh
#
# Hand-rolled instead of `bench new-app` so nothing is pip-installed and no
# upstream file is touched. Reaches sys.path through a .pth file, the same
# mechanism frappe/erpnext themselves use in this bench.
set -euo pipefail

BENCH=/workspace/frappe-bench
APP=erx_spike
ROOT=$BENCH/apps/$APP
SITE=erx.localhost

echo "== 1. app skeleton =="
mkdir -p "$ROOT/$APP/public/js" "$ROOT/$APP/config"

cat > "$ROOT/$APP/__init__.py" <<'EOF'
__version__ = "0.0.1"
EOF

# modules.txt is read by frappe during install; must be non-empty
cat > "$ROOT/$APP/modules.txt" <<'EOF'
Erx Spike
EOF

cat > "$ROOT/$APP/patches.txt" <<'EOF'
EOF

# Two injection routes on purpose:
#   erx_spike.bundle.js  -> goes through esbuild + assets.json (bench build owns it)
#   /assets/erx_spike/js/V16-raw-probe.js -> raw path, bypasses the bundler
cat > "$ROOT/$APP/hooks.py" <<'EOF'
app_name = "erx_spike"
app_title = "Erx Spike"
app_publisher = "ERX-001 spike V-16"
app_description = "throwaway probe app for待验表 V-16"
app_email = "spike@example.invalid"
app_license = "MIT"

app_include_js = [
	"erx_spike.bundle.js",
	"/assets/erx_spike/js/V16-raw-probe.js",
]
EOF

echo "== 2. bundle entry + raw copy of the probe =="
# esbuild entry: import the probe so it lands inside the built bundle
cat > "$ROOT/$APP/public/js/erx_spike.bundle.js" <<'EOF'
import "./V16-bundled-probe.js";
EOF

# The bundled copy tags itself as route=bundle, the raw copy as route=raw.
sed 's/window.__ERX_V16 = window.__ERX_V16 || {}/window.__ERX_V16 = window.__ERX_V16 || {}/' \
	/workspace/Spike/V16-desk-js-override.probe.js > "$ROOT/$APP/public/js/V16-bundled-probe.js"

# raw route: same file, but only records presence/order (no double patching)
cat > "$ROOT/$APP/public/js/V16-raw-probe.js" <<'EOF'
(function () {
	var R = (window.__ERX_V16_RAW = window.__ERX_V16_RAW || {});
	R.loaded = true;
	R.t_parse = Date.now();
	R.bundle_probe_ran_before_me = !!(window.__ERX_V16 && window.__ERX_V16.loaded);
	R.sidebar_header_defined = !!(window.frappe && frappe.ui && frappe.ui.SidebarHeader);
	R.script_count_at_parse = document.querySelectorAll("script[src]").length;
	console.log(
		"[ERX-V16-RAW] loaded, bundle_probe_ran_before_me=" +
			R.bundle_probe_ran_before_me +
			" sidebar_header_defined=" +
			R.sidebar_header_defined
	);
})();
EOF

echo "== 3. python packaging (pyproject + .pth, no pip) =="
cat > "$ROOT/pyproject.toml" <<'EOF'
[project]
name = "erx_spike"
version = "0.0.1"
description = "throwaway probe app for ERX-001 V-16"
requires-python = ">=3.10"
dependencies = []

[build-system]
requires = ["flit_core >=3.4,<4"]
build-backend = "flit_core.buildapi"
EOF

SP=$(ls -d $BENCH/env/lib/python*/site-packages)
echo "$ROOT" > "$SP/$APP.pth"
echo "   .pth -> $SP/$APP.pth"

echo "== 4. register in sites/apps.txt =="
# NOTE (observed): this bench's sites/apps.txt has NO trailing newline, so a
# plain `echo >>` yields "erpnexterx_spike" and install-app dies with
# "App erx_spike not in apps.txt". Rewrite the whole file instead.
if ! grep -qx "$APP" "$BENCH/sites/apps.txt"; then
	printf '%s\n' "$APP" >> "$BENCH/sites/apps.txt"
	# collapse any glued line produced by a missing trailing newline
	awk 'BEGIN{RS="\n"} {print}' "$BENCH/sites/apps.txt" > "$BENCH/sites/apps.txt.tmp"
	printf 'frappe\nerpnext\n%s\n' "$APP" > "$BENCH/sites/apps.txt"
	rm -f "$BENCH/sites/apps.txt.tmp"
fi
cat -A "$BENCH/sites/apps.txt"

echo "== 5. assets symlink (same shape as frappe/erpnext) =="
ln -sfn "$ROOT/$APP/public" "$BENCH/sites/assets/$APP"
ls -la "$BENCH/sites/assets/" | grep "$APP"

echo "== 6. import check =="
cd "$BENCH"
./env/bin/python -c "import erx_spike.hooks as h; print('hooks ok, app_include_js =', h.app_include_js)"

echo "== 7. install on site =="
bench --site "$SITE" install-app "$APP" 2>&1 | tail -5

echo "== 8. installed apps =="
bench --site "$SITE" list-apps 2>&1 | tail -10

echo "SETUP DONE"
