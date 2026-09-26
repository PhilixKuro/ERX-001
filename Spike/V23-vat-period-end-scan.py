#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V-23 探针：saoxia-erpnext_china 是否实现「月末结转 / 增值税期末结转」

命题：Reference/saoxia-erpnext_china/ 是否含 进项税额转出 / 转出未交增值税 /
      未交增值税 的期末结转实现？若有，形态是 Journal Entry 模板、自有 DocType，
      还是脚本？

只读探针。不复制任何源文件，不创建 saoxia 目录下的文件，不跑其安装器。
不回显手机号等个人数据（命中即只记路径与计数，不打印行内容）。

用法：
  set PYTHONUTF8=1 && set PYTHONIOENCODING=utf-8 && python V23-vat-period-end-scan.py
输出：V23-vat-period-end-scan.out.json
"""

import json
import os
import re
import sys
from collections import defaultdict

REPO = r"D:/ERX-001/Reference/saoxia-erpnext_china"
APP = os.path.join(REPO, "erpnext_china")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "V23-vat-period-end-scan.out.json")

# 同义关键词分组。分组是为了区分「命中了会计结转」与「只命中了无关的
# closing/period 字样」——后者在 CRM/HR 代码里到处有，不能当证据。
KEYWORDS = {
    # A 组：直接指向中国增值税期末结转的科目名与科目号
    "A_vat_cn_accounts": [
        "转出未交增值税", "未交增值税", "进项税额转出", "应交增值税",
        "销项税额", "进项税额", "2221003", "2221007", "2221020", "2221001",
        "2221002",
    ],
    # B 组：中文结转/期末语汇
    "B_cn_closing_terms": [
        "结转", "月末", "期末", "月结", "年结", "本月应交", "损益结转",
        "科目余额", "余额表",
    ],
    # C 组：ERPNext 侧的凭证与结转 API
    "C_erpnext_je_api": [
        "Journal Entry", "journal_entry", "JournalEntry",
        "Period Closing Voucher", "period_closing_voucher",
        "closing_account_head", "make_gl_entries", "GL Entry", "gl_entry",
    ],
    # D 组：英文结转/期末/税 语汇（宽口，噪声高，须逐条看上下文）
    "D_en_generic": [
        "carry_forward", "carryforward", "period_end", "month_end",
        "monthend", "periodend", "closing", "vat", "VAT", "tax_withholding",
        "Sales Taxes", "Purchase Taxes", "Account Head", "account_head",
        "fiscal_year", "Fiscal Year",
    ],
    # E 组：可能承载结转的宿主形态（报表 / 定时任务 / Check 字段分支）
    "E_hosting_forms": [
        "scheduler_events", "enqueue", "background_jobs", "execute(",
        "get_columns", "get_data", "frappe.throw", "docstatus",
        "is_submittable", "on_submit",
    ],
}

# 不读的二进制/无关后缀
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff",
            ".woff2", ".ttf", ".eot", ".pyc", ".zip", ".gz", ".map"}
# 隐私风险文件：命中只计数不回显
PRIVACY_HINT = re.compile(r"1[3-9]\d{9}")


def walk_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in SKIP_EXT:
                continue
            yield os.path.join(dirpath, fn)


def rel(p):
    return os.path.relpath(p, REPO).replace("\\", "/")


def main():
    result = {
        "proposition": "V-23 saoxia 是否实现增值税期末结转",
        "repo": REPO,
        "inventory": {},
        "keyword_hits": defaultdict(list),
        "keyword_zero": [],
        "privacy_files": [],
        "file_count": 0,
        "scanned_bytes": 0,
    }

    # ---- 1. 清单：模块、DocType 目录、Report 目录、fixtures、patches ----
    inv = result["inventory"]
    inv["modules_txt"] = _read(os.path.join(APP, "modules.txt")).splitlines()
    inv["patches_txt"] = [
        ln for ln in _read(os.path.join(APP, "patches.txt")).splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    for mod in ("erpnext_china", "hrms_china"):
        base = os.path.join(APP, mod)
        inv[f"{mod}_doctypes"] = _listdir(os.path.join(base, "doctype"))
        inv[f"{mod}_reports"] = _listdir(os.path.join(base, "report"))
        inv[f"{mod}_subdirs"] = _listdir(base)
    inv["fixtures_dir"] = _listdir(os.path.join(APP, "fixtures"))
    inv["setup_tree"] = sorted(
        rel(p) for p in walk_files(os.path.join(APP, "setup"))
    )
    inv["utils_tree"] = sorted(
        rel(p) for p in walk_files(os.path.join(APP, "utils"))
    )
    # DocType 的 is_submittable / 自定义字段落在哪个 module
    inv["doctype_json_flags"] = _doctype_flags()

    # ---- 2. 多同义词全库扫描 ----
    found_any = defaultdict(int)
    for path in walk_files(REPO):
        result["file_count"] += 1
        text = _read(path)
        if not text:
            continue
        result["scanned_bytes"] += len(text)

        if len(PRIVACY_HINT.findall(text)) > 20:
            # 疑似个人数据聚集文件：只记路径，不逐行回显
            result["privacy_files"].append(
                {"path": rel(path), "phone_like_count":
                 len(PRIVACY_HINT.findall(text))}
            )

        lines = text.splitlines()
        for group, kws in KEYWORDS.items():
            for kw in kws:
                if kw not in text:
                    continue
                found_any[kw] += 1
                # A/B/C 组逐行记行号（证据要求精确定位）；D/E 组只记文件+计数
                if group in ("A_vat_cn_accounts", "B_cn_closing_terms",
                             "C_erpnext_je_api"):
                    for i, ln in enumerate(lines, 1):
                        if kw in ln:
                            result["keyword_hits"][f"{group}:{kw}"].append(
                                {"file": rel(path), "line": i,
                                 "text": ln.strip()[:300]}
                            )
                else:
                    result["keyword_hits"][f"{group}:{kw}"].append(
                        {"file": rel(path),
                         "count": text.count(kw)}
                    )

    for group, kws in KEYWORDS.items():
        for kw in kws:
            if found_any.get(kw, 0) == 0:
                result["keyword_zero"].append(f"{group}:{kw}")

    result["keyword_hits"] = dict(result["keyword_hits"])
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    # ---- 3. 控制台摘要 ----
    print("=" * 70)
    print("V-23 扫描摘要")
    print("=" * 70)
    print(f"扫描文件数: {result['file_count']}  字节: {result['scanned_bytes']}")
    print(f"modules.txt: {inv['modules_txt']}")
    print(f"patches.txt 有效行: {inv['patches_txt'] or '（空——无 patch）'}")
    print(f"\nerpnext_china DocType ({len(inv['erpnext_china_doctypes'])}): "
          f"{inv['erpnext_china_doctypes']}")
    print(f"\nerpnext_china Report ({len(inv['erpnext_china_reports'])}): "
          f"{inv['erpnext_china_reports']}")
    print(f"\nhrms_china DocType ({len(inv['hrms_china_doctypes'])}): "
          f"{inv['hrms_china_doctypes']}")
    print(f"hrms_china Report ({len(inv['hrms_china_reports'])}): "
          f"{inv['hrms_china_reports']}")
    print(f"\nfixtures/: {inv['fixtures_dir']}")

    print("\n--- 零命中关键词（断言缺失的依据）---")
    for k in result["keyword_zero"]:
        print(f"  0  {k}")

    print("\n--- 有命中关键词 ---")
    for k, v in sorted(result["keyword_hits"].items()):
        files = {h["file"] for h in v}
        print(f"  {len(v):>4} 处 / {len(files):>2} 文件  {k}")
        for fp in sorted(files)[:6]:
            print(f"          {fp}")
        if len(files) > 6:
            print(f"          ...另 {len(files)-6} 个文件")

    if result["privacy_files"]:
        print("\n--- 疑似个人数据聚集文件（仅记路径，未回显内容）---")
        for pf in result["privacy_files"]:
            print(f"  {pf['phone_like_count']:>7} 处手机号样式  {pf['path']}")

    print(f"\n详细结果: {OUT}")


def _read(path):
    for enc in ("utf-8", "gb18030", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, OSError):
            continue
    return ""


def _listdir(path):
    if not os.path.isdir(path):
        return ["<目录不存在>"]
    return sorted(os.listdir(path))


def _doctype_flags():
    """列出 app 内所有 DocType 定义 json 的关键标志位。"""
    out = []
    for path in walk_files(APP):
        if not path.endswith(".json"):
            continue
        txt = _read(path)
        if '"doctype": "DocType"' not in txt:
            continue
        try:
            d = json.loads(txt)
        except Exception:
            continue
        out.append({
            "file": rel(path),
            "name": d.get("name"),
            "module": d.get("module"),
            "is_submittable": d.get("is_submittable", 0),
            "istable": d.get("istable", 0),
            "field_count": len(d.get("fields", [])),
        })
    return out


if __name__ == "__main__":
    sys.exit(main())
