"""Repair the fixed TS-007 sample and matching batch entries.

The first batch pass used a fallback translator and left obvious mixed-English
and placeholder strings.  Keep these corrections explicit so the repair is
repeatable and reviewable; the source strings remain the keys in zh.csv.
"""
from __future__ import annotations

import csv
import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv"
OVERRIDES_PATH = ROOT / "frappe-bench/apps/frappe_china/frappe_china/tests/translation_overrides.py"


REPAIRS = {
    # CRM
    "{0}% complete": "{0}% 完成",
    "Enable Exotel integration to make and receive calls directly from your CRM": "启用 Exotel 集成，以便直接从您的 CRM 拨打和接听电话",
    "Replacing my current CRM": "替换我当前的 CRM",
    "Create form": "创建表单",
    "Cannot rename: an unrelated {0} '{1}' already exists on the other side. Resolve manually first.": "无法重命名：另一侧已存在无关的 {0}“{1}”。请先手动解决。",
    "{0} isn't a linkable field on a CRM form.": "{0} 不是 CRM 表单中的可链接字段。",
    "Setting up Yahoo requires you to enable two factor authentication and app specific passwords. Read more": "设置 Yahoo 需要启用双重身份验证和应用专用密码。阅读更多",
    "Expected deal value is required.": "必须填写预计商机金额。",
    "Choose how you want to use the application by setting your preferences.": "请通过设置偏好选择您使用此应用的方式。",
    "{0} users added to hierarchy": "已将 {0} 名用户添加到层级结构",
    # ERPNext
    "Frappe CRM": "Frappe CRM",
    "Rate at which document currency is converted to company currency": "单据币种转换为公司币种的汇率",
    "Line references undefined in {0}: {1}": "行引用在 {0} 中未定义：{1}",
    # Frappe
    "added {0} row(s) to {1}": "已将 {0} 行添加到 {1}",
    "Outlook.com": "Outlook.com",
    "Sendgrid": "Sendgrid",
    "Sync Timeout (Seconds)": "同步超时（秒）",
    "Verdana": "Verdana",
    "No pinned document types.": "没有固定的单据类型。",
    # HRMS
    "Shortlist": "候选名单",
    "Leave Settings": "请假设置",
    "21:00": "21:00",
    "No Bank/Cash Account found for currency {0}. Please create one under company {1}.": "未找到币种 {0} 对应的银行/现金科目。请在公司 {1} 下创建科目。",
    "Advance Account is mandatory. Please set the {0} in the Company {1} and submit this document.": "预付款科目为必填项。请在公司 {1} 中设置 {0}，然后提交此单据。",
    # Insights
    "Bulk Enqueue Import Job": "批量加入导入作业队列",
    "Insights Workbook": "Insights 工作簿",
    "Refreshing Tables": "正在刷新表",
    "Action if table exists": "表已存在时的操作",
    "Is Native Query": "是否为原生查询",
    "New Alert": "新建提醒",
    # Raven
    "{0} joined.": "{0} 已加入。",
    "You'll need an invite to rejoin this channel": "您需要邀请才能重新加入此频道",
    "Delete Scheduled Message?": "删除定时消息？",
    "Add a new variable in the function.": "在函数中添加新变量。",
    "Joining…": "正在加入…",
    "Status set to {0}": "状态已设置为 {0}",
    "React with {0}": "用 {0} 表情回应",
    "Rows per page": "每页行数",
    "Log out of your account?": "要退出您的账户吗？",
    "Can be HTML/Markdown/Plain Text. Support Jinja tags": "可以是 HTML/Markdown/纯文本。支持 Jinja 标签",
    "Forwarded": "已转发",
    "Turning this on will remove any public channels where you have not joined from the sidebar.": "启用此项会从侧栏移除您尚未加入的所有公共频道。",
    "This channel is no longer available": "此频道已不可用",
    "{0} votes": "{0} 票",
    "Create and manage document processors for your bots.": "为您的机器人创建和管理文档处理器。",
    "If you later intend to make this private you will have to manually remove members that should not have access to this channel.": "如果您之后想将其设为私有，必须手动移除不应访问此频道的成员。",
    "Read receipts": "已读回执",
    "Working Hours Start": "工作时间开始",
    "1 member selected": "已选择 1 位成员",
    "Meeting links from these sites show a join card in chat.": "来自这些站点的会议链接会在聊天中显示加入卡片。",
    "You may want to try adjusting your filters.": "您可以尝试调整筛选条件。",
    "Raven Push Token": "Raven 推送令牌",
    "There is no one else in this workspace to add.": "此工作区没有其他可添加的成员。",
    "Go back to the previous channel or page.": "返回上一频道或页面。",
    "What Enter does can be changed in Preferences.": "可以在偏好设置中更改回车键的功能。",
    "Sent a photo": "已发送照片",
    "Cannot send an empty message": "无法发送空消息",
    "Click to pause": "点击暂停",
    "Shown on the message action dialog.": "显示在消息操作对话框中。",
}


def main() -> None:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    seen: set[str] = set()
    for row in rows:
        if len(row) >= 2 and row[0] in REPAIRS:
            row[1] = REPAIRS[row[0]]
            seen.add(row[0])

    # The pre-existing catalogue had two exact-key rows for these generic
    # strings.  Frappe's last-row-wins loader made the result order-dependent;
    # keep the first row and remove the duplicate while repairing the batch.
    deduped: list[list[str]] = []
    keys: set[str] = set()
    for row in rows:
        if len(row) not in (2, 3):
            deduped.append(row)
            continue
        key = row[0] + (":" + row[2] if len(row) == 3 and row[2] else "")
        if key in keys:
            continue
        keys.add(key)
        deduped.append(row)
    rows = deduped

    missing = sorted(set(REPAIRS) - seen)
    if missing:
        raise SystemExit(f"repair keys not found in zh.csv: {missing}")

    # Do not write a BOM: Frappe's CSV loader treats it as part of the first key.
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)

    update_overrides()
    print(f"repaired {len(seen)} source keys")


def update_overrides() -> None:
    """Keep the S6 override expectations aligned with repaired CSV values."""
    pattern = re.compile(r'^(\s*)("(?:\\.|[^"])*"):\s*Override\((.*)\),?\s*$')
    lines = OVERRIDES_PATH.read_text(encoding="utf-8").splitlines(keepends=True)
    changed: set[str] = set()
    output: list[str] = []
    for line in lines:
        match = pattern.match(line.rstrip("\r\n"))
        if not match:
            output.append(line)
            continue
        key = ast.literal_eval(match.group(2))
        if key not in REPAIRS:
            output.append(line)
            continue
        call = ast.parse(f"Override({match.group(3)})", mode="eval").body
        official, _old_ours, basis = (ast.literal_eval(arg) for arg in call.args)
        newline = "\n" if line.endswith("\n") else ""
        output.append(
            f"{match.group(1)}{match.group(2)}: Override({official!r}, {REPAIRS[key]!r}, {basis!r}),{newline}"
        )
        changed.add(key)
    # Most batch rows have no official override entry.  Only update the
    # existing entries; adding every batch key to OVERRIDES would turn the
    # override table into a second translation catalogue.
    OVERRIDES_PATH.write_text("".join(output), encoding="utf-8")


if __name__ == "__main__":
    main()
