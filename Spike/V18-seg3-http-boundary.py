# V-18 segment 3: the boundary segments 1a/1b did not touch -- the REAL path a
# user takes.  1a/1b both ran in-process (`env/bin/python script.py`), while a
# human creates a company through the desk UI, i.e. over HTTP through
# frappe/handler.py -- and handler.py IS one of the four places
# override_whitelisted_method() is consulted.
#
# So this asks: does going over HTTP change the answer?  Two things get checked:
#   A. the whitelisted route /api/method/...get_charts_for_country and ...get_chart
#      -- do they return the app's chart (they should: handler.py dispatches
#      through the override)?  This is what populates the desk's chart dropdown.
#   B. a company actually created over HTTP (frappe.client.insert), so
#      Company.on_update -> create_default_accounts -> create_charts runs inside
#      a real request.  Does the override reach create_charts there?
#
# B is the decisive one: if it fails over HTTP the same way it failed in 1a, the
#1a failure is not an artifact of running in-process.
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V18-seg3-http-boundary.py

import json
import subprocess

import frappe

SITE = "erx.localhost"
COMPANY = "V18原生丙"
ABBR = "V18C"
CHART = "小企业会计准则(2024)"
BASE = "http://127.0.0.1:8000"
OUT = "/workspace/Spike/V18-out/seg3-http-boundary.json"

result = {"segment": "3 HTTP / desk boundary"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


def curl(path, data=None, cookie=None, method="GET"):
    cmd = ["curl", "-s", "-S", "-w", "\n__HTTP__%{http_code}",
           "-H", "Host: erx.localhost", "-H", "Accept: application/json"]
    if cookie:
        cmd += ["-b", cookie, "-c", cookie]
    elif cookie is not None:
        cmd += ["-c", cookie]
    if data is not None:
        cmd += ["-X", method if method != "GET" else "POST",
                "-H", "Content-Type: application/json", "-d", json.dumps(data)]
    cmd.append(BASE + path)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    body, _, code = p.stdout.rpartition("\n__HTTP__")
    return code.strip(), body


COOKIE = "/tmp/v18-cookies.txt"
subprocess.run(["rm", "-f", COOKIE])

# admin password from site_config
frappe.init(site=SITE)
pw = frappe.get_site_config().get("admin_password") or "admin"
frappe.destroy()

code, body = curl("/api/method/login", {"usr": "Administrator", "pwd": pw}, cookie=COOKIE, method="POST")
rec("login_http_code", code)
rec("login_body", body[:200])
if code != "200":
    rec("FATAL", "could not log in over HTTP")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1, default=str)
    raise SystemExit(2)

# ---- A. whitelisted routes (what the desk dropdown / tree view call) --------
code, body = curl(
    "/api/method/erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country"
    "?country=China", cookie=COOKIE)
rec("A_get_charts_for_country_http_code", code)
rec("A_get_charts_for_country_body", body[:600])

code, body = curl(
    "/api/method/erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_chart"
    "?chart_template=" + CHART, cookie=COOKIE)
rec("A_get_chart_http_code", code)
try:
    parsed = json.loads(body)
    msg = parsed.get("message")
    rec("A_get_chart_toplevel_keys", list(msg.keys()) if isinstance(msg, dict) else repr(msg)[:200])
except Exception as e:
    rec("A_get_chart_parse_error", f"{e}: {body[:300]}")

# ---- B. create a company over HTTP -----------------------------------------
frappe.init(site=SITE)
frappe.connect()
exists = frappe.db.exists("Company", COMPANY)
acc_before = frappe.db.count("Account")
err_before = frappe.db.count("Error Log")
base_before = frappe.db.count("Account", {"company": "华东弹簧"})
frappe.destroy()
rec("B_company_existed_before", bool(exists))
rec("B_account_count_before", acc_before)
rec("B_error_log_before", err_before)
rec("B_baseline_accounts_before", base_before)

if exists:
    rec("B_SKIPPED", f"{COMPANY} already exists")
else:
    code, body = curl("/api/resource/Company", {
        "company_name": COMPANY,
        "abbr": ABBR,
        "default_currency": "CNY",
        "country": "China",
        "chart_of_accounts": CHART,
        "create_chart_of_accounts_based_on": "Standard Template",
    }, cookie=COOKIE, method="POST")
    rec("B_insert_http_code", code)
    rec("B_insert_body_head", body[:3000])
    result["B_insert_body_full"] = body

frappe.init(site=SITE)
frappe.connect()
rec("B_company_exists_after", bool(frappe.db.exists("Company", COMPANY)))
rec("B_account_count_for_company", frappe.db.count("Account", {"company": COMPANY}))
rec("B_account_count_total_after", frappe.db.count("Account"))
rec("B_baseline_accounts_after", frappe.db.count("Account", {"company": "华东弹簧"}))
rec("B_error_log_after", frappe.db.count("Error Log"))
rec("B_error_logs_recent", frappe.get_all(
    "Error Log", fields=["name", "method", "creation"], order_by="creation desc", limit=6))
if frappe.db.count("Account", {"company": COMPANY}):
    rec("B_roots", frappe.get_all(
        "Account", filters={"company": COMPANY, "parent_account": ("is", "not set")},
        fields=["account_number", "account_name", "root_type"], order_by="account_number"))
frappe.destroy()

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print(f"\nwrote {OUT}", flush=True)
