# V-22 segment 1: build the throwaway fixtures and the Chinese-header sample
# statement files. Creates ONLY new documents; touches nothing pre-existing.
#
# Creates:
#   Account       V22测试银行存款 - HDS   (leaf, account_type Bank, CNY, under 银行账户 - HDS)
#   Bank          V22测试银行             (+ 7 Bank Transaction Mapping rows, Chinese file_field)
#   Bank Account  V22测试账户             (company account, points at the leaf account above)
#   Payment Entry one Receive of 1045.00 from 江南机械, reference_no V22REF20260922001
#   files         /workspace/Spike/V22-sample-statement.xlsx  and  .csv
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg1-setup.py

import json

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
ABBR = "HDS"
OUT = "/workspace/Spike/V22-out/seg1-setup.json"

ACC_NAME = "V22测试银行存款"
ACC = f"{ACC_NAME} - {ABBR}"
BANK = "V22测试银行"
BANK_ACCT_NAME = "V22测试账户"
BANK_ACCT = f"{BANK_ACCT_NAME} - {BANK}"
MATCH_REF = "V22REF20260922001"

result = {"segment": "1 setup fixtures + chinese sample files"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

# ---------------------------------------------------------------- 1. GL account
if frappe.db.exists("Account", ACC):
    rec("account_preexisting", ACC)
else:
    a = frappe.get_doc({
        "doctype": "Account",
        "account_name": ACC_NAME,
        "parent_account": f"银行账户 - {ABBR}",
        "company": COMPANY,
        "account_type": "Bank",
        "account_currency": "CNY",
        "is_group": 0,
    }).insert()
    rec("account_created", a.name)

# ------------------------------------------------- 2. Bank + the column mapping
# The mapping is the thing under test: Chinese column name -> Bank Transaction field.
# 借方发生额 = debit on the depositor statement = money OUT = withdrawal
# 贷方发生额 = credit on the depositor statement = money IN = deposit
MAPPING = [
    ("交易日期", "date"),
    ("摘要", "description"),
    ("贷方发生额", "deposit"),
    ("借方发生额", "withdrawal"),
    ("对方户名", "bank_party_name"),
    ("交易流水号", "reference_number"),
    ("币种", "currency"),
]

if frappe.db.exists("Bank", BANK):
    rec("bank_preexisting", BANK)
    bank = frappe.get_doc("Bank", BANK)
else:
    bank = frappe.get_doc({"doctype": "Bank", "bank_name": BANK})
    for file_field, bt_field in MAPPING:
        bank.append("bank_transaction_mapping",
                    {"file_field": file_field, "bank_transaction_field": bt_field})
    bank.insert()
    rec("bank_created", bank.name)

rec("bank_mapping_rows", [(d.file_field, d.bank_transaction_field)
                         for d in bank.bank_transaction_mapping])
rec("bank_mapping_count", len(bank.bank_transaction_mapping))

# ------------------------------------------------------------- 3. Bank Account
if frappe.db.exists("Bank Account", BANK_ACCT):
    rec("bank_account_preexisting", BANK_ACCT)
else:
    ba = frappe.get_doc({
        "doctype": "Bank Account",
        "account_name": BANK_ACCT_NAME,
        "bank": BANK,
        "account": ACC,
        "company": COMPANY,
        "is_company_account": 1,
    }).insert()
    rec("bank_account_created", ba.name)

rec("bank_account_row", frappe.db.get_value(
    "Bank Account", BANK_ACCT, ["name", "account", "company", "is_company_account"], as_dict=True))

# --------------------------------------------- 4. throwaway Payment Entry to match
# Receive 1045.00 from the demo customer, landing in the TEST bank account.
# reference_no is set on purpose: get_pe_matching_query line 1381-1382 adds
# `.where(pe.reference_no == transaction.reference_number)` whenever
# frappe.flags.auto_reconcile_vouchers is True, so auto-reconcile can only ever
# match a voucher whose reference_no equals the statement reference.
existing = frappe.get_all("Payment Entry", filters={"reference_no": MATCH_REF}, pluck="name")
if existing:
    rec("payment_entry_preexisting", existing)
else:
    try:
        pe = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": "Receive",
            "company": COMPANY,
            "posting_date": "2026-09-22",
            "party_type": "Customer",
            "party": "江南机械",
            "paid_from": f"应收账款 1 - {ABBR}",
            "paid_to": ACC,
            "paid_amount": 1045.00,
            "received_amount": 1045.00,
            "source_exchange_rate": 1,
            "target_exchange_rate": 1,
            "reference_no": MATCH_REF,
            "reference_date": "2026-09-22",
            "bank_account": BANK_ACCT,
        })
        pe.insert()
        pe.submit()
        rec("payment_entry_created", pe.name)
    except Exception:
        rec("payment_entry_ERROR", frappe.get_traceback())

rec("test_payment_entries", frappe.get_all(
    "Payment Entry", filters={"reference_no": MATCH_REF},
    fields=["name", "payment_type", "party", "paid_amount", "received_amount",
            "received_amount_after_tax", "paid_to", "paid_from", "posting_date",
            "reference_no", "clearance_date", "docstatus"]))

# ----------------------------------------- 5. the Chinese-header statement files
HEADERS = ["交易日期", "摘要", "借方发生额", "贷方发生额", "余额", "对方户名", "交易流水号", "币种"]
ROWS = [
    ["2026-09-22", "货款收入",  "",       "1045.00", "1045.00", "江南机械",       MATCH_REF,           "CNY"],
    ["2026-09-22", "电汇付款",  "750.00", "",        "295.00",  "宝钢弹簧钢丝",   "V22REF20260922002", "CNY"],
    ["2026-09-23", "手续费",    "12.50",  "",        "282.50",  "",               "V22REF20260923001", "CNY"],
    ["2026-09-23", "利息收入",  "",       "3.68",    "286.18",  "",               "V22REF20260923002", "CNY"],
    ["2026-09-24", "货款收入",  "",       "2000.00", "2286.18", "江南机械",       "V22REF20260924001", "CNY"],
    ["2026-09-24", "差旅报销",  "480.00", "",        "1806.18", "",               "V22REF20260924002", "CNY"],
]
rec("sample_headers", HEADERS)
rec("sample_row_count", len(ROWS))

import csv as _csv

import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "对账单"
ws.append(HEADERS)
for r in ROWS:
    ws.append(r)
XLSX = "/workspace/Spike/V22-sample-statement.xlsx"
wb.save(XLSX)
rec("wrote_xlsx", XLSX)

CSV = "/workspace/Spike/V22-sample-statement.csv"
with open(CSV, "w", encoding="utf-8", newline="") as f:
    w = _csv.writer(f)
    w.writerow(HEADERS)
    w.writerows(ROWS)
rec("wrote_csv", CSV)

frappe.db.commit()

for dt in ("Bank Transaction", "Payment Entry", "Bank Account", "Bank", "Error Log"):
    rec(f"count_after_setup_{dt}", frappe.db.count(dt))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
