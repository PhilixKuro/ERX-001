"""TS-017 第 2 步：覆盖清单逐条判（容器内 env/bin/python 跑）。写新 translation_overrides.py 与判定附表。"""
import sys
sys.path.insert(0, "/workspace/frappe-bench/apps/frappe_china")
from pathlib import Path
from frappe_china.tests import test_translation_quality as q
import subprocess, types
# 原清单从 HEAD 只读取出（本脚本会覆写工作区的 translation_overrides.py，可重复跑）
_src = subprocess.run(["git", "-C", "/workspace/frappe-bench/apps/frappe_china", "show",
                       "af015fa:frappe_china/tests/translation_overrides.py"], check=True, capture_output=True, text=True).stdout
_mod = types.ModuleType("orig_overrides"); exec(_src, _mod.__dict__)
OVERRIDES = _mod.OVERRIDES
from frappe_china.tests.test_named_terms import NAMED_TERMS

OWN = {  # A15 ①：本 app 自有源词，cn_tax 字段 label
    "Formula": "本 app 自有源词（cn_tax `Cash Flow Code.formula`；S5 装序检查探针 `install.PROBE_SOURCE`）",
    "Yearly Amount": "本 app 自有源词（cn_tax `Cash Flow Subtotal.yearly_amount`；避开法定列头「本年累计金额」，S4 LG-134）",
}
NAMED_BASIS = {
    "Dr": "DEC-003／022（S3 DEC-081）",
    "Setup": "DEC-019",
    "Payment References": "DEC-014",
    "Payment Entry Reference": "DEC-014",
    "Cash Flow": "DEC-015（原生报表保留官方）",
    "Closed Date": "DEC-021",
    "Create Chart Of Accounts Based On": "DEC-021",
    "Accounts Receivable": "S3 术语标准 §2.3（保留）",
    "Debtors": "S3 术语标准 §2.3（科目名，保留）",
    "Receivable": "S3 术语标准 §2.3（现值同官方，演示撞名在 TS-019 按 §2.3 判）",
    "Agents": "DEC-001（需求 §4.2.2 必改条目）",
    "Bot": "DEC-001（需求 §4.2.2 必改条目）",
    "Create Quotation": "DEC-001（需求 §4.2.2 必改条目；单据用「单」，DEC-016）",
    "Add Row": "DEC-001（需求 §4.2.2 必改条目）",
    "Opening & Closing": "DEC-001（需求 §4.2.2 必改条目，原误译）",
}

def decide(key, ov):
    problems = q.guard_problems([[key, ov.ours]])
    if problems:
        return "删", "ours 命中守卫：" + "；".join(p.split(":")[0] for p in problems)
    if key in OWN:
        return "留", OWN[key]
    if "TS-014" in ov.basis:
        return "留", "DEC-026（R4 TS-014 整句修复）"
    if key in NAMED_TERMS:
        return "留", NAMED_BASIS[key]
    if "工时表" in ov.official and ov.ours == ov.official.replace("工时表", "工时单"):
        return "留", "DEC-016（Timesheet 全族）"
    return "删", "过守卫但指不出决策"

def py(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

kept, table = [], []
for key, ov in OVERRIDES.items():
    verdict, basis = decide(key, ov)
    table.append((key, ov.official, ov.ours, verdict, basis))
    if verdict == "留":
        kept.append((key, ov, basis))

lines = ["from typing import NamedTuple", "", "", "class Override(NamedTuple):", "\tofficial: str", "\tours: str", "\tbasis: str", "",
         "", "# 覆盖官方译名的 csv 行，逐条写真实依据（S6 R6 方案 TS-017；依据形态见 test_translations.test_override_basis_forms）",
         "OVERRIDES: dict[str, Override] = {"]
for key, ov, basis in sorted(kept, key=lambda item: (item[0].casefold(), item[0])):
    lines.append(f"\t{py(key)}: Override({py(ov.official)}, {py(ov.ours)}, {py(basis)}),")
lines.append("}")
out = Path("/workspace/frappe-bench/apps/frappe_china/frappe_china/tests/translation_overrides.py")
out.write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))

md = ["# P1-S6-R7 D 回执附表：覆盖清单逐条判定（TS-017 第 2 步）", "",
      f"原 {len(OVERRIDES)} 条；留 {len(kept)} 条、删 {len(OVERRIDES) - len(kept)} 条。判定脚本 `Spike/P1S6R7/ts017_rebuild.py`。", "",
      "| 键 | 官方 | ours | 判定 | 依据／原因 |", "|---|---|---|---|---|"]
esc = lambda s: s.replace("|", chr(92) + "|").replace(chr(10), chr(92) + "n")
for row in sorted(table, key=lambda r: (r[3] != "留", r[0].casefold())):
    md.append("| " + " | ".join(f"`{esc(row[0])}`" if i == 0 else esc(row[i]) for i in range(5)) + " |")
Path(sys.argv[1]).write_text("\n".join(md) + "\n", encoding="utf-8")
print({"total": len(OVERRIDES), "kept": len(kept)})
