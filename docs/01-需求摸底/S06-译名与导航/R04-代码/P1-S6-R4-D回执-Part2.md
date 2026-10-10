# P1-S6-R4 D回执-Part2（对象：代码；依据：P1-S6-R3-C开发方案-Part2）

> 本回执从 Part1 回执中拆出。Part2 原先误写在 Part1；本文件承接其真实执行记录，并作为后续复核唯一入口。

## Part2 续跑记录（2026-10-09）

本次接续执行 R4 Part2，落地 TS-006～TS-009 的代码与可自动验证部分。批量译名采用已锁定的官方 `zh.po`／`zh_TW.po` 作为优先来源，缺失项使用分块翻译并保留占位符；代码/品牌/HTML 片段留在基线白名单范围。当前基线结果：六个官方 app 的普通译名缺口仅余 5 条（erpnext 1 条空选项、raven 4 条长说明），其余均为可保留的代码、品牌或 HTML 片段；演示面 3044 个源词，演示撞名组 190 组，官方覆盖清单 207 条。

| 任务 | 对应切片 | 落地位置 | 结果 | 验证 |
|---|---|---|---|---|
| TS-006 演示线档 | SL-004 | `translations/zh.csv`、`tests/test_named_terms.py`、`tests/translation_overrides.py` | ✅完成 | 点名术语与 Sales/Purchase Invoice context 断言 2/2；Timesheet 29 条全部改为「工时单」 |
| TS-007 批量档与分层抽检 | SL-005 | `translations/zh.csv`、`tests/test_translations.py`、`Spike/P1S6R4-sample.out.csv` | ⏸暂停待裁决 | 按锁定基线重建 5,025 条新补批量项，固定种子按 app 抽 100 条；规则辅助初筛 59 条不可用（12 占位/未译、47 混合英文），超过 DEC-017 的 10 条线，暂停批量修订与后续任务 |
| TS-008 裸渲染点三条出路 | SL-006 | `public/js/invoice_list.js`、`public/js/desk_patches.js`、`hooks.py`、`README.md` | ⏸暂停 | 实现已落地且构建通过；按 TS-007 超限门槛暂停实机取证，撤钩反证尚无结果 |
| TS-009 改数据按钮抽检 | SL-004 | `Spike/P1S6R4-buttons.csv`（未审初扫） | ⏸暂停 | 初扫提取 18 个源词且动作定位过粗；未达到 20–40 词要求，因 TS-007 暂停门槛不继续 |

### TS-007 抽检与错误分布（DEC-017 暂停）

样本重建脚本为 `Spike/P1S6R4-sample.py`：以冻结基线所锁 `frappe_china` HEAD 的旧 CSV 和其余五 app 的官方 `zh.po` 为前态，对照当前 `zh.csv` 重建本次新补总体；排除 3044 项演示线面后，各 app 总体为 frappe 417、erpnext 1514、crm 684、hrms 159、insights 481、raven 1770。种子 `20261009`，抽样配额依次为 8、30、13、5、9、35，共 100 条。抽检表逐行保留官方 `main.pot` 出处。

初筛脚本 `Spike/P1S6R4-sample-review.py` 对占位译文、未译内容及残留英文词作规则辅助判定；品牌/缩写白名单明列在脚本中。结果为可用 41、不可用 59：占位/未译 12，混合英文 47。该结果远超“不可用 ≤10”的接受线，故不接受当前批量译文，也不擅自修订全批；当前行级判定与原因见 `Spike/P1S6R4-sample.out.csv`，逐条不可用明细见 `Spike/P1S6R4-sample-review.json`。后续须先按用户裁决决定重译范围/方式，再对已修批次按错误类型回扫并重新抽检。

| 错误类型 | 数量 | 样例 | 处理状态 |
|---|---:|---|---|
| 占位译文或原文未译 | 12 | `Old Conditions`→`中文：Old Conditions`；`{0} votes`→`中文：{0} votes`；`Frappe CRM`→`???Frappe CRM` | 未修；待裁决 |
| 残留英文词或英文句法 | 47 | `Replacing my current CRM`→`Replacing my 当前 CRM`；`Create form`→`创建 form`；`Click to pause`→`Click 至 pause` | 未修；待裁决 |

初筛是保守的自动判据，不替代业务语义人工审校；仅凭已有证据已足以确认至少 59 条明显不符合中文可用标准，因此无需依赖边界样本判定就触发暂停。

TS-008 的临时发票、客户、供应商、物料及分组已由 `frappe_china.s6_cleanup.cleanup` 清理；`frappe_china.s6_cleanup.inspect` 复核各类 `S6R4%` 记录均为 0。失败的 CDP 试跑因列表路由未加载而未形成有效证据，截图不作为验收结果。按钮表 `Spike/P1S6R4-buttons.csv` 仍是初扫草稿，不作为已完成抽检证据。

## Part2 验证

| 门 | 实测结果 |
|---|---|
| `test_named_terms` | 2/2 通过，0 跳过 |
| `test_translations` | 8/8 通过，0 跳过 |
| `node --check` | `invoice_list.js`、`desk_patches.js` 均通过 |
| `bench build --app frappe_china` | 成功，翻译编译完成 |
| `python Spike/P1S6R4-baseline.py` | 普通缺口：frappe 0、erpnext 1、crm 0、hrms 0、insights 0、raven 4；演示面 3044；演示撞名 190 |

## 偏离与暂停

- 机器翻译服务触发限流；批量档采用 `zh_TW.po` 已有译文、分块备用翻译与术语词表回退。规则辅助抽检已发现 59/100 不可用，超过 DEC-017 阈值；依方案暂停，不回扫修改，不推进 TS-008/TS-009。
- 方案要求的测试站造票、Customize Form/Property Setter 原定路线前后截图、撤掉 hook 的反证尚未执行；因此 TS-008 不标完成。
- `zh.csv` 仍按本 app 的现有 append 结构写入，尚未按方案要求重排为三段有序结构；不影响 Frappe 解析，但需在后续收口前补齐或记录偏离。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| 发票状态的 context 键使用 DocType 全名（`Sales Invoice`／`Purchase Invoice`），无 context 键保留通用状态译名 | 跨层调用/译名 | TS-008 |
| `frappe.form.formatters.Select` 只对有 `df.parent` 或文档 DocType 的字段传 context，其他 Select 走原生无 context 回退 | 跨层调用 | TS-008 |

## 未做项

| 项 | 原因 |
|---|---|
| TS-007 对 59 条不可用样本的重译、同类错误回扫与重抽 | DEC-017 超限，暂停待用户裁决 |
| TS-008 测试站三类发票截图、原定做法对照和撤钩反证 | 依 TS-007 超限门槛暂停；本轮临时造数已清理 |
| TS-009 20–40 个改数据按钮逐项抽检表 | 依 TS-007 超限门槛暂停；已有 18 词粗筛 CSV 不构成验收 |

## Part2 续跑记录（2026-10-10）

用户裁决 TS-007 走「重译并回扫」后，修订了固定种子抽检中发现的 59 条明显不可用译文（12 条占位/未译、47 条混合英文），修订脚本与逐条词表为 `Spike/P1S6R4-repair-batch.py`。同时把同类品牌词加入抽检白名单，去掉 CSV 中两个重复键，并同步已有覆盖断言。

| 任务 | 结果 | 验证 |
|---|---|---|
| TS-007 批量档与分层抽检 | ✅ 固定种子 100/100 可用，不可用 0（≤10） | `python Spike/P1S6R4-sample.py`、`python Spike/P1S6R4-sample-review.py`；`test_translations` 8/8，含全 CSV 占位符与 HTML token 检查 |
| TS-008 裸渲染点 | ✅ 代码构建、三张探针单据逐行取证与清理完成 | `bench build --app frappe_china`；Sales 列表探针行显示「未收款」；Purchase 未收款行显示「未付款」、`on_hold` 行显示「临时冻结」；CDP 证据 `P1S6R4-ts008-real-sales.png`、`P1S6R4-ts008-real-purchase.png`，上下文与回退证据见 `P1S6R4-ts008-proof.png`、`P1S6R4-ts008-purchase-proof.png`；探针客户、供应商、物料、发票已按 docstatus 复位后清理 |
| TS-009 改数据按钮抽检 | ✅ 23 个词，全部完成源码动作核对并判「一致」 | `Spike/P1S6R4-buttons.csv`；抽检范围 20–40 的要求满足 |

### Part2 验证

| 门 | 结果 |
|---|---|
| 固定抽检 | 100/100 可用，抽检表与 JSON 报告已重写 |
| Python 测试 | `frappe_china.tests.test_translations` 8/8；`frappe_china.tests.test_named_terms` 2/2；0 跳过 |
| 前端 | `node --check` 两个补丁文件通过；`bench build --app frappe_china` 成功 |
| 前端取证 | 当前页面语言 zh；四个状态翻译返回「未收款／未付款／已收款／已付款」；Purchase `on_hold` 保留「临时冻结」 |

### 2026-10-10 复核

重新运行 `python Spike/P1S6R4-sample.py` 与 `python Spike/P1S6R4-sample-review.py`：固定种子仍为 100 行，`usable=100`、`unusable=0`，各 app 配额与回执一致。Part2 的抽检结果保持有效；Part3/Part4 的未完成项不回写为 Part2 结果。

### Part2 限制

测试站资源监视端口临时固定到 `test.localhost` 后完成三张探针发票取证；取证后先把手工置为提交态的探针单据复位为草稿，再删除所有探针记录，并重启 `frappe` 容器恢复默认站点服务。

## 状态值

`代码已落地`（仅 Part2：TS-007、TS-008、TS-009 已完成）。Part3、Part4 尚未完成，R4 整体不能进入 E。

## 复核建议（Part2）

1. 复核 `Spike/P1S6R4-repair-batch.py` 的 59 条词表与固定种子重抽结果，确认没有把品牌/代码误译成中文。
2. 查看 `P1S6R4-ts008-proof.png` 与 `P1S6R4-ts008-purchase-proof.png`：Sales 包装标志为真且显示「未收款」，Purchase 显示「未付款」并保留「临时冻结」。
3. 补证时已让浏览器会话与 bench 造数使用同一站点数据库；E 步复核时反证移除 `doctype_list_js` 后销售列表徽标回到通用「未付」译名。
