"""TS-019 回执附表：① 演示线档定词表（源词／出处／译文）② S3 改词占用重查表 ③ 撞名判定表。宿主 python -I -X utf8 跑。"""
import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/01-需求摸底/S06-译名与导航/R07-代码/P1-S6-R7-D附表-演示线定词.md"
esc = lambda s: (s or "").replace("|", "\|").replace("\n", "\n")
md = ["# P1-S6-R7 D 回执附表：演示线定词（TS-019）", ""]
# ①
items = {}
for f in sorted((ROOT / "Spike/P1S6R6-demo").glob("in-*.json")):
    for it in json.loads(f.read_text(encoding="utf-8"))["items"]:
        items[it["key"]] = it["refs"][0] if it["refs"] else ""
rows = []
for f in sorted((ROOT / "Spike/P1S6R6-demo").glob("part-*.csv")):
    for r in csv.reader(f.open(encoding="utf-8", newline="")):
        if r:
            k = r[0] + (":" + r[2] if len(r) == 3 and r[2] else "")
            rows.append((k, items.get(k, ""), r[1]))
md += [f"## 一、演示面无中文键逐条定词（{len(rows)} 条；另 Excel／WhatsApp／ERPNext 进白名单、35 个编号规则等代码值进白名单）", "",
       "| 源词 | 出处（首个） | 译文 |", "|---|---|---|"]
md += [f"| `{esc(k)}` | {esc(ref.replace('frappe-bench/apps/', ''))} | {esc(t)} |" for k, ref, t in sorted(rows, key=lambda x: x[0].casefold())]
# ②
recheck = json.loads((ROOT / "Spike/P1S6R7/s3_recheck.json").read_text(encoding="utf-8"))
written = {r["key"]: r for r in json.loads((ROOT / "Spike/P1S6R7/s3_rows.json").read_text(encoding="utf-8"))}
md += ["", f"## 二、S3 收付款方向与改词组占用重查（{len(recheck)} 个键；S3 实数 75 组改，草案记 73）", "",
       "| 键 | S3 原定 | 冲突源词（占用者） | 改定／落法 |", "|---|---|---|---|"]
for r in recheck:
    w = written.get(r["key"], {})
    occ = ", ".join(r.get("occupants") or []) or "无"
    act = w.get("action", "")
    final = r["target"] or "（不写）"
    note = w.get("why", "") or r.get("note", "")
    md.append(f"| `{esc(r['key'])}` | {esc(r['s3_target'])} | {esc(occ)} | {esc(final)}；{esc(act)}：{esc(note)} |")
md += ["", "占用者 7 处的判定：`Defaults`／`Default Value`、`Discounted Amount`／`Amount after discount`、`Done`／`processed`、`Dr`／`Debit`、`Incoming Rate (Costing)`／`Outgoing Rate`、`More Information`／`Additional Information `、`Paid`／`Is Paid` —— 前六处占用者与之同义（S3 DEC-075 同义判据）；`Is Paid` 本轮同改为「是否已付」，占用随之消解。不改 S3 新词。"]
# ③
table = json.loads((ROOT / "Spike/P1S6R7/collision_table.json").read_text(encoding="utf-8"))
eff = json.loads((ROOT / "Spike/P1S6R7/collision_effective.json").read_text(encoding="utf-8"))
md += ["", f"## 三、演示撞名判定（基线 {eff['groups']} 组：context 行已解 {eff['resolved_by_context']} 组；仍撞 {eff['still']} 组）", "",
       "### 3.1 异义，定唯一用词", "", "| 源词 | 定词 | 落法 | 占用核查 | 理由 |", "|---|---|---|---|---|"]
for t in table:
    if "rows" in t:
        md.append(f"| `{esc(t['source'])}` | {esc(t['target'])} | {esc('、'.join(t['rows']))} | {esc(', '.join(t['occupants']) or '无占用')} | {esc(t['why'])} |")
md += ["", "### 3.2 同义保留", "", "| 目标词 | 源词 | 依据 |", "|---|---|---|"]
for t in table:
    if t.get("verdict"):
        md.append(f"| {esc(t['group'])} | {esc(' / '.join(t['sources']))} | {esc(t['why'])} |")
md += ["", "### 3.3 已由 context 行解开的组", "", "、".join(eff["resolved_groups"])]
OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
print(OUT, len(md))
