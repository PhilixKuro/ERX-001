"""TS-021 残余缺口清理（容器内 env/bin/python 跑；默认只报告，--write 才落盘）。
① csv 里译文与源词相同、且不含汉字的行（产品名、技术名原样）：基线把它算缺口，删行回落官方／原文，键进 UNTRANSLATED。
② main.pot 从 TSX 抽出时把 JS 字符串的转义换行记成字面反斜杠 n 的键：运行时是真换行，由换行后的 csv 行生效，
   字面写法本身在 csv 里无法表达（Frappe 读 csv 会把源词的反斜杠 n 换成换行），故字面键进 UNTRANSLATED 写理由。
③ 指定键直接进 UNTRANSLATED（EXTRA）。
另查 csv 按 Frappe 读法（反斜杠 n → 换行）有无撞键。"""
import csv, importlib.util, re, sys
sys.path.insert(0, "/workspace/Spike/P1S6R7"); argv = sys.argv[1:]; sys.argv = ["x"]
import apply_rows as a
spec = importlib.util.spec_from_file_location("bl", "/workspace/Spike/P1S6R4-baseline.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
WL = "/workspace/frappe-bench/apps/frappe_china/frappe_china/tests/translation_whitelist.py"
CJK = re.compile(r"[一-鿿]")
EXTRA = {"<hr>": "纯 HTML 标签，无可译文字",
         "<table class='table table-bordered'><tr><th>{0}</th><th>{1}</th></tr>": "纯 HTML 标签与占位符，无可译文字",
         "johndoe@mail.com": "示例邮箱地址，原样显示"}
NL_REASON = ("main.pot 从 TSX 抽出时把 JS 字符串里的转义换行记成了字面反斜杠 n；运行时是真换行，"
             "由同句换行写法的 csv 行生效（Frappe 读 csv 时把源词的反斜杠 n 换成换行）")
rows = a.read_rows(a.CSV_PATH)
identity = [r for r in rows if r[1].strip() == r[0].strip() and not CJK.search(r[1])]
norm = {}
dups = []
for r in rows:
    k = a.key_of(r)
    if k in norm: dups.append(k)
    norm[k] = r
merged, _ = bl.merged_dict()
literal = []
for app in bl.APPS[:-1]:
    for e in bl.parse_po(bl.app_path(app) / "locale/main.pot"):
        k = bl.entry_key(e)
        if "\\n" in k and not (merged.get(k) and CJK.search(merged[k])):
            v = merged.get(k.replace("\\n", "\n"))
            if v and CJK.search(v):
                literal.append(k)
print({"identity_rows": [a.key_of(r) for r in identity], "runtime_dups": dups, "literal_nl_keys": len(literal)})
if "--write" not in argv:
    sys.exit(0)
drop = {a.key_of(r) for r in identity}
kept = [r for r in rows if a.key_of(r) not in drop]
with open(a.CSV_PATH, "w", encoding="utf-8", newline="") as h:
    csv.writer(h, lineterminator="\n").writerows(kept)
a.write_overrides({k: v for k, v in a.OVERRIDES.items() if k not in drop})
text = open(WL, encoding="utf-8", newline="").read()
add = {**{k: "产品名或技术名，原样显示" for k in sorted(drop)}, **{k: NL_REASON for k in literal}, **EXTRA}
i = text.rindex("}")
lines = "".join(f"\t{k!r}: {v!r},\r\n" for k, v in add.items() if f"\t{k!r}:" not in text)
open(WL, "w", encoding="utf-8", newline="").write(text[:i] + lines + text[i:])
print({"csv_total": len(kept), "whitelist_added": lines.count("\r\n")})
