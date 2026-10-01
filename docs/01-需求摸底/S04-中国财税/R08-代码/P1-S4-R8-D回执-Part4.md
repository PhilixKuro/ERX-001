# D回执（对象：代码 / 依据：P1-S4-R7-C开发方案-Part4）

**轮次**：P1-S4-R8｜**日期**：2026-10-01｜**步骤**：`plannedDev` D（build）
**依据**：[开发方案总纲](../R07-开发方案/P1-S4-R7-C开发方案-总纲.md)＋[Part4](../R07-开发方案/P1-S4-R7-C开发方案-Part4.md)

## 逐项执行结果

| 任务 | 对应切片 | 落地位置 | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-015 现金流四件套并入与修正 | SL-007 | 见 [D回执-Part3](P1-S4-R8-D回执-Part3.md) | ✅完成 | 2026-09-30 | 已在 Part3 执行并验证。 |
| TS-016 现金流量表 | SL-007 | 见 [D回执-Part3](P1-S4-R8-D回执-Part3.md) | ✅完成 | 2026-09-30 | 已在 Part3 执行并验证。 |
| TS-017 法定格式 PDF、导出核对与 LG-134 守卫 | SL-008 | 见 [D回执-Part3](P1-S4-R8-D回执-Part3.md) | ✅完成 | 2026-09-30 | 已在 Part3 执行并验证。 |
| TS-018 银行流水前置处理 | SL-009 | `frappe_china/accounting/bank_import.py`；`cn_tax/doctype/bank_statement_format/`；`cn_tax/doctype/bank_statement_preprocess/`；`tests/test_bank_preprocess.py` | ✅完成 | 2026-09-30 | 两个 DocType、CSV/XLSX/XLS 读取、UTF-8/GB18030 解码、表头定位、日期/金额/合计/重复校验、UTF-8 BOM 输出与表单入口已落地；7 项解析测试通过。 |
| TS-019 导入与对账测试 | SL-009 | `frappe_china/accounting/bank_import.py`；`tests/test_bank_preprocess.py` | ✅完成 | 2026-09-30 | 6 行 GB18030 流水经原生 Bank Statement Import 提交，中文、日期、金额逐行保留；同流水号 Payment Entry 自动核销；重复 CSV 跳过 6 行；xlsx 另导 6 行；Bank 映射导入前后均为空。 |
| TS-020 README、并入登记与译名 csv | SL-010 | `frappe-bench/apps/frappe_china/README.md`；`frappe_china/translations/zh.csv`；`tests/test_translations.py` | ✅完成 | 2026-09-30 | README 已覆盖定位、模块边界、开发测试、银行 worker 依赖、逐文件并入登记、不带入清单、已知限制与 MIT；14 个自有词条通过官方键零重叠和法定标签防串义测试。 |
| TS-021 演示站清站与建 `HDTH` | SL-010 | `docker/backups/保留-S4清站前/`；`erx.localhost` | ✅完成 | 2026-10-01 | 已取得用户明确确认；新增清站前备份后重装站点，执行 `seed-demo.sh --bare`、安装 `frappe_china`、设置中文/上海时区/`yyyy-mm-dd`/CNY/`Commercial Rounding`，创建 2026 会计年度与 `HDTH`。唯一公司、266 科目、自检通过、6 条报表模板、业务单据全为空。 |
| TS-022 全量回归 | SL-010 | `test.localhost`；`frappe_china/accounting/statements/labels.py` | ✅完成 | 2026-10-01 | 迁移后首轮发现 `Print Statutory Format` 被误列入法定标签守卫；移除该 UI 文案后，定向 4 项测试与全量 74 项回归均通过；演示站只读科目自检通过。 |

## 全量验证

| 门 | 结果 |
|---|---|
| TS-021 演示站验收 | ✅完成：站点设置、应用列表、HDTH 科目自检、默认科目、空业务数据、报表模板与静态资源均已核验 |
| TS-022 全量回归 | ✅完成：`test.localhost` 全量 74/74 通过；`System Settings` 的 `zh`、`Asia/Shanghai`、`yyyy-mm-dd`、`currency=null`、`Commercial Rounding` 基线保持不变；`erx.localhost` 唯一 HDTH 公司只读自检返回 `checked=True, ok=True`、266/266 科目、无缺失默认科目。 |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-018 | `tests/test_bank_preprocess.py` 覆盖 SL-009 验收第 5 条，以及 `_read` 的三种格式与两种编码 | `bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_bank_preprocess` | ✅ 7 项解析测试通过；三种格式的分派均覆盖，CSV 的 UTF-8 BOM 与 GB18030 均实解码；五条异常路径均断言。 |
| TS-019 | 导入、自动核销、重复导入与 xlsx 版本集成测试；测试站界面手工走一次并留截图 | 同一测试模块中的 `test_import_reconcile_duplicate_and_xlsx_equivalence` | ✅ 单项集成测试通过：6 行导入、1 笔自动核销、重复新增 0、xlsx 新增 6；界面手工验证仍待与 TS-020 后一并执行。 |
| TS-020 | `test_translations.py`；README 与 TS-015 表、需求 §4.2 逐条对照 | `bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_translations`；README 20 项关键词清单逐项断言；`python -m compileall -q frappe_china`；Ruff 对本任务测试文件单独检查 | ✅ 译名测试 1/1 通过；README 20/20 项命中；编译通过；`test_translations.py` 的导入排序已由 Ruff 修正，随后 `ruff check` 与 `ruff format --check` 均通过。 |

### TS-020 README 对照

| 对照项 | README 落点 | 结果 |
|---|---|---|
| 定位、装载位置、唯一模块与同名空侧栏 | 「定位与装载位置」「模块边界」 | ✅ |
| 测试站、全量命令、不 import `erpnext.tests.utils` | 「开发与测试」 | ✅ |
| 科目表 JSON 原样并入 | 「科目表、税与默认科目」第 1 行 | ✅ |
| 税模板两处科目号笔误、含税位置、9%／6% 进项 | 同表第 2 行 | ✅ |
| 默认科目 CSV 改科目号 JSON、删 5 字段、补 DEC-097 六项 | 同表第 3～5 行 | ✅ |
| `Products` 默认费用科目 | 同表第 6 行 | ✅ |
| 三个白名单入口、`create_charts`、flag 复位、不吞异常、`log_error`、`__file__`、`get_chart` 多余返回 | 「建账胶水层」 | ✅ |
| TS-015 现金流四件套逐文件修改 | 「现金流四件套」8 行对照表 | ✅ |
| 需求 §4.2 与 `field_property.csv` 不带入清单 | 「不带入」 | ✅ |
| 五项已知限制、银行后台 worker、MIT | 「已知限制」「银行对账」「许可」 | ✅ |
| TS-021 | SL-010 验收第 1–4 条，逐条在回执给出命令与输出 | 清站前备份、重装、bare 初始化、安装 app、站点设置与只读查询 | ✅ 通过；用户已确认清站；唯一公司为 `华东弹簧有限公司`（`HDTH`），266 科目且 `check_company_chart` 返回 `checked=True, ok=True`；6 个默认科目非空；9 类业务单据均为 0；`Financial Report Template` 为 6 条；Desk/ERPNext 静态资源返回 200。 |
| TS-022 | 测试站全量回归、演示站只读复核、证据汇总与临时文件清理 | `bench --site test.localhost run-tests --app frappe_china`；`bench --site erx.localhost execute frappe_china.accounting.selfcheck.check_all_cn_companies`；读取 `System Settings` | ✅ 首轮 74 项中 73 项通过、1 项因 UI 文案误入法定标签集合失败；修复后定向 4 项与全量 74 项均通过（270.082s）；测试站基线未变；演示站自检唯一公司 `华东弹簧有限公司`（`HDTH`）返回 `ok=True`、266/266。 |

## 偏离与暂停

- 方案偏离：无。
- TS-021 已按 DEC-101 在用户明确确认后执行；重装前备份保存在 `docker/backups/保留-S4清站前/`，演示站原有业务数据已按确认范围清除。
- 全 app Ruff 基线尚未清零：`ruff check frappe_china` 报 85 项（RUF001 56、I001 26、F402 1、F823 1、B905 1），`ruff format --check frappe_china` 报 29 个文件待格式化；TS-020 自身的测试文件已单独清零。本任务不扩散修改其余任务文件。
- TS-022 首轮回归暴露 `Print Statutory Format` 被误纳入 `LEGAL_LABELS`；已从 `frappe_china/accounting/statements/labels.py` 移除，译名仍保留在 `translations/zh.csv` 供报表按钮使用。

## 新增约定

| 约定 | 类别（命名/位置/错误处理/依赖/跨层调用） | 在哪个任务确立 |
|---|---|---|
| 非 UTF-8 或须保留 BOM 的附件，创建时用 `File.content` 写原始字节，读取时从 `File.get_full_path()` 以二进制打开；不得用旧 `frappe.utils.file_manager.save_file` 承载此类内容，因为 File 插入会按 `windows-1250` 兜底解码并改写字节 | 跨层调用 / 错误处理 | TS-018／TS-019 |

## 未做项

| 项 | 为什么没做 |
|---|---|
| TS-019 界面手工走一次并留截图 | 自动化集成链已通过；本次续跑无浏览器执行工具，界面证据仍待补。 |
| 全 app Ruff 基线清理 | 跨越 TS-020 范围，且包含法定中文全角标点的 RUF001 误报与此前任务文件的格式问题，留待单独处理。 |

## 状态值

**进行中**——TS-001～022 的实现与自动化验证已完成；R8 仅保留 TS-019 界面截图与全 app Ruff 基线等未做项。

## 复核建议

1. 抽查 README「相对 zelin 的修改」是否与 TS-015 表及需求 §4.2 逐项一致，重点看默认科目 5 个删除字段、DEC-097 六项和现金流四件套。
2. 抽查 `translations/zh.csv` 只含本 app 自有词条，且没有以其它源词映射到法定报表标签。
3. 决定是否单独清理全 app Ruff 基线；该清理不改变 TS-020／TS-022 的通过结论。
4. 补做 TS-019 界面手工流程并留截图。
