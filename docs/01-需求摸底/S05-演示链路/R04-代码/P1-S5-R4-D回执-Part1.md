# D 回执（对象：代码 / 依据：P1-S5-R3-C开发方案-Part1）

## 逐项执行结果

| 任务 | 对应切片/优化项 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-001 | SL-001 | [docker/apps.json](/D:/ERX-001/docker/apps.json:1) | ✅完成 | 2026-10-05 | 七条按方案顺序写入；四个官方 App 标记 `official=true`，Insights 使用 `tag=v3.14.2`。 |
| TS-002 | SL-001 | [install.py](/D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/install.py:9) | ✅完成 | 2026-10-05 | 新增 `target_app_order` 与幂等 `reorder_installed_apps`；11 个安装测试通过。 |
| TS-003 | SL-001 | [setup.sh](/D:/ERX-001/docker/scripts/setup.sh:133) | ⚠️部分 | 2026-10-05 | 已完成 ref/tag 解析、预检、按清单安装、归位与未声明 App 警告；仅完成 `bash -n`，端到端重建留 TS-015。 |
| TS-004 | SL-001 | [lock-apps.sh](/D:/ERX-001/docker/lock-apps.sh:31) | ✅完成 | 2026-10-05 | 保持清单顺序、tag、官方 URL；`--show` 已在容器中实跑，当前未克隆条目保留并告警。 |
| TS-005 | SL-002 | [hr.py](/D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/accounting/hr.py:17) | ⚠️部分 | 2026-10-05 | 预配、回填、建账入口与 HRMS 安装钩子已落地；3 个定向测试通过。HRMS 未装，5 类型正向落库与安装后回填留 TS-006。 |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-001 | `apps.json` 顺序、commit 长度、tag/branch 字段 | 容器 Python 解析 `docker/apps.json` | 7 条；每个 commit 40 位；Insights 为 tag `v3.14.2`；通过 |
| TS-002 | `bench ... run-tests ... test_install` | `docker compose exec ... bench ...` | 11/11 通过 |
| TS-003 | `bash -n docker/scripts/setup.sh` | 容器内 `bash -n` | 通过；端到端重建待 TS-015 |
| TS-004 | `lock-apps.sh --show` 与保序/tag 检查 | 容器内配置 safe.directory 后运行 `bash ... --show` | 输出保留 7 条顺序；官方/缺失条目提示正确；通过 |
| TS-005 | HR 预配边界、聚合缺项、回填筛选 | `bench ... test_hr` | 3/3 通过；HRMS 正向安装验证待 TS-006 |

## 全量验证

| 门 | 结果 |
|---|---|
| Part1 定向测试 | 27/27 通过（test_install 11、test_hr 3、test_company 13） |
| JSON / shell 静态检查 | `company_defaults.json` 解析通过；两个 shell `bash -n` 通过 |
| Ruff | 未执行：容器与 bench venv 均无 `ruff` 模块 |
| 全量回归 | ⬜未开始（由 Part4 TS-016 执行） |

## 偏离与暂停

方案未偏离。TS-003 的端到端重建与 TS-005 的 HRMS 正向落库验证按方案顺序移交 TS-006/TS-015；未用未验证结果替代实测。

## 新增约定

| 约定 | 类别（命名/位置/错误处理/依赖/跨层调用） | 在哪个任务确立 |
|---|---|---|
| `apps.json` 条目按安装顺序排列；`official` App 仅保留只读 `upstream`；`tag` 与 `branch` 二选一 | 依赖/跨层调用 | TS-001 / TS-004 |
| `frappe_china.install.reorder_installed_apps` 是安装脚本与人工修复共用的归位入口 | 跨层调用 | TS-002 / TS-003 |
| HRMS 未装时按 DocType 名零动作，不在 `frappe_china` 顶层导入 HRMS | 依赖/错误处理 | TS-005 |

## 未做项

| 项 | 为什么没做 |
|---|---|
| HRMS 安装后 5 个报销类型的正向落库验证 | 当前测试站未安装 HRMS，按方案留至 TS-006；代码与无依赖边界已测试 |
| 空目录重建与坏 tag 预检实测 | 属 TS-015 的端到端验证，Part1 不提前执行 |

## 状态值

`⚠️部分`：Part1 任务代码已落地；两项依赖四 App 安装/空目录重建的验收留待后续任务，D 步整体尚未收口。

## 复核建议

方案留白最大的两处是 `target_app_order` 的未知 App 保序和 HRMS 类型缺失处理：前者保留未知 App 相对顺序并将其置于业务 App 与尾部 App 之间，后者告警并跳过，以免历史数据删类型导致建账失败。测试最薄的是 HRMS 正向安装路径，需在 TS-006 装 HRMS 后核对五个 `Expense Claim Account` 行与不产生 `Expense Claims` 科目。当前没有方案外代码偏离；Ruff 因环境未安装未执行。
