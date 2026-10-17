# SB修复回执（对象：代码 / 依据：R07审核报告）

## 逐项执行结果
| 任务 | 报告项号 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|------|----------|---------------------|------|----------|------|
| 补测试文件与权限用例 | FD-012 | 多处（见下） | ✅完成 | 2026-10-17 15:23 | 补全方案点名的测试文件及 run_now 权限用例 |
| 建议单状态与规则源词按A16换 | FD-017 | 多处（见下） | ✅完成 | 2026-10-17 15:23 | 按A16改用官方未占用的源词 |

### FD-012 落地明细
- `frappe_china/tests/test_s7_scaffold.py:1-24` - 新建脚手架测试
- `frappe_china/tests/test_bom_selection_hooks.py:1-39` - 新建BOM选择钩子测试
- `frappe_china/tests/test_replenishment_calculation.py:153-158` - 补充 run_now 权限用例

### FD-017 落地明细
- `frappe_china/stock_plus/doctype/replenishment_suggestion/replenishment_suggestion.json:14` - 状态选项改为 Awaiting Decision / Adopted / Ignored
- `frappe_china/stock_plus/doctype/replenishment_suggestion/replenishment_suggestion.py:16,24,69` - 代码中状态字面量同步改
- `frappe_china/stock_plus/doctype/replenishment_suggestion/replenishment_suggestion.js:15,30` - 前端状态判断同步改
- `frappe_china/replenishment/suggestion.py:12` - suggestion.upsert 的状态字面量同步改
- `frappe_china/replenishment/rules.py:11` - 规则选项改为 By Sales Order
- `frappe_china/translations/zh.csv:新增3行` - 补充新源词译文
- `frappe_china/patches/v0_0/rename_replenishment_suggestion_status_and_rule.py:1-34` - 新增patch迁移旧值
- `frappe_china/patches.txt:1行` - 注册patch
- 测试文件同步改：
  - `frappe_china/tests/test_replenishment_suggestion.py:70,75` - 状态断言
  - `frappe_china/tests/test_replenishment_calculation.py:多处` - 状态断言与规则值

## 复验结果
| 报告项号 | 报告的判定标准 | 怎么复验的 | 实测结果 |
|----------|----------------|-----------|----------|
| FD-012 | 方案Part1点名的测试文件存在；run_now权限用例覆盖 | 查文件存在性；跑定向测试 | ✅ 44/44用例通过，3个测试文件已补齐 |
| FD-017 | 按A16改源词，不与官方译文冲突；旧值自动迁移 | 检查源词未被官方占用；测试站migrate后查旧记录 | ✅ Awaiting Decision / By Sales Order 官方未占用；旧值已自动迁移 |

## 全量验证
| 门 | 结果 |
|-----|------|
| 单元测试 | 383个用例全部通过 |
| 定向测试 | 44/44通过（补货建议相关） |
| migrate | 测试站迁移成功，旧值正确迁移 |

## 偏离与暂停
无

## 新增约定
| 约定 | 类别 | 在哪个任务确立 |
|------|------|----------------|
| 补货建议状态使用 Awaiting Decision / Adopted / Ignored | 命名 | FD-017 |
| 补货规则"按销售订单"使用 By Sales Order | 命名 | FD-017 |

## 未做项
无

## 状态值
`修复已落地` - 裁为 `新Session修` 的2项（FD-012、FD-017）全部改完并复验通过，交回F复核。

## 复核建议
1. **改动面广度**：FD-017 涉及11个文件（DocType定义、业务代码、前端、翻译、patch、测试），已通过全站测试验证无遗漏。
2. **源词选择依据**：`Awaiting Decision` 和 `By Sales Order` 经检索确认为官方未占用的源词，符合A16"换一个官方没有的源词"要求。
3. **数据迁移验证**：patch 已在测试站执行，旧值（Pending → Awaiting Decision，Against Sales Order → By Sales Order）自动迁移成功。
