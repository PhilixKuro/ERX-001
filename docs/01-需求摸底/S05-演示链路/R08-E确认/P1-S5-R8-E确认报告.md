# 确认报告（对象：P1-S5 R7 D 步落地＋R5 SB 修复 / 清单：R6 开发方案＋R5 E 确认报告的未通过项）

**轮次**：P1-S5-R8｜**日期**：2026-10-07｜**步骤**：`plannedDev` E（confirm，复核）｜**执行者**：Claude（Opus 5.5）｜`打tag=否`
**清单**：[R6 C开发方案](../R06-开发方案/P1-S5-R6-C开发方案.md) TS-017～020；[R5 E确认报告](../R05-确认报告/P1-S5-R5-E确认报告.md) 交 SB 的 8 项与交 C 的 2 项
**待核声称**：[R7 D回执](../R07-D代码/P1-S5-R7-D回执.md)、[R5 SB修复回执](../R05-确认报告/P1-S5-R5-SB修复回执.md)
**被核对物**：`frappe_china` HEAD `4b21aae`（与 `origin/main`、`docker/apps.json` 一致）；主仓库 HEAD `ff00729`（工作区干净）；测试站 `test.localhost`、演示站 `erx.localhost`

> 本步只对两份回执所声称的内容逐项复核，不另找清单外的漏（那是 F 步）。R5 已判通过或已裁决延迟的项只做反向确认。

## 逐项确认

结论：✅ 通过／❌ 未通过（附 IT 号）／⏸ 未通过·已裁决延迟（编号）。

### 一、R6 方案任务（R7 D 步）

| # | 清单项 | 落地否 | 生效否 | 根因消除否 | 验收标准 | 验证方式（本步实跑） | 结论 |
|---|---|---|---|---|---|---|---|
| TS-017 | 删公司清理 | ✅ `company.py` `is_cn_company`／`on_trash`；`hr.py` `clear_company_expense_claim_accounts`；`hooks.py:160` | ✅ 钩子已注册；`before_insert` 改用 `is_cn_company` | ✅ 两站悬空 `Expense Claim Account` 行均 0 | SL-011 ①～⑤ | 专项 15/15；变异（注释 `on_trash` 两行删除）→ SL-011 七例全部报错，连带 SL-012 六例在建公司时报 `LinkValidationError`（就是 IT-001 那条），还原后 `git diff` 空 | ✅ |
| TS-018 | 保存前预配与兜底科目 | ✅ `company_defaults.json` `expense_claim_type_fallback`=5602250 且 `_comment` 已补；`hr.py` 遍历站上全部类型；`company.py` `validate`；`hooks.py:158` | ✅ | ✅ | SL-012 ①②④⑤⑥②③④ | 变异（去掉 `hooks.py` 的 `validate`）→ 恰 3 处失败：SL-012 ① zh／en 的「`repointed` 为空」断言（终态仍对，被改挂救回）与 ⑥②，与 R6 方案预期、R7 回执所述一致；还原后清缓存 | ✅ |
| TS-019 | 复制建账改挂，删旧逻辑 | ✅ `hr.py` `repoint_generic_expense_claim_accounts`；`on_update` 改调它 | ✅ | ✅ 源码（测试外）无 `_remove_hrms_expense_claim_account`、无 `_("Expense Claims")` | SL-012 ③⑥①⑦ | 变异（`repoint` 直接返回）→ SL-012 ③ zh／en／复制的复制、①、④、⑤、⑥① 等子用例共 25 处失败（出现「费用报销记录」科目、科目号为空）；还原 | ✅ |
| TS-020 | 全量回归与收尾 | ✅ README「已知限制」两条在 | — | ✅ | 完成标准两条 | 全量见下；测试站 `_FCT` 前缀公司只剩 `_FCT CRM 验证`（见 IT-030）；悬空行 0 | ✅（残留另记 IT-030） |

### 二、R5 交 SB 的 8 项（SB 修复回执）

| # | 清单项 | 落地否 | 生效否 | 根因消除否 | 判定标准 | 验证方式（本步实跑） | 结论 |
|---|---|---|---|---|---|---|---|
| IT-005 | 演示站接入四个 App | ✅ | ✅ | ✅ | SL-004 ①②③④⑥ | 演示站 `check_app_order`：`ok`／`order_ok`／`overrides_ok`／`translation_ok`／`company_checks_ok` 均真，`problems` 空；`Formula` 实得「计算方式」，竞争者 `{hrms: 公式}`。SB 的复核脚本以只读方式（`--no-save --config`）重跑 37/37 通过：HDTH 科目 266、自检 `ok`、报销行 5 行与映射逐行一致、业务计数 0；七个 app HEAD 与 `apps.json` 一致、工作区空；`保留-S5装App前/` 4 个文件在 | ✅ |
| IT-006 | SL-002 测试补齐 | ✅ `test_expense_claim.py` 7 例；`test_scaffold.test_hrms_is_optional` | ✅ | ✅ | TS-005 第 5 条 ①～⑧ | 变异（去掉 `build_cn_company` 末尾预配）→ ①③ 失败，与回执一致；还原 | ✅ |
| IT-013 | 配置脚本拆分与补齐行为 | ✅ 宿主入口＋`docker/scripts/configure_apps.py` 三函数 | ✅ | ⚠ | Part3 TS-009 | 测试站：正常跑「无改动」rc=0；公司不存在 rc=1、未知参数 rc=2，文案对。**演示站 bot `model` 为 `gpt-4o`，脚本与回执都说「留空」** | ❌ IT-029 |
| IT-014 | 报表通道与工具描述 | ✅ | ✅ | ✅ | 改正偏离；描述中文；报表名与过滤键 | 两站 `Raven AI Function` 各 15 条，类型只有 Get List 8／Get Document 6／Get Report Result 1；`run_report` 为 Get Report Result；描述里 6 张报表在演示站均存在（Script Report）；`ai/queries.py` 已无 `run_report` | ✅ |
| IT-017 | CRM 链路重做 | ✅ | ✅ | ✅ | 裁决后为脚本化＋关键值 | 测试站重跑 `P1-S5-R5-IT017-crm-chain.py`：29/29 通过、`EXIT=0`、清理后残留 0（日志 `frappe-bench/logs/s5-r8-it017.log`） | ✅ |
| IT-018 | Insights 演示站验收 | ✅ | ✅ | ✅ | SL-006 ②③ | 看了查询截图（`count_of_rows` 列为 1）；演示站 `Insights Workbook`／`Query v3`／`Query Reference` 均 0，无残留。未重跑脚本（会再写演示站） | ✅ |
| IT-024 | 本机连通基线 | ✅ `run()` 轮询带 `use_local_cache=False` | ✅ | ✅ | SL-008 ① | 重跑 `P1-S5-R5-IT024-local-baseline.mjs`：失败 0 项。通过 572.3 ms；页面未开 → 失败；停 proxy → 失败；起 proxy 刷新后 → 通过 584.6 ms。proxy 已恢复运行（日志 `s5-r8-it024.log`） | ✅ |
| IT-026 | 新基准点与常驻文件回写 | ✅ | — | ✅ | SL-010 ⑤⑥ | `保留-S5装App后/` 4 个文件在，`20261007_011313` 是根目录最新一套；`项目概况.md` 演示站状态、端口、HRMS、备份基准点已改写；`开发守则.md` 新增五节在；路线文档 v1.7 | ✅ |

### 三、R5 交 C 的 2 项

| # | 清单项 | 结论 |
|---|---|---|
| IT-002 | 删一次中式公司后全站建不出公司 | ✅ 由 TS-017 消除（见上） |
| IT-003 | 保存公司清零报销映射 | ✅ 由 TS-018／019 消除（见上） |

---

## 问题详情

三格取值见流程规范 §2.3。

**IT-029 演示站 bot `model` 实为 `gpt-4o`，脚本提示与 SB 回执都说「留空」**
- 现象：演示站与测试站 `ERX 分析助手` 的 `model` 都是 `gpt-4o`。`configure_apps.py` 在 `RAVEN_LLM_MODEL` 未设时打印「bot 的 model 不改（新建时留空）」；SB 回执复核建议 3 写「bot 的 `model` 为空」。
- 定位：Raven `raven_bot.json` 的 `model` 字段 `default: gpt-4o`，新建时框架填缺省值。R3 Part3 第 28 行要求未设时「`model` 留空并打警告」。
- 影响：现在不影响任何功能（Raven 连接字段没开）。SH-P1S5006 接 LiteLLM 时，若只填 URL／KEY、不填 MODEL，bot 会拿 `gpt-4o` 去请求 LiteLLM，报错原因不直观。
- 建议：改 `configure_apps.py` 那句提示为实情（「新建时取 Raven 缺省 `gpt-4o`」）；SH-P1S5006 描述补一句「须同时设 `RAVEN_LLM_MODEL`」。
- 建议档位：`本Session修`｜待裁决点：要不要让脚本在 MODEL 未设时把 `model` 显式写空。合方案字面，但表单再保存时是否又回填 `gpt-4o` 未验；建议不写空，只改提示 → **用户裁决（2026-10-07）：按建议**｜状态：已修复（见当场修清单）

**IT-030 测试站留有 `_FCT CRM 验证` 公司，且 CRM 集成指向它，SB 回执没有申报**
- 现象：测试站 `_FCT` 前缀公司剩 1 家 `_FCT CRM 验证`（中式），`ERPNext CRM Settings.erpnext_company` 指向它。R6 方案 TS-020 第 2 步的残留核对要求「无 `_FCT` 前缀公司」；SB 在 IT-013 建它、IT-017 用它，之后保留，回执未写。
- 影响：功能上是有用的——IT-017 脚本靠它跑，全量回归 205 条也照过。风险在 `_FCT` 前缀本来表示「测试临时数据」，延迟中的 `raven_dataset.py` 按前缀强删（IT-019 已记），重写前若被调用会删掉它。
- 建议：保留作测试站 CRM 夹具，在 `docker/README.md`「配置四个 App」节记一句它的用途；或删掉，IT-017 脚本改为自建自删公司。
- 建议档位：`延迟或不修`（不做，本报告留档即可）｜待裁决点：保留并记一句，还是删除 → **用户裁决（2026-10-07）：按建议，保留、不做**｜状态：不做

## 当场修清单

| # | 对应未通过项 | 改动位置（文件:行） | 用户确认于 |
|---|---|---|---|
| 1 | IT-029 | `docker/scripts/configure_apps.py:266-267` 提示改为「新建时取 Raven 缺省 gpt-4o；接 LiteLLM 时须同时设 RAVEN_LLM_MODEL」并注出处；`docker/README.md`「配置四个 App」节 `RAVEN_LLM_MODEL` 行补同一说明；Stage 概况登记册 SH-P1S5006 补「三个须一起设」 | 2026-10-07「都按你的建议」 |

修后验证：测试站 `docker/configure-apps.sh --site test.localhost` 输出新提示、「无改动」、rc=0。只改提示文字，不涉代码路径，未重跑全量。

## 全量回归 + 未执行项

**回归**：`bench --site test.localhost run-tests --app frappe_china`（日志 `frappe-bench/logs/s5-r8-regression.log`，2026-10-07 本步实跑）：**Ran 205、OK、`EXIT=0`**，205 条全 ✔、跳过 0，耗时 979 秒。对比 R7 的 196、R5 的 180、S4 的 160：只增不减 ✅。

**判别力变异**（本步自己做，每次跑完还原、`git diff` 空）：TS-017／018／019、IT-006 各一次，均有测试失败，详见逐项表。日志 `s5-r8-mut-*.log`。

**未执行项反向确认**：
- 已裁决延迟的未被意外改动：`ai/queries.py` 仍是 IT-015 所记的 4 个函数；`tests/raven_dataset.py` 文件头仍注明不可用（IT-019）；`docker/.env` 无 `RAVEN_*`，两站 `Raven Settings` `enable_ai_integration=0`（SH-P1S5006）✅
- 上游源码未改：frappe、erpnext、crm、hrms、insights、raven 工作区全空，四个官方 App 只有 `upstream` remote ✅
- 演示站无测试痕迹：`_FCT` 公司 0、Insights 工作簿与查询 0、`Translation` 0 ✅

## 总体结论

**全部通过**（裁决后）。复核时新出 2 项：IT-029 已当场修，IT-030 裁为不做（留档）。R6 方案四个任务、R5 交 SB 与交 C 的 10 项全部复核通过，全量 205/205。

两份回执与实测相符，除 IT-029（`model` 说成「留空」）与 IT-030（残留公司未申报）两处。

**状态值：`全部通过`**（2026-10-07 用户裁决两项均按建议）。按出口路由 → **F 审核**。

## 复核建议

1. **判定最靠边界的一项：IT-018。** 本步没有重跑 Insights 脚本（会再写演示站），只看了截图和库里无残留。若要实证，在测试站跑同一脚本（改 `--site`）即可，不碰演示站。
2. **与回执声称不一致处**：
   - SB 回执复核建议 3「bot 的 `model` 为空」→ 实为 `gpt-4o`（IT-029）。
   - R7 回执「TS-017 变异 → 14 例报错」→ 本步实测 15 例里 13 例报错（SL-011 七例＋SL-012 六例）、错误数 17（含子用例）。差一例，可能是测试执行顺序不同、连带失败的例数随之不同；结论（变异能被测出）一样，不另立项。
   - SB 回执「IT-018 留下 4 条 `Deleted Document`」→ 演示站 10-07 起共 8 条，多出的 4 条是 00:41 装 HRMS 时删的 `Employee` Property Setter，是 HRMS 安装自己的行为，在新基准点之前，不影响 SL-004 ⑥。
3. **拿不准处**：IT-029 若照方案字面把 `model` 写空，Raven 前端表单再次保存时会不会回填 `gpt-4o`，本步没验。
