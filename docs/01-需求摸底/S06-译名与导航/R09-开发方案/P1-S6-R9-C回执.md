# P1-S6-R9 回执（C 步·开发方案，R8 E 报告回流）

**轮次**：P1-S6-R9｜**日期**：2026-10-12｜**执行者**：Claude（Opus 5.5）
**Spec**：[C-implPlan-plannedDev-build.md](../../../流程体系/workflows/plannedDev/C-implPlan-plannedDev-build.md)｜`打tag=否`
**产物**：[R9 开发方案](P1-S6-R9-C开发方案.md)（单文件；SL-016～023、TS-025～037、HT-021～027、A23～A28）；中途 [C 讨论记录](P1-S6-R9-C讨论记录.md)（1 步；DEC-039～041、NV-036～038、LG-011）
**依据**：[R8 E 确认报告](../R08-确认/P1-S6-R8-E确认报告.md)「问题详情」「用户裁决」「交出去向」三节；R3 方案（总纲＋Part1～4）与 R6 方案；[R2 B 需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) v1.0

## 状态值

| 状态值 | 判定依据 |
|---|---|
| **`方案已产出`** | 产物规格各节齐备；R8 交给 C 的两处用词已由用户定（DEC-039、040）；九条自评审逐条过（见下）。按 `plannedDev` 出口路由 → **D 步（R10）**，执行完回 E 复核（R11） |

## 本步做了什么事实补查

| 查什么 | 怎么查 | 结论 |
|---|---|---|
| 15 屏英文的接入点 | 逐处读上游：`filter_list.js:130-145`、`list_view.js:752-814`、`page.js:622-662`、`query_report.js:1379-1452`、`version_timeline_content_builder.js:411-418`、`dialog.js:10-33`、`crm_fields_layout.py:113-146,179-191`、`SidePanelLayout.vue:148-160`、frappe-ui `ListFooter.vue:12-21`、`crm/www/crm.html:2` | 每处都有可包的原型方法、可覆盖的 whitelisted 方法或可限定的 DOM 区域，写入 TS-027～034。唯一包不到的是 `format_content_for_timeline`（模块内函数），所以按 E 代裁走 Observer |
| bundle 加载次序 | `frappe/hooks.py:25-34`、`www/desk.html:65` | frappe 各 bundle 先于 app 的 `app_include_js` 输出（HT-021，读码） |
| ECharts 取 locale | `echarts/lib/core/locale.js:55-58`；grep CRM 构建产物 css 中的 `:lang(`／`[lang` | 按 `document.documentElement.lang` 取；css 里 0 处 lang 选择器（HT-022） |
| 称呼数据 | `Spike/P1S6R9-C/salut.py` 经 `bench execute` 只读，两站各跑一次 | 演示站 `tabSalutation` 0 条，测试站 9 条（记录名为英文）；两站业务数据都没引用称呼（讨论记录第 1 步 ②） |
| 新词占用 | `python -I Spike/P1S6R4-occupancy.py X <候选>` | 太太、小姐、夫人、少爷、小先生都未被占用；「女士」被 4 词占用 |
| Raven `Available` | `raven/apps/web/src/...Profile.tsx:28`、`hooks/useSetAvailability.ts:9`、`lib/translate.ts`、`UserAvatar.tsx:156-157` | 模块级常量、无 context，取 `frappe._messages`；Raven 区分「手动可联系」与「实际在线」 |
| 现有合并字典 | 读 R8 留下的 `Spike/P1S6R8-E/sl013/merged_zh.json` | `From Date` 起始日期、`To Date` 截止日期、`Add {0}`／`Select {0}` 官方有译；`{0} Filter Applied` 一类官方无键，须自加 |

## 自评审执行结果

| # | 检查 | 结果 |
|---|---|---|
| 1 | 切片与任务双向对账 | SL-016 ← TS-027／028；SL-017 ← TS-029；SL-018 ← TS-030；SL-019 ← TS-033／034；SL-020 ← TS-031／032；SL-021 ← TS-025／026；SL-022 ← TS-036；SL-023 ← TS-037；TS-035 横跨 SL-016～021（截图类验收项都落在它）。无孤立项 |
| 2 | 验收条件可判定 | 全部落成 Node／Python 断言、截图读数或站点查询。首稿 SL-016 ① 写「title 显示中文」，改为写出期望文字与 csv 键 |
| 3 | 异常路径已覆盖 | 每个前端补丁有「英文会话不变／上游缺失只告警／重复加载不叠加」三条（A23）；SL-016 ② 找不到错误 title 原样返回；SL-017 ③ 白名单外不变、空值原样；SL-018 ② 时间线外不改；SL-019 ① 上游模板变了测试当场失败，④ 自定义占位保留、无布局返回 `[]`；SL-020 ③ context 行缺失时告警；SL-021 ② 取法有反例；SL-022 ② 补丁没覆盖到的屏暂停 |
| 4 | 切片粒度可运行 | SL-021 是测试取法加 csv，做完即可在站上看到称呼等改词；其余切片各对应一组屏，做完能在测试站看到。SL-022、SL-023 同 R6 的收尾切片 |
| 5 | 接口与需求对齐 | R8 `出方案修` 各项逐项落到切片（§六表）；需求 AC 不新增，本方案只补 R6 SL-014 ③ 未过的屏 |
| 6 | 任务顺序可执行 | TS-025 先于一切新增自有键；TS-026 的 csv 依赖 TS-025 的取法；`desk_patches.js` 系列 TS-027～031 串行；`independent_app_labels.js` 系列 TS-032→033→034 串行；TS-035 在所有代码之后；TS-036 依赖 TS-035 通过 |
| 7 | 假设显式 | 7 条进 §三。首稿有两处裸假设：Raven 注入脚本先于 module 求值（补 HT-025）、带分组裸串改 label 不破坏上游按 label 查按钮（补 HT-027） |
| 8 | 详细度合规 | 每处补丁给接入点（文件:行）、包装伪代码与匹配条件；csv 行给表；没有给完整实现 |
| 9 | 可执行性自读 | 查出三处并已改：① 首稿把筛选按钮单复数写反（上游 `n > 1` 才用复数）；② 清场脚本只 exec FunctionDef，拆出的新函数要一并取出、import 要留在函数体内；③ 演示站无称呼记录，称呼下拉屏改为只在测试站截 |

## 复核建议

**1. 验收条件最不确定是否覆盖到位的切片**

- **SL-022（演示站全部屏 `pass=true`）**：本方案按 E 报告的定位修了 15 屏，但每处修法的实际生效只在 TS-035 的测试站实页上验。若有某屏的英文来自 E 没点到的第二处生成点，D 会在 TS-036 第 6 步暂停，又得回 C。查法：对照 R7 `Spike/P1S6R6-screens/result.json` 那 15 屏的 `english`、`title_issues` 两列，逐词看本方案 §六 有没有对应任务。
- **SL-019 ③（翻页「of」）**：判定写成「前后都是数字的 of」，靠的是 frappe-ui `ListFooter.vue` 的 DOM 形态（三个兄弟 div）。CRM 若有别的列表组件不用 `ListFooter`，那里的「of」不会被改。查法：`grep -rn "ListFooter\|>of<" crm/frontend/src`。

**2. 切片划分**：按「改哪一屏」切（列表、报表、时间线、CRM、对话框与 Raven、csv）。第二种合理切法是按「改哪个文件」切（`desk_patches.js` 一片、`independent_app_labels.js` 一片），任务顺序其实就是按文件串的。没这样切，是因为 E 复核要按屏判过不过，按屏切时验收条件能直接对上 R7 未过的 15 屏。

**3. 技术假设是否有遗漏**：判为「成熟做法、故未列」的有：jQuery 字符串替换 `get_header_html()` 返回值不破坏表头事件（事件在外层委托绑定，`list_view.js` 在 prepend 后才 bind）；`frappe.format` 拿到中文显示值后不会再查 Link 路由（`voucher_type` 列不是 Link）；`override_whitelisted_methods` 对 Vue 前端 `createResource` 的调用同样生效（与 Desk 同一个 `/api/method` 入口）。`docs/开发守则.md` 无 §12「高风险技术点清单」（同 R3、R6），未能对照。

**4. 拿不准处**：

| 位置 | 推断内容 | 依据 |
|---|---|---|
| TS-029 | `against_voucher_type`、`party_type` 两列一并翻译 | E 只点名 `voucher_type`；这两列同样装 DocType 名，也在演示线的总账屏上。若嫌超范围，可从白名单删掉 |
| TS-034 | 侧栏的 label 用无 context 的 `_(label)` | CRM 前端 `__(field.label)` 也不带 context，两边取同一个词；若某 label 演示线定词带 context，侧栏会和表单显示不一 |
| TS-026 | `Inter Company Invoice` 取 R7 按钮抽检定稿「公司间销售发票」 | 该按钮在采购发票上，建的是对方公司的销售发票（R7 附表第 106 行读码）；R8 没对这个词另提意见 |
| A25 | 上游缺陷报告只写草稿，不外发 | 向 GitHub 提 issue 属外发，须用户另行许可 |

## 改动清单

| # | 文件 | 改动 | 来源 |
|---|---|---|---|
| 1 | R9 开发方案（新增） | 本步主产物 | — |
| 2 | R9 C 讨论记录（新增） | 1 步，DEC-039～041 | `play-build` 纪律 3 |
| 3 | P1-S6-概况 | 当前进度加 R9，下一步改为 D（R10） | 流程中枢第 8 步 |
| 4 | P1-概况 | 级联指针 | 同上 |
| 5 | `Spike/P1S6R9-C/salut.py`、`probe1.txt`（新增） | 事实补查脚本与输出 | 本回执「事实补查」 |

**常驻文件**：本步未写。

## 未做项

| 项 | 原因 |
|---|---|
| 记录验证（子 Agent 比对） | 讨论记录只有 1 步，原始对话全程在本 Session，由 Claude 自核 |
| tag | `打tag=否` |
| git 提交 | 未获许可，改动只在工作区 |
