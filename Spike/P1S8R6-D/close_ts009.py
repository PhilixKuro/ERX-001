from pathlib import Path

stage = Path('docs/01-需求摸底/S08-数据与操控')
p = stage / 'R06-代码/P1-S8-R6-D回执-Part1.md'
lines = p.read_text(encoding='utf-8').splitlines()
for i, line in enumerate(lines):
    if line.startswith('| TS-009 译名与显示 |'):
        lines[i] = '| TS-009 译名与显示 | SL-008 | frappe_china/public/js/desk_patches.js、independent_app_labels.js、tests/test_s8_labels.py、计件字段与列表 | ✅完成 | 2026-10-21 | 全量459/459＋5/5＋4/4、Node115/115、Ruff182文件及译名门通过；CRM真实下拉/看板、采购入库真实提交、工序/BOM保存重读、有数据SPC、计件姓名/来源及对账均实测；临时夹具已清理。 |'
    elif line.startswith('| TS-009 真实采购') or line.startswith('| TS-009 0.004') or line.startswith('TS-008 重点复核'):
        lines[i] = None
    elif line.startswith('| TS-010～TS-012 |'):
        lines[i] = '| TS-010～TS-012 | TS-009已完成，继续按方案顺序推进；SL-009全量门在TS-011后执行 |'
    elif line.startswith('执行中，尚未满足'):
        lines[i] = '执行中，尚未满足“代码已落地”。TS-001～009已完成；TS-009全量459/459＋5/5＋4/4、Node115/115、Ruff182文件及译名门通过，指定浏览器验收及夹具清理已完成。继续TS-010～012；整年性能待TS-017的s8dev数据就绪。'
    elif line.startswith('- TS-009 单价精度实机'):
        lines[i] = '- TS-009单价：Operation与BOM工序保存重读均为0.004，表单显示0.0040，符合HT-010明定的precision=4、界面四位要求。此前将尾零列为阻塞是验收解读错误，现纠正，不增加格式补丁。'
    elif line.startswith('- TS-009：真实页面'):
        lines[i] = line.replace('实机只验证了该真实 show_alert 渲染路径，未提交实际 Purchase Receipt。', '已实际提交临时Purchase Receipt并见中文提示，随后取消删除及核查清理。')
    elif line.startswith('| TS-009 | SL-008 演示画面'):
        lines[i] = '| TS-009 | SL-008演示画面译名与显示 | Python/Node、译名门、三个浏览器验收脚本 | 全量459/459＋5/5＋4/4、Node115/115；CRM下拉/看板、真实提交、精度、计件姓名/来源、有数据SPC及对账通过；见实测证据节 |'
    elif line.startswith('本步进行中。TS-006'):
        lines[i] = line.split('TS-009 尚待')[0] + 'TS-009重点核SuccessAction默认句精确匹配、英文/自定义委托与CRM看板DOM范围。HT-009当前未复现历史英文，根因不能追溯，未改SPC算法。'
    elif line.startswith('- 首次全量唯一失败'):
        lines[i] = line.replace('当前尚未结束', '已完成457/457（2345.409秒）、旧类5/5、未分类4/4，退出0')
s = '\n'.join(x for x in lines if x is not None) + '\n'
evidence = '''## TS-009 实测证据与验收边界

| 验收 | 实测与证据 |
|---|---|
| ①／HT-010 | s8-ts009-display-acceptance.json：Operation数值0.004、BOM三行均0.004，保存重读控件0.0040。截图SL008-operation-rate-saved.png、SL008-bom-rate-saved.png。 |
| ② | crm_status_acceptance.cjs读取真实role=option及看板标题：线索/商机各7项中文、存值不改。证据s8-ts009-crm-acceptance.json及SL008-crm-{leads,deals}-{dropdown,kanban}.png；旧脚本期望数组不充作证据。 |
| ③／HT-008 | purchase_receipt_ui.cjs实际提交MAT-PRE-2026-00005，docstatus=1，提示已成功提交采购入库，截图SL008-submit-success-real.png。finally取消/删除单据及物料，复查items/receipts均空；原00002草稿未动。 |
| ④ | 实际对账0行、提示库存与账面金额无差异，截图SL008-reconciliation.png；有差异由Node委托契约覆盖。 |
| ⑤ | 质检context实测来料检验/出货检验/过程检验，无context电话仍呼入/呼出。 |
| ⑥／HT-009 | 28张已提交临时质检驱动SPC：六列中文，摘要子组26、读数106、剔除0、判异12，prepared_report=0。截图SL008-spc-populated.png。当前未复现R2英文，历史会话/缓存原因无证据，不能归因为缓存；未改SPC算法。 |
| ⑦ | Node契约覆盖已创建/已跳过/问题及空段“无”。 |
| ⑧⑨ | 列表employee_name、明细三类来源中文，截图SL008-piece-rate-list.png、SL008-piece-rate-sources.png。展示夹具mock collect_rows不作为工资计算证据；零数量由Python覆盖。 |
| ⑩ | test_capacity_load覆盖周三/月15日首桶，其余桶保持。 |

最终门：Python459/459（2422.628秒）、旧类5/5（0.257秒）、未分类4/4（0.005秒），退出0；Node115/115（219.087毫秒）；Ruff check/format182文件及译名自检通过。全量后未改app实现。夹具清理cleaned=40、remaining=[]，manifest已删除。JSON在frappe-bench/logs，截图/脚本在Spike/P1S8R6-D。

CRM无context撞名覆盖影响面：New→新线索（公共“新建”类文字）、Converted→已转化（其它转换状态）、Qualified→合格、Unqualified→不合格（其它资格/质量状态）、Qualification→需求确认（其它资质文字）。CRM调用无context，按方案覆盖并逐条登记translation_overrides.py。无新增工程约定，前端包装已登记README；HT-009历史原因无法追溯如实作为复核限制。

'''
s = s.replace('## TS-008 验证证据与既有用例调整', evidence + '## TS-008 验证证据与既有用例调整')
p.write_text(s.replace('\\n', '\n'), encoding='utf-8', newline='\n')
p = stage / 'P1-S8-概况.md'
lines = p.read_text(encoding='utf-8').splitlines()
for i, line in enumerate(lines):
    if line.startswith('- **R6 D 代码进行中**'):
        lines[i] = '- **R6 D 代码进行中**（Codex接续）：[Part1回执](R06-代码/P1-S8-R6-D回执-Part1.md)为续跑锚点。TS-001～009已完成；全量459/459＋5/5＋4/4、Node115/115、Ruff182文件及译名门通过。测试站CRM真实下拉/看板、采购入库真实提交、工序/BOM精度、计件姓名/来源、有数据SPC及对账均验收，临时夹具清理完毕。0.0040符合HT-010；历史SPC英文未复现，原因未证实。本轮未提交、未推送，演示站未写入。'
    elif line.startswith('- **下一步**'):
        lines[i] = '- **下一步**：TS-010策略对比→TS-011侧栏与SL-009切片门→TS-012前置数据。整年性能待TS-017的s8dev数据就绪；TS-021前仍须SA验HT-015。四项口径沿用D讨论第2/4/6/7步，无需重复确认。'
p.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
p = stage / 'R06-代码/P1-S8-R6-D讨论记录.md'
s = p.read_text(encoding='utf-8')
s = s.replace('已裁决 A，待先红后绿实现 | TS-007 收尾后按任务顺序推进', '已实现并验收，全量457/457＋5/5＋4/4 | 已完成，见D回执')
s = s.replace('待确认 | 当前已有商机看板七阶段截图与线索列表状态中文；TS-009 收尾前补验', '真实下拉与看板各7项中文 | 已完成，见crm_status_acceptance及四张截图')
s = s.replace('待确认 | 现有成功提示为原生 SuccessAction 渲染路径实测；精度为定向存取测试；SPC 已实机截图；TS-009 收尾前补其余验收', '真实提交/清理、精度、对账及有数据SPC全部完成 | 0.0040符合HT-010；历史SPC英文原因未复现')
s += '''
#### 第8步：续做验收并纠正旧阻塞记录

**背景：** 用户要求继续开发，有问题说明位置；本轮按交接结果续做。
**执行核对：** CRM真实下拉/看板、采购入库真实提交、单价保存重读、计件姓名/来源、有数据SPC已完成，夹具清理完毕。HT-010明定四位显示，0.0040是预期，之前尾零阻塞解读已纠正。HT-009当前未复现历史英文，不能声称根因是缓存。
**结论：** 沿用四项用户裁决，TS-009完成，继续TS-010/011；同一轮续做，不新增产品裁决。
'''
p.write_text(s, encoding='utf-8', newline='\n')
print('TS-009 receipt, overview and discussion corrected')
