# V-18 segment 3b: redo segment 3's "A" check with the chart name properly
# percent-encoded.  In 3a the Chinese name went into the query string raw, the
# name never matched, and the response came back as Taiwan's chart -- which is
# itself worth recording, because it exposes a second defect in zelin's
# get_chart: on a no-match it does `return chart`, and `chart` is whatever raw
# file text the loop last read (a str, not a tree dict), whereas erpnext's own
# get_chart falls off the end and returns None.
#
# This probe separates the two: with correct encoding, does the whitelisted HTTP
# route hand back the right tree?  And what does each implementation return for
# a name that genuinely does not exist?
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V18-seg3b-http-getchart.py

import json
import subprocess
import urllib.parse

import frappe

SITE = "erx.localhost"
CHART = "小企业会计准则(2024)"
BASE = "http://127.0.0.1:8000"
COOKIE = "/tmp/v18-cookies-b.txt"
OUT = "/workspace/Spike/V18-out/seg3b-http-getchart.json"

result = {"segment": "3b whitelisted get_chart over HTTP, name properly encoded"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


def curl(path, data=None, method="GET"):
    cmd = ["curl", "-s", "-S", "-w", "\n__HTTP__%{http_code}",
           "-H", "Host: erx.localhost", "-H", "Accept: application/json",
           "-b", COOKIE, "-c", COOKIE]
    if data is not None:
        cmd += ["-X", "POST", "-H", "Content-Type: application/json", "-d", json.dumps(data)]
    cmd.append(BASE + path)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    body, _, code = p.stdout.rpartition("\n__HTTP__")
    return code.strip(), body


subprocess.run(["rm", "-f", COOKIE])
frappe.init(site=SITE)
pw = frappe.get_site_config().get("admin_password") or "admin"
frappe.destroy()
code, _ = curl("/api/method/login", {"usr": "Administrator", "pwd": pw})
rec("login_http_code", code)

# properly encoded, via POST body (no query-string encoding ambiguity at all)
code, body = curl(
    "/api/method/erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_chart",
    {"chart_template": CHART})
rec("post_body_http_code", code)
try:
    msg = json.loads(body).get("message")
    rec("post_body_message_type", type(msg).__name__)
    rec("post_body_toplevel_keys", list(msg.keys()) if isinstance(msg, dict) else repr(msg)[:200])
    if isinstance(msg, dict):
        rec("post_body_root_types", {k: v.get("root_type") for k, v in msg.items()
                                     if isinstance(v, dict)})
except Exception as e:
    rec("post_body_parse_error", f"{e}: {body[:300]}")

# and via a properly percent-encoded query string
enc = urllib.parse.quote(CHART, safe="")
rec("percent_encoded_name", enc)
code, body = curl(
    "/api/method/erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_chart"
    f"?chart_template={enc}")
rec("qs_http_code", code)
try:
    msg = json.loads(body).get("message")
    rec("qs_message_type", type(msg).__name__)
    rec("qs_toplevel_keys", list(msg.keys()) if isinstance(msg, dict) else repr(msg)[:200])
except Exception as e:
    rec("qs_parse_error", f"{e}: {body[:300]}")

# what do the two implementations return for a name that truly does not exist?
frappe.init(site=SITE)
frappe.connect()
from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa_mod
from erx_v18.chart_of_accounts.custom_accounts import custom_account as app_mod

for label, fn in (("erpnext_native", coa_mod.get_chart), ("zelin_copy", app_mod.get_chart)):
    got = fn("绝不存在的科目表名")
    rec(f"nomatch_{label}_type", type(got).__name__)
    rec(f"nomatch_{label}_repr_head", repr(got)[:160])
frappe.destroy()

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print(f"\nwrote {OUT}", flush=True)
