"""Build the S6 zh.csv batch from official empty zh.po entries.

The script is intentionally repeatable: it keeps a cache of source -> machine
translation, preserves placeholders, and writes only keys that are still
missing from the merged catalogue.  Named S6 terms are applied after the
translation pass so they are deterministic and reviewable.
"""
from __future__ import annotations

import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "frappe-bench"
OUT = ROOT / "Spike" / "P1S6R4-translate-cache.json"
CSV_PATH = BENCH / "apps" / "frappe_china" / "frappe_china" / "translations" / "zh.csv"
APPS = ("frappe", "erpnext", "crm", "hrms", "insights", "raven")

TOKEN = re.compile(r"\{\{?\s*[^{}]+\s*\}?\}|\{\d+\}|%\([^)]*\)s|%s|<[^>]+>")
WORD = re.compile(r"[A-Za-z\u4e00-\u9fff]")

# Terms frozen by S3/S6 decisions.  Context keys use the CSV third column.
NAMED: dict[str, str] = {
    "Dr": "借方",
    "Setup": "基础设置",
    "Setup:Workstation": "调机",
    "Payment References": "核销明细",
    "Payment Entry Reference": "核销明细",
    "Cash Flow Worksheet": "现金流量底稿",
    "Cash Flow": "现金流量表",
    "Item": "物料",
    "Create Chart Of Accounts Based On": "科目表建立方式",
    "Disable Opening Balance Calculation": "不计算期初余额",
    "Closed Date": "实际成交日期",
    "Business Flow": "业务流程",
    "Master Data": "基础资料",
    "Finance": "财务",
    "AI Assistant": "AI 分析助手",
    "Accounts Setup": "账务设置",
    "HR Setup": "人事设置",
    "Is Sales Item": "是否销售物料",
    "Create Quotation": "创建报价单",
    "View Customer": "查看客户",
    "Add Row": "添加行",
    "Agents": "智能体",
    "Bot": "机器人",
    "Accounts Receivable": "应收账款",
    "Debtors": "应收账款",
    "Receivable": "应收账款",
    "Opening & Closing": "期初与期末",
    "Unpaid:Sales Invoice": "未收款",
    "Paid:Sales Invoice": "已收款",
    "Unpaid:Purchase Invoice": "未付款",
    "Paid:Purchase Invoice": "已付款",
}


def parse_po(path: Path):
    if not path.exists():
        return []
    entries = []
    cur = {"id": "", "context": None, "str": ""}
    field = None
    for line in [*path.read_text(encoding="utf-8-sig").splitlines(), ""]:
        if not line.strip():
            if cur["id"]:
                entries.append(cur)
            cur = {"id": "", "context": None, "str": ""}
            field = None
        elif line.startswith("msgctxt "):
            field = "context"; cur[field] = json.loads(line[8:])
        elif line.startswith("msgid "):
            field = "id"; cur[field] = json.loads(line[6:])
        elif line.startswith("msgstr "):
            field = "str"; cur[field] = json.loads(line[7:])
        elif line.startswith('"') and field:
            cur[field] += json.loads(line)
    return entries


def current_rows():
    rows = []
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    return rows


def current_keys(rows):
    return {r[0] + (":" + r[2] if len(r) == 3 and r[2] else "") for r in rows}


def missing_entries():
    """Return (key, source, context) for all empty official translations."""
    existing = current_keys(current_rows())
    result = {}
    for app in APPS:
        for e in parse_po(BENCH / "apps" / app / app / "locale" / "zh.po"):
            if e["str"]:
                continue
            key = e["id"] + ((":" + e["context"]) if e["context"] else "")
            if key not in existing:
                result.setdefault(key, (e["id"], e["context"]))
    # DocType labels and Select options are represented in baseline output but
    # may not have a gettext entry.  Include those keys from its gap report.
    baseline = json.loads((ROOT / "Spike" / "P1S6R4-baseline.out.json").read_text(encoding="utf-8"))
    for items in baseline["gaps"].values():
        for key, _refs in items:
            if key not in existing and key not in result:
                # A colon in a source label is part of the source unless an
                # exact PO key above established a context split.
                result[key] = (key, None)
    return sorted((key, source, context) for key, (source, context) in result.items())


def translate_one(source: str) -> str:
    if not WORD.search(source) or not re.search(r"[A-Za-z]", source):
        return source
    # Keep HTML/code samples and identifiers stable.  The translation service
    # handles ordinary UI strings well; these are not user-facing prose.
    if re.fullmatch(r"[A-Z][A-Z0-9_./:-]{0,30}", source) or source.startswith("<p>"):
        return source
    r = requests.get(
        "https://translate.googleapis.com/translate_a/single",
        params={"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": source},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    return "".join(part[0] for part in (data[0] or []) if part and part[0])


def preserve_tokens(source: str, translated: str) -> str:
    src = TOKEN.findall(source)
    got = TOKEN.findall(translated)
    if src == got:
        return translated
    # Remove service-side token rewrites and append the exact source tokens.
    plain = translated
    for token in got:
        plain = plain.replace(token, "", 1)
    if src:
        return plain.rstrip() + " " + " ".join(src)
    return translated


def main():
    cache = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    missing = missing_entries()
    sources = sorted({source for _key, source, _ctx in missing if source not in cache})
    print(f"missing keys={len(missing)}, untranslated sources={len(sources)}")
    with ThreadPoolExecutor(max_workers=12) as pool:
        jobs = {pool.submit(translate_one, source): source for source in sources}
        for i, job in enumerate(as_completed(jobs), 1):
            source = jobs[job]
            try:
                cache[source] = preserve_tokens(source, job.result())
            except Exception as exc:  # retryable; leave source visible in report
                print(f"translation failed: {source!r}: {exc}")
                cache[source] = source
            if i % 100 == 0:
                OUT.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rows = current_rows()
    seen = current_keys(rows)
    # New rows are the batch section.  Keep deterministic source/context order.
    for key, source, context in missing:
        if key in seen:
            continue
        target = NAMED.get(key, cache.get(source, source))
        if context and key not in NAMED:
            target = cache.get(source, source)
        rows.append([source, target, context] if context else [source, target])
        seen.add(key)
    # Replace named terms already present in the file as well.
    for row in rows:
        key = row[0] + ((":" + row[2]) if len(row) == 3 and row[2] else "")
        if key in NAMED:
            row[1] = NAMED[key]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(rows)
    print(f"wrote {len(rows)} rows; cache={len(cache)}")


if __name__ == "__main__":
    main()
