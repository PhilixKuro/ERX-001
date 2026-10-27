# 把用户 2026-10-27「按建议来」及 FD-039/040 待裁决点答复填回 R11 复核报告问题清单
import re, sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
base = "（2026-10-27 按建议）"
status = {"本Session修": "已修复", "新Session修": "待新Session修", "出方案修": "待详细修复方案", "延迟或不修": "延迟"}
extra = {
    "FD-039": "；待裁决点答：插汇率记录",
    "FD-040": "；待裁决点答：保留并登记",
    "FD-037": "；待裁决点留到 SB 开工前定",
    "FD-043": "；待裁决点留到 C 开工前定",
    "FD-038": "；登记延迟需求，修法待唤醒时定",
    "FD-042": "；接受只防按钮流程",
    "FD-045": "；暂不补",
    "FD-049": "；判定留到唤醒时",
}
n = 0
def fix(m):
    global n
    line = m.group(0)
    fd = re.match(r"\| (FD-\d{3}) ", line).group(1)
    tier = re.search(r"\| `(本Session修|新Session修|出方案修|延迟或不修)` \|", line).group(1)
    n += 1
    return line.replace("| 待裁决 | |", f"| {status[tier]} | {tier}{base}{extra.get(fd, '')} |", 1)
s = re.sub(r"^\| FD-0(3[6-9]|4\d|5[0-3]) \|.*$", fix, s, flags=re.M)
open(p, "w", encoding="utf-8", newline="").write(s)
print("rows", n)
