from pathlib import Path

stage = Path('docs/01-需求摸底/S08-数据与操控')
path = stage / 'R06-代码/P1-S8-R6-D回执-Part1.md'
s = path.read_text(encoding='utf-8')
s = s.replace('| TS-010 策略对比报表 | SL-009 | — | ⬜未开始 | — | |',
    '| TS-010 策略对比报表 | SL-009 | stock_plus/report/replenishment_strategy_comparison、tests/test_strategy_comparison.py | 🟡验收中 | 2026-10-21 | 先红6/6模块缺失，再绿6/6（14.334秒）；真实中文报表/三段柱图已验。库存均值880/1050/900、采购2/1/0、总成本44.8219178082/25.7534246575/4.9315068493。整年性能待TS-017。切片全量待TS-011收尾。 |')
s = s.replace('| TS-011 侧栏入口 | SL-009 | — | ⬜未开始 | — | |',
    '| TS-011 侧栏入口 | SL-009 | workspace_sidebar/business_flow.json、tests/test_business_flow_navigation.py、README | 🟡验收中 | 2026-10-21 | 用户批准15项完整清单（D讨论第9步）；7节66入口，静态6/6（0.445秒），报价页sidebar_title=Business Flow已实测；逐项点击与译名门收尾中。 |')
s += '''
## TS-010／011 续做证据

- TS-010先跑红6条均为缺模块，1.451秒；实现后测试站6/6，14.334秒。真实单据：4笔库存收发、3张提交采购订单（每单两行验证distinct），另外草稿及无关物料订单排除；缺料三工单只计1。日期段1/4、倒置、首尾同日重叠、缺日期报错，默认三规则并集、缺参数总成本为空且提示。取消SLE不计，10天与365天查询数相同且不超过2。
- 浏览器SL009-strategy-comparison.png：八列中文、三段数据及实际SVG柱图，prepared_report=0；报价页SL009-quotation-business-flow.png，sidebar_title实测Business Flow，HT-011成立，无需fallback。
- TS-011先红：侧栏缺15项、报表未注册两个失败；json及测试站迁移后静态6/6。方案14为计数笔误，用户第9步批准按15项补齐，总入口66；其余7节及已有51项保持。
- 首次译名门20条中2失败：SPC Chart缺译及一个公司不存在公共词条未登记。新增SPC Chart独立源词；公司不存在直接沿用官方译文，删除重复CSV覆盖，不为过门制造覆盖依据。后续复验为准。
'''
path.write_text(s.rstrip()+'\n', encoding='utf-8', newline='\n')
path = stage / 'P1-S8-概况.md'
s = path.read_text(encoding='utf-8').replace('TS-010策略对比→TS-011侧栏与SL-009切片门→TS-012前置数据',
    'TS-010/011已实现，手算6/6与侧栏静态6/6、中文报表/报价侧栏实测通过；完成逐入口点击、译名与SL-009全量门后推进TS-012前置数据')
path.write_text(s,encoding='utf-8',newline='\n')
print('TS-010/011 progress recorded')
