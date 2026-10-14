"""把用户 2026-10-13 的裁决填进 R12 F 审核报告问题清单的「状态」「用户裁决」两列。"""
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

AS_SUGGESTED = "按建议"
RULINGS = {
	"FD-001": ("待新Session修", "按建议：新Session修（SB）；定级维持中"),
	"FD-002": ("待新Session修", "选 ①：`override_doctype_dashboards` 改工位看板分组标题（L3），`Master` 继续给称呼用；SB 做，补一屏「工位表单·关联页签」"),
	"FD-003": ("待裁决", "按建议：本Session修，第 4 项固定按 zh 判"),
	"FD-004": ("不做", "保留官方「默认成品仓(收料仓)」，括注不改"),
	"FD-005": ("延迟", "按建议：认定与 `Qualification` 同属 DEC-033 默认数据，补进 `SH-P1S6002`"),
	"FD-006": ("待裁决", "同意：还原科目表字节、加 sha256 断言，提交推送 `frappe_china` 并推进锁"),
	"FD-007": ("待裁决", "同意：cdp.cjs 纳入版本（exclude 加例外）；被引证据逐份定纳入与否，不纳入的注明仅本机"),
	"FD-021": ("待裁决", "改：`Stock Balance` 不改；`Stock Ledger Invariant Check` 定新词"),
	"FD-026": ("待裁决", "本Session修，等其余当场修改完、本次提交前改"),
}
SUGGESTED_STATUS = {
	"本Session修": "待裁决",
	"新Session修": "待新Session修",
}
DELAYED = {"FD-005", "FD-011", "FD-022", "FD-023", "FD-029"}

count = 0
out = []
for line in text.splitlines(keepends=True):
	match = re.match(r"\| (?:\*\*)?(FD-\d{3})(?:\*\*)? \|", line)
	if not match or not line.rstrip("\r\n").endswith("| 待裁决 | |"):
		out.append(line)
		continue
	fd = match.group(1)
	if fd in RULINGS:
		status, ruling = RULINGS[fd]
	else:
		cells = line.split("|")
		grade = next((cell.strip() for cell in cells if cell.strip().strip("`") in ("本Session修", "新Session修", "出方案修", "延迟或不修")
			or cell.strip().startswith(("`本Session修", "`新Session修", "`延迟或不修"))), "")
		grade = grade.strip("`").split("`")[0]
		if grade.startswith("延迟或不修"):
			status = "延迟" if fd in DELAYED else "不做"
		else:
			status = SUGGESTED_STATUS.get(grade, "待裁决")
		ruling = f"{AS_SUGGESTED}：{grade}"
	eol = line[len(line.rstrip("\r\n")):]
	out.append(line.rstrip("\r\n")[: -len("| 待裁决 | |")] + f"| {status} | {ruling} |" + eol)
	count += 1

path.write_text("".join(out), encoding="utf-8")
print("filled", count)
