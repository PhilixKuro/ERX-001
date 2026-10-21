from pathlib import Path

root = Path('/workspace/docs/01-需求摸底/S08-数据与操控')
p = root / 'R06-代码/P1-S8-R6-D回执-Part1.md'
s = p.read_text(encoding='utf-8')
s = s.replace('切片全量正在运行：已发现旧评论断言仍为「手动指定」，须按 SL-006④ 改为「人工指定」并定向复验；暂不标完成', '首次切片全量 449 条中仅旧评论断言失败（2407.397 秒），旧类 5/5、未分类 4/4；按 SL-006④ 将「手动指定」改为「人工指定」后，本模块 8/8（2.503 秒）、debug 1/1（0.052 秒）、译名自检通过。整套重跑中，日志 s8-ts007-full-final.log；暂不标完成')
s = s.replace('切片全量发现旧评论措辞断言尚未更新，待结束后修正并定向复验', '首次全量仅旧评论措辞断言失败，已按 SL-006②④ 修改且模块 8/8；整套重跑中')
s = s.replace('449 条集成的切片全量运行中，发现旧评论断言待按方案修正。', '首次全量集成 448/449、旧类 5/5、未分类 4/4；唯一失败为旧措辞断言，修正后模块 8/8，debug 1/1、译名自检通过；整套重跑中。')
s = s.replace('TS-007 的前后端确认边界与真实生产计划→工单字段传递待后续实测。', 'TS-007 可核 production_plan.js／work_order.js 的 kept 重询及 confirmed／manual 不重询边界；来源及真实建单路径各 6/6，浏览器同一计划 kept→confirmed→不重询已有证据，整套重跑尚未结束。')
anchor = '## TS-006 既有用例期望变动'
insert = '''## TS-007 既有用例期望变动

| 用例 | 旧期望 | 新期望 | 依据与复验 |
|---|---|---|---|
| `test_bom_selection.TestBomSelection.test_work_order_preserves_manual_bom_and_comments` | 评论含「手动指定」 | 评论含「人工指定」 | SL-006②明定人工指定，④要求同步 S7 旧断言；仍保留 BOM-MANUAL、不自动替换且列出 BOM-CHEAP 两项断言。首次全量唯一失败后修正，模块 8/8（2.503 秒） |

TS-007 首次全量：集成 449 条，2407.397 秒，failures=1；旧类 5/5（0.285 秒），未分类 4/4（0.005 秒），进程退出 1。不得记为全量通过。修正仅一条旧措辞断言后整套重跑，输出 `frappe-bench/logs/s8-ts007-full-final.log`；运行期间 app 冻结，TS-008 仅在 Spike 准备。

'''
if '## TS-007 既有用例期望变动' not in s:
    s = s.replace(anchor, insert + anchor)
if 'TS-007 无新增工程约定' not in s:
    s = s.replace('## 未做项', 'TS-007 无新增工程约定：确认弹窗与来源标记为 doctype_js／doc_events 追加，不替换原生类或方法；沿用现有 Select 存值与翻译纪律。\n\n## 未做项')
p.write_text(s, encoding='utf-8')
p = root / 'P1-S8-概况.md'
s = p.read_text(encoding='utf-8').replace('449 条集成的切片全量运行中，已发现旧评论断言仍为「手动指定」，待按 SL-006④ 更新为「人工指定」并复验。', '首次切片全量 449 条中仅旧评论措辞断言失败（2407.397 秒），旧类 5/5、未分类 4/4；已按 SL-006④ 改为「人工指定」，模块复验 8/8，debug 1/1、译名自检通过。整套重跑中（s8-ts007-full-final.log），TS-008 仅在 Spike 准备。')
s = s.replace('两项口径已裁决：', '三项口径已裁决：').replace('（第 4 步）。写 TS-021', '（第 4 步）；TS-008 从 Company.default_wip_warehouse 合并该公司已提交工单仓（第 6 步）。写 TS-021')
p.write_text(s, encoding='utf-8')
p = root / 'R06-代码/P1-S8-R6-D讨论记录.md'
s = p.read_text(encoding='utf-8').replace('| 已裁决 A，待实现与回归 | TS-006 全量门通过后，按 kept 重询判据先红后绿 |', '| 已实现，定向／浏览器通过；首次全量仅旧措辞断言失败，修后整套重跑中 | 见 D 回执 TS-007；整套通过后标完成 |')
p.write_text(s, encoding='utf-8')
for path in (root / 'R06-代码/P1-S8-R6-D回执-Part1.md', root / 'P1-S8-概况.md', root / 'R06-代码/P1-S8-R6-D讨论记录.md'):
    s = path.read_text(encoding='utf-8')
    if path.name == 'P1-S8-R6-D回执-Part1.md':
        s = s.replace('首次切片全量 449 条中仅旧评论断言失败（2407.397 秒），旧类 5/5、未分类 4/4；按 SL-006④ 将「手动指定」改为「人工指定」后，本模块 8/8（2.503 秒）、debug 1/1（0.052 秒）、译名自检通过。整套重跑中，日志 s8-ts007-full-final.log；暂不标完成', '修正旧评论断言后，全量 449/449（2392.615 秒）、旧类 5/5（0.258 秒）、未分类 4/4（0.006 秒）均通过；Node 109/109，debug 1/1、译名自检通过。首次全量失败为旧措辞与 SL-006②④ 不符，详见下表。TS-007 完成')
        s = s.replace('首次全量仅旧评论措辞断言失败，已按 SL-006②④ 修改且模块 8/8；整套重跑中', '首次全量唯一失败为旧评论措辞断言，按 SL-006②④ 更新后模块 8/8；重跑全量 449/449、5/5、4/4 全过')
        s = s.replace('TS-007 首次全量：集成 449 条，2407.397 秒，failures=1；旧类 5/5（0.285 秒），未分类 4/4（0.005 秒），进程退出 1。不得记为全量通过。修正仅一条旧措辞断言后整套重跑，输出 `frappe-bench/logs/s8-ts007-full-final.log`；运行期间 app 冻结，TS-008 仅在 Spike 准备。', 'TS-007 首次全量：449 条，2407.397 秒，唯一失败为旧措辞断言；旧类 5/5（0.285 秒）、未分类 4/4（0.005 秒），退出 1。改为验收明确的「人工指定」后，模块 8/8 且切片全量重跑 `frappe-bench/logs/s8-ts007-full-final.log` 通过：449/449、5/5、4/4。随后 Node 109/109、debug 1/1、`translation_check.run` 通过。')
        s = s.replace('| TS-007 | SL-006 ①浏览器保留后换用；②五类来源；③来源有值不改；④旧断言按新口径更新 | `test_bom_confirmation`、`test_bom_selection_hooks`、Node 专项及全量；`bom_confirmation_ui.cjs`；切片全量 | 来源 6/6、路径 6/6、专项 17/17、Node 109/109；浏览器 kept→confirmed→不重询通过。首次全量仅旧评论措辞断言失败，已按 SL-006②④ 修改且模块 8/8；整套重跑中 |', '| TS-007 | SL-006 ①浏览器保留后换用；②五类来源；③来源有值不改；④旧断言按新口径更新 | `test_bom_confirmation`、`test_bom_selection_hooks`、Node 专项及全量；`bom_confirmation_ui.cjs`；切片全量 | 来源 6/6、路径 6/6、专项 17/17、Node 109/109；浏览器 kept→confirmed→不重询通过。首次全量唯一失败为旧评论措辞，修正后模块 8/8；全量 449/449、旧类 5/5、未分类 4/4 通过 |')
        s = s.replace('| TS-007 全量门、TS-008～TS-012 | TS-007 已实现并完成定向／浏览器验收，全量运行中；后续任务尚未开始 |', '| TS-008～TS-012 | TS-007 全量、Node、debug、自检均已通过并收尾；TS-008 正在先红测试准备 |')
        s = s.replace('执行中，尚未满足“代码已落地”。TS-001～006 已完成，TS-006 切片全量 441＋5＋4 全过。TS-007 实现、来源 6/6、建单路径 6/6、前端专项 17/17、Node 109/109、浏览器重存三步及夹具清理已完成；首次全量集成 448/449、旧类 5/5、未分类 4/4；唯一失败为旧措辞断言，修正后模块 8/8，debug 1/1、译名自检通过；整套重跑中。测试站迁移已自然结束，不重复迁移，不操作演示站。', '执行中，尚未满足“代码已落地”。TS-001～006 全量门已通过；TS-007 来源／建单各 6/6、前端 17/17、浏览器 kept→confirmed→不重询、Node 109/109、debug 1/1、自检通过。首次全量唯一失败的旧措辞断言已修正，模块 8/8；全量 449/449、旧类 5/5、未分类 4/4 通过。测试站迁移已自然结束，不重复迁移，不操作演示站。TS-008 开始先红测试。')
        s = s.replace('## 偏离与暂停', 'TS-007 无新增工程约定：确认弹窗与来源标记为 doctype_js／doc_events 追加，不替换原生类或方法；沿用现有 Select 存值与翻译纪律。\n\n## 偏离与暂停') if 'TS-007 无新增工程约定' not in s else s
        s = s.replace('TS-007 可核 production_plan.js／work_order.js 的 kept 重询及 confirmed／manual 不重询边界；来源及真实建单路径各 6/6，浏览器同一计划 kept→confirmed→不重询已有证据，整套重跑尚未结束。', 'TS-007 前后端确认边界可核 production_plan.js／work_order.js；来源与真实建单路径各 6/6，浏览器同一计划 kept→confirmed→第三次保存无弹框；全量 449/449、旧类 5/5、未分类 4/4 已过。TS-008 尚无实现，测试正准备先红。')
    elif path.name == 'P1-S8-概况.md':
        s = s.replace('首次切片全量 449 条中仅旧评论措辞断言失败（2407.397 秒），旧类 5/5、未分类 4/4；已按 SL-006④ 改为「人工指定」，模块复验 8/8，debug 1/1、译名自检通过。整套重跑中（s8-ts007-full-final.log），TS-008 仅在 Spike 准备。', '首次切片全量唯一失败为旧评论措辞断言（2407.397 秒）；按 SL-006④ 改为「人工指定」后模块 8/8、全量 449/449（2392.615 秒）、旧类 5/5、未分类 4/4 通过。Node 109/109、debug 1/1、自检通过。TS-007 收尾完成，TS-008 先红测试开始。')
        s = s.replace('完成 TS-007 切片全量、旧评论断言修正、debug 冒烟和译名自检后，按顺序推进 TS-008', '按用户批准的 v16 Company 在制品仓口径推进 TS-008')
    else:
        s = s.replace('已实现，定向／浏览器通过；首次全量仅旧措辞断言失败，修后整套重跑中', '已实现，定向、浏览器与切片全量 449/449、旧类 5/5、未分类 4/4 通过；首次旧措辞断言已按 SL-006②④ 修正')
        s = s.replace('见 D 回执 TS-007；整套通过后标完成', 'D 回执 TS-007；已完成')
    path.write_text(s, encoding='utf-8')
print('TS-007 slice gates passed and receipt updated')
