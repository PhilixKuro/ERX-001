# P1-S8-R6 D 回执 · Part1

**日期**：2026-10-21｜**执行者**：Codex｜**打 tag**：否
**依据**：[R5 开发方案·Part1](../R05-开发方案/P1-S8-R5-C开发方案-Part1.md)及总纲。

## 逐项执行结果

| 任务 | 对应切片 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-001 骨架、装序、after_commit | SL-001 | `frappe-bench/apps/frappe_debug/frappe_debug/tests/test_smoke.py:8`、`frappe-bench/apps/frappe_china/frappe_china/install.py:203` | ✅完成 | 2026-10-21 | 私有仓库已创建、本地骨架已建并安装到测试站；`frappe_debug` 冒烟 1/1 通过，装序检查 `ok: true`；after_commit 提交／回滚两条定向测试已分别通过，Ruff 检查通过。`frappe_debug` 已提交并推送，commit=`616d897`；`apps.json` 与锁文件仍待按方案登记锁定 commit |
| TS-002 账务修正与迁移 | SL-002 | `frappe-bench/apps/frappe_china/frappe_china/accounting/stock_entry_accounts.py:11`、`frappe-bench/apps/frappe_china/frappe_china/patches/s8_cn_accounting_defaults.py:7`、`frappe-bench/apps/frappe_china/frappe_china/tests/test_s8_accounting.py:11` | ✅完成 | 2026-10-21 | 新公司默认、迁移范围／幂等／自定义值保留、银行方式补齐与付款取科目、制造差异科目中式隔离均有测试；完工入库集成实测生成工序成本并只记 `1405`／`1409`／`410199`，无损益行及「Cost of Goods Sold」提示 |
| TS-003 损耗率字段与整体值 | SL-003 | `frappe-bench/apps/frappe_china/frappe_china/production/process_loss.py:1`、`frappe-bench/apps/frappe_china/frappe_china/tests/test_process_loss.py:1`、`frappe-bench/apps/frappe_china/frappe_china/fixtures/custom_field.json` | ⚠️部分 | 2026-10-21 | A18 整数精度算法、BOM 钩子、工序字段、前端只读与提示已实现；测试先红（缺模块）。测试站 migrate 已同步 fixtures 并执行 TS-002 补丁，但最终卡在 Docker 挂载目录 I/O；TS-003 红绿与字段表确认尚未完成 |
| TS-004 反算、超产、按订单放大 | SL-003 | — | ⬜未开始 | — | |
| TS-005 税模板沿用与改名 | SL-004 | — | ⬜未开始 | — | |
| TS-006 工时与 BOM 工序列 | SL-005 | — | ⬜未开始 | — | |
| TS-007 换 BOM 人确认 | SL-006 | — | ⬜未开始 | — | |
| TS-008 补货口径与呈现 | SL-007 | — | ⬜未开始 | — | |
| TS-009 译名与显示 | SL-008 | — | ⬜未开始 | — | |
| TS-010 策略对比报表 | SL-009 | — | ⬜未开始 | — | |
| TS-011 侧栏入口 | SL-009 | — | ⬜未开始 | — | |
| TS-012 前置数据 | SL-010 | — | ⬜未开始 | — | |

## 全量验证

| 门 | 结果 |
|---|---|
| 执行前 frappe_china Python 基线 | 未完成：长测于 33/约 400 测试中断；期间代码已变化，不能作基线 |
| 执行前 Node 基线 | 89/89 通过 |
| frappe_china TS-002 定向验证 | `test_company` 14/14 通过；迁移扩展、制造科目隔离、`test_s8_accounting` 完工入库、`frappe_debug` 冒烟各 1/1 通过 |
| `frappe_debug` | 冒烟 1/1；Ruff check 与 format check 通过 |
| TS-003 本地静态检查 | Ruff check／format、JS 语法、Custom Field JSON 均通过；集成测试未能启动完成 |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-001 | SL-001 ①②④ 贴命令输出；③ 单测 test_install.py 加两条；记两套测试用例数基线 | `Spike/P1S8R6-D/install_cache_probe.py`；测试站 `check_app_order`、`frappe_debug.tests.test_smoke`；after_commit 定向测试 | 安装后 `check_app_order` 返回 `ok: true`；冒烟 1/1 通过；提交后清缓存／回滚不清缓存均通过。验收 grep 的测试源码额外命中已记偏离 |
| TS-002 | SL-002 ①～⑥；迁移测试二次运行无改动；账务单据 GL 与提示 | `test_company`、`test_s8_accounting`（test.localhost） | 新公司 `410199`、四种银行方式 `1002`；迁移补缺不覆盖自定义值、非中式不动且重复运行通过；付款默认函数返回 `1002`；完工凭证只含 `1405`／`1409`／`410199`，无 Income／Expense 行，`400101` 无余额，保存无 COGS 提示；通过 |
| TS-003 | `test_process_loss.py`：六个数量各存两次、手填保持、非整数单位精度 | 先跑红测，测试发现生产模块缺失；实现后执行测试站 `migrate` | migrate 显示 `frappe_china` DocType 同步 100%、fixtures 同步及 TS-002 补丁成功，但进程随后卡在 Docker 挂载目录 I/O 等待；红绿测试与字段表正向查询待续跑 |

## 偏离与暂停

- 概况原预设执行者 Claude，本次按用户“继续开发项目”由 Codex 接续。
- 全量 Python 基线启动后才确认运行时间超过预期，且后续编辑导致它不再是干净基线；已在约 33 个测试处中止。仅以定向测试验证改动。
- 验收 grep 会命中 `test_install.py` 的装序测试中预期值；保留可读的测试断言，因此相比方案声称的「只命中 install.py 与 README」有测试源码额外命中。
- TS-003 开发期间测试站 migrate 与 web 进程进入不可中断的 Docker `p9_client_rpc` 文件系统等待，超 6 分钟未退出；未重启容器，以免影响现有站点状态。该环境阻塞不代表 TS-003 测试通过。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| frappe_debug 普通包 builders／scenario／demo，注册模块目录装 DocType／Page，配置在 data；依赖单向指向 frappe_china | 位置／跨层调用 | TS-001（方案 A1） |

## 未做项

| 项 | 为什么没做 |
|---|---|
| apps.json 新 app 条目 | 方案 TS-001 要求远程推送后填锁定 commit；本次已推送 `frappe_debug`（`616d897`），但尚未更新 apps.json 与锁文件 |
| TS-003 后续验证、TS-004～TS-012 | 尚未完成；TS-003 已部分落地，须先恢复测试站验证 |

## 状态值

执行中，尚未满足“代码已落地”。续跑从 TS-003 开始：先确认测试站 Docker I/O 已恢复、查询 Custom Field 与 hooks，再跑 `test_process_loss`；不能因已同步 fixtures 就跳过红绿验证。

## 复核建议

本步进行中，验证完成后补实际复核位置与薄弱项。
