# 把 R11 F 复核裁为延迟的 12 项登记进 S8 延迟需求登记册（插在 SH-P1S8022 行之后）
import sys
p = sys.argv[1]
src = "[R11 F 复核报告](R11-F复核/P1-S8-R11-F复核报告.md)"
first = f"{src} {{fd}}（登记 2026-10-27，用户裁决「按建议来」）"
rows = [
    ("SH-P1S8023", "整数计数单位下，工单各道报工损耗都为 0、BOM 整体损耗率非 0、完工数不是 BOM 数量整倍数时，原生完工入库按 `fg×整体损耗率÷100` 回退得小数损耗（2103 支→103.047）被整数校验拦下；报错是原生「不能为小数」、不提示怎么办。绕过法：手填整数损耗。修法二选一：零报工损耗时置 0 并跳过 BOM 回退，或回退值取整并提示（会改原生损耗语义，须出方案）。演示数据不触发（完工入库损耗最小 44）", "客户正式库上线前，或客户出现整单无损耗报工时", "FD-038"),
    ("SH-P1S8024", "FD-011 开播守卫的两条控制台旁路：工作库判定信任前端传的 `mode`；`drop_snapshots` 清空登记表 `base_db` 后守卫失效。按钮流程不触发", "演示操作者不止一人，或改 `demo/progress.py` 时", "FD-042"),
    ("SH-P1S8025", "`stock_entry_accounts.py` `fallback_operating_cost_share` docstring 写「accounting review recorded in SH-P1S8010」，读来像会计已复核，应改为待复核", "下次改该文件时", "FD-044"),
    ("SH-P1S8026", "`docs/项目概况.md` 对 ERPNext fork 改动（`a729571`）只论证了不用类覆盖，没答为何不用运行时替换类方法（同 `overproduction.py`）；可行则考虑撤掉 fork 改动", "上游同步 ERPNext 时，或 P1 收口前", "FD-045"),
    ("SH-P1S8027", "`prepare_work(quality_preview=1)` 参数在站点标记上线后冗余，可在演示站跳过开播前计划检查，应删去只认 `is_quality_preview_site()`", "下次改 `demo/workspace.py` 时", "FD-046"),
    ("SH-P1S8028", "开播前只核 SPC 计划指纹，不核计划能否对上实际单据号；「只跑生成器」产出的计划要到第 2 段首日才失败。可让导出计划附来源标记并一并比对", "下次重做 SPC 计划流程，或演示者不止一人时", "FD-047"),
    ("SH-P1S8029", "`snapshot_status` 仍收 GET、调用即可能改写登记表，应改 `methods=[\"POST\"]` 并补断言", "下次改 `demo/snapshot.py` 时", "FD-048"),
    ("SH-P1S8030", "`frappe_debug/README.md` 前端覆盖登记缺行号与锁定 commit；`crm_inject.py` 替换 `/crm` 模板入口未登记，也未说明为何判为追加", "下次写 `frappe_debug` 回执或改前端覆盖时", "FD-049"),
    ("SH-P1S8031", "班组按全部场景工位分，`卷簧机-2` 全年无工序卡、其班组 3 人 0 条报工，实际 9 人参与；`verify` `staff.reporting_employees` 门槛只要求 4 人", "下次改生成器排程或员工参数时", "FD-050"),
    ("SH-P1S8032", "第 9 幕保留期（E−21 起扣 EOQ 与定期复核）让第 8 幕策略对比第 3 段末尾一次定期复核被忽略，该段成本数字偏低；可把第 3 段终点改为 `act9_hold_start − 1`", "下次改第 8、9 幕前置时，或客户追问第 8 幕数字时", "FD-051"),
    ("SH-P1S8033", "`SH-P1S8021` 的 SPC 拖尾豁免实际适用全部 8 条判异规则（按回看长度，最长 15 组），不只规则 5、6；随 `SH-P1S8021` 一并重新决策", "随 `SH-P1S8021`", "FD-052"),
    ("SH-P1S8034", "`frappe-bench/apps/frappe_debug` 工作区行尾 CRLF、提交为 LF（`core.autocrlf=true`），`git status` 常显示 21 处假修改；`git add -A` 可能混进整文件行尾改动。可加 `.gitattributes` 固定 LF", "下次在 `frappe_debug` 提交前", "FD-053"),
]
lines = open(p, encoding="utf-8").read().split("\n")
i = next(k for k, l in enumerate(lines) if l.startswith("| SH-P1S8022 |"))
new = [f"| {sid} | {text} | {wake} | {first.format(fd=fd)} | 延期 |" for sid, text, wake, fd in rows]
lines[i + 1:i + 1] = new
open(p, "w", encoding="utf-8", newline="").write("\n".join(lines))
print("inserted", len(new))
