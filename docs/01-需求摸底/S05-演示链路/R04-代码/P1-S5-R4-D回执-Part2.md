# D 回执（对象：代码 / 依据：P1-S5-R3-C 开发方案 Part2）

## 逐项执行结果

| 任务 | 对应切片 | 落地位置 | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-006 | SL-003 | 测试站 `test.localhost` | ✅完成 | 2026-10-05 | CRM、HRMS、Raven、Insights 均安装；`_FCT 入口二` 在安装 HRMS 前创建；HRMS 安装后 5 行 `Expense Claim Account`、266 个科目、无 `Expense Claims`；归位完成。 |
| TS-007 | SL-004 | — | ⏸未执行 | 2026-10-05 | 按约束，测试站全量回归通过前不修改演示站；本轮未触碰 `erx.localhost`。 |
| TS-008 | SL-004 | [install.py](/D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/install.py:5)、[test_install.py](/D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/tests/test_install.py:1) | ✅完成 | 2026-10-05 | 新增 `check_app_order`；正向、错误顺序、缺少覆盖三组测试通过；测试站真实反证完成并恢复。 |

## 方案要求的验证

| 任务 | 怎么跑的 | 实测结果 |
|---|---|---|
| TS-006 | `docker-compose.exe -f docker/compose.yaml exec -T -w /workspace/frappe-bench frappe bench --site test.localhost install-app {crm,hrms,raven,insights}`；随后 `reorder_installed_apps`、清缓存、重启容器 | `list-apps` 含四个 App；`installed_apps` 为 `frappe, erpnext, crm, hrms, insights, raven, frappe_china`；`_FCT 入口二` 266 个科目、5 行报销科目、无 `Expense Claims`。 |
| TS-008 正向 | `bench --site test.localhost execute frappe_china.install.check_app_order` | `ok=true`；`order_ok=true`、`overrides_ok=true`、`translation_ok=true`、`company_checks_ok=true`；探针 `Formula`：期望/实际均为 `计算方式`，HRMS 竞争译名为 `公式`。 |
| TS-008 反向 | 将测试站顺序临时改为 `... crm, frappe_china, hrms, insights, raven`，清缓存后调用同一函数，再归位并重启 | `ok=false`、`order_ok=false`、`translation_ok=false`；实际探针为 `公式`；归位后再次 `ok=true`。 |

## 全量验证

| 项目 | 结果 |
|---|---|
| `frappe_china` 全量回归 | 170/170 通过，耗时 628.498 秒 |
| Part2 定向测试 | `test_company` 13/13、`test_hr` 3/3、`test_install` 14/14 通过 |
| `check_app_order` 正反证 | 单元测试 3/3 通过；真实测试站反证通过并恢复 |
| Shell / JSON 静态检查 | `setup.sh`、`lock-apps.sh` `bash -n` 通过；`company_defaults.json` 解析通过 |

## 实测钩子顺序（LG-139）

测试站当前 `frappe.get_hooks("doc_events")["Company"]["on_update"]` 顺序为：

```text
hrms.overrides.company.make_company_fixtures
hrms.overrides.company.set_default_hr_accounts
hrms.overrides.company.set_expense_claim_type_accounts
frappe_china.accounting.company.on_update
```

因此 `frappe_china` 的中国科目表兜底清理在 HRMS 公司钩子之后执行；新建中国公司通过预置 5 行报销科目避免生成通用科目，已有公司复制路径保留 ERPNext 原生科目复制。

## 新增约定

| 约定 | 类别 | 确立任务 |
|---|---|---|
| 每次安装新 App 后执行 `reorder_installed_apps`，再用 `check_app_order` 验证顺序、覆盖、探针翻译和中国公司自检 | 依赖 / 跨层调用 | TS-008 |

## 偏离与暂缓

TS-007 演示站接入暂缓，原因是本轮约束要求演示站必须等测试站全量回归通过后再修改；本轮未对演示站做任何写操作。

## 状态

`✅ Part2 已完成（TS-007 按约束暂缓）`

## Supplementary verification (2026-10-06)

| Task | Slice | Result | Evidence |
|---|---|---|---|
| TS-009 | SL-005 / SL-007 | Passed | `configure-apps.sh` is idempotent on `test.localhost`; CRM integration validation creates the cross-app fields; ERPNext CRM data synchronization is enabled; Raven keeps 15 read-only tools and the bot; LiteLLM connection remains skipped when `RAVEN_LLM_*` is absent. |
| TS-010 | SL-005 | Passed | Temporary test data completed Item sync -> CRM Lead -> CRM Deal -> submitted Quotation (`quotation_to=CRM Deal`) -> submitted Sales Order. The Sales Order hook created the Customer from the Deal, both transaction currencies were CNY, the mapped item was present, and the forecast dashboard returned the Deal month. All temporary records were removed. |
| TS-011 | SL-006 | Passed | `insights.tests.test_basic_workflow.TestBasicWorkflow.test_query_execution`: 1/1 passed against the `Site DB` data source. |

The full `frappe_china` regression remains blocked by pre-existing invalid HRMS `Expense Claim Type` links (`FCT_TEMP`, `_FCT 入口二`, `5602090 - 管理费用_办公费 - FCT2`, `5602090 - 管理费用_办公费 - FCT3`). The test site was not cleaned without an explicit data-cleanup decision. TS-007, external-device checks, and LiteLLM connection/model tests remain deferred.
