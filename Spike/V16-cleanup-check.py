# V-16 cleanup verification + stale-entry removal.
#
# Run inside the container:
#   docker exec -w /workspace/frappe-bench erx001-frappe-1 \
#     ./env/bin/python /workspace/Spike/V16-cleanup-check.py
#
# `bench uninstall-app` removes the app from the SITE (Module Def, Desktop
# Icons, Workspace Sidebars, installed_apps) but does NOT touch
# sites/assets/assets.json, so the erx_spike.bundle.js -> dist path mapping
# written by `bench build` survives and is still serialized into every desk
# page's boot payload. That is a probe artifact, so remove it here and report
# whatever else still mentions the throwaway app.
#
# ASCII only on purpose (Windows/GBK).

import json
import os

BENCH = "/workspace/frappe-bench"
APP = "erx_spike"

print("== 1. assets json files ==")
for fname in ("assets.json", "assets-rtl.json"):
    path = os.path.join(BENCH, "sites/assets", fname)
    if not os.path.exists(path):
        print(f"   {fname}: absent")
        continue
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    stale = [k for k, v in data.items() if APP in k or APP in str(v)]
    if stale:
        for k in stale:
            print(f"   {fname}: removing stale entry {k} -> {data[k]}")
            del data[k]
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=4)
            fh.write("\n")
        print(f"   {fname}: {len(stale)} entry(ies) removed, {len(data)} left")
    else:
        print(f"   {fname}: clean ({len(data)} entries)")

print("== 2. filesystem ==")
for p in (
    f"{BENCH}/apps/{APP}",
    f"{BENCH}/sites/assets/{APP}",
    f"{BENCH}/env/lib/python3.14/site-packages/{APP}.pth",
):
    print(f"   {'PRESENT' if os.path.exists(p) else 'gone   '}  {p}")

with open(f"{BENCH}/sites/apps.txt", "rb") as fh:
    raw = fh.read()
print(f"   sites/apps.txt bytes = {raw!r}")

print("== 3. database leftovers ==")
import frappe

frappe.init(site="erx.localhost", sites_path=f"{BENCH}/sites")
frappe.connect()
try:
    print("   installed_apps      :", frappe.get_installed_apps())
    print("   all_apps (apps.txt) :", frappe.get_all_apps())
    checks = [
        ("Module Def", {"app_name": APP}),
        ("Desktop Icon", {"module_name": ("like", "%Erx Spike%")}),
        ("Workspace Sidebar", {"name": ("like", "%Erx%")}),
        ("DocType", {"module": ("like", "%Erx Spike%")}),
    ]
    for dt, filt in checks:
        try:
            rows = frappe.get_all(dt, filters=filt, pluck="name")
            print(f"   {dt:20s}: {rows if rows else 'none'}")
        except Exception as exc:
            print(f"   {dt:20s}: query failed ({exc})")
finally:
    frappe.destroy()

print("DONE")
