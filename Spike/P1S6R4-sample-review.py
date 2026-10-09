"""Classify obvious untranslated or mixed-English rows in the fixed sample."""
import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / "Spike/P1S6R4-sample.out.csv"
REPORT = ROOT / "Spike/P1S6R4-sample-review.json"
ALLOW = {
    "AI", "API", "BOM", "CRM", "CSV", "ERPNext", "Exotel", "Frappe",
    "HTML", "Insights", "Item", "Jinja", "Lead", "Markdown", "PDF",
    "Raven", "Yahoo", "ZIP",
    "Outlook.com", "Sendgrid", "Verdana",
}
TOKEN = re.compile(r"(?<![A-Za-z])[A-Za-z][A-Za-z0-9_.'-]*(?![A-Za-z])")


def main():
    with SHEET.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    reviewed = []
    counts = Counter()
    for app, key, refs, translation, _judgment, _reason in rows[1:]:
        words = [word for word in TOKEN.findall(translation)
                 if word not in ALLOW and not word.isupper()]
        has_placeholder = "???" in translation or "中文：" in translation
        if has_placeholder:
            reason = "占位译文或原文未译"
        elif words:
            reason = "残留英文词或英文句法：" + ", ".join(words[:5])
        else:
            reason = ""
        judgment = "不可用" if reason else "可用"
        if reason:
            counts["占位/未译" if has_placeholder else "混合英文"] += 1
        reviewed.append([app, key, refs, translation, judgment, reason])
    with SHEET.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["app", "源词", "出处", "译文", "判定", "不可用原因"])
        writer.writerows(reviewed)
    bad = [
        {"app": row[0], "key": row[1], "translation": row[3], "reason": row[5]}
        for row in reviewed if row[4] == "不可用"
    ]
    report = {"rows": len(reviewed), "usable": len(reviewed) - len(bad),
              "unusable": len(bad), "error_types": dict(counts),
              "sample_counts_by_app": dict(Counter(row[0] for row in reviewed)),
              "unusable_rows": bad,
              "method_note": "规则辅助初筛；英文词残留统一判不可用，品牌/代码白名单见脚本，需裁决后再修订全批。"}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "unusable_rows"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
