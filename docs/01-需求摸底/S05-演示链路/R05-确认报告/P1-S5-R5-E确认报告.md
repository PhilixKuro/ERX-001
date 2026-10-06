# 确认报告（对象：P1-S5 D 步落地 / 清单：P1-S5-R3 开发方案）

**轮次**：P1-S5-R5｜**日期**：2026-10-06｜**步骤**：`plannedDev` E（confirm）｜**执行者**：Claude（Opus 5.5）
**清单**：[开发方案总纲](../R03-开发方案/P1-S5-R3-C开发方案-总纲.md)＋[Part1](../R03-开发方案/P1-S5-R3-C开发方案-Part1.md)／[Part2](../R03-开发方案/P1-S5-R3-C开发方案-Part2.md)／[Part3](../R03-开发方案/P1-S5-R3-C开发方案-Part3.md)／[Part4](../R03-开发方案/P1-S5-R3-C开发方案-Part4.md)
**待核声称**：[D回执-Part1](../R04-代码/P1-S5-R4-D回执-Part1.md)～[Part4](../R04-代码/P1-S5-R4-D回执-Part4.md)
**被核对物**：`frappe-bench/apps/frappe_china/`（HEAD `4af8672`）、主仓库 `docker/`（HEAD `6edc902`）；测试站 `test.localhost`、演示站 `erx.localhost`

## 覆盖自证（分片）

方案拆为总纲＋4 Part，按 `bricks/sharding.md` 分 4 片，每片一个独立只读 Session（不改文件、不写站点、不跑测试）。主会话跑全量回归、复现关键发现、做跨片比对。

| 片 | 范围 | 实际查了什么 | 跳过及原因 |
|---|---|---|---|
| 1 | Part1 TS-001～005 | 读 `setup.sh`／`lock-apps.sh`／`install.py`／`hr.py`／`company.py`／测试；四上游 `ls-remote` 核 commit；坏 tag 预检 rc；`bash -n`；`target_app_order` 喂 5 组输入；`lock-apps.sh` 写入模式在仓库外临时副本跑两次（已清）；七个 app 的 remote／HEAD | `run-tests`（主会话在跑）；`setup.sh` 端到端（写操作，属 TS-015）；SL-002 ① 现场核（测试站无中式公司、演示站无 HRMS） |
| 2 | Part2 TS-006～008 | 两站 `list-apps`／`get_installed_apps`／`site_config.json`；两站各跑一次 `check_app_order`；`get_hooks` 只读；tabVersion／Deleted Document／Module Def 时间线；备份目录；回归日志与 testing 日志 | 反证重做（写操作）；SL-003 ②⑤ 复测（公司已删、HRMS 已装，场景不可重现） |
| 3 | Part3 TS-009～012 | 读 `configure-apps.sh`、`queries.py`、`raven_dataset.py`（逐字符解码）、Raven 上游 `functions.py`／`raven_ai_function.py`；测试站 Singles（密钥只判空）、Raven Bot／AI Function、CRM 留痕、Property Setter、Insights 数据源；演示站 `_FCT` 与 DocType 存在性 | `configure-apps.sh` 实跑（会写站，幂等性只读码判）；给 bot 发消息；浏览器与截图（无 web 进程） |
| 4 | Part4 TS-013～016 | 读 `realtime_check.py`／`.js`／hooks／csv、compose、模板、`save-images.sh`、README；`nginx -T`；`compose ps`；`netstat`；curl 8000／9100／6787；演示站跑一次 `realtime_check.run(timeout=3)`；宿主跑预检两条与 `lock-apps.sh --show`；两仓 git diff 文件清单 | 起 `bench start`（会与回归抢资源），故静态资源 200、转发通路、本机 6787 未验 |
| 主 | 全量回归、复现、跨片比对 | `run-tests --app frappe_china`（日志 `frappe-bench/logs/s5-r5-regression.log`）；SQL 复核悬空行；复现 `raven_dataset.py` 乱码、`queries.py` 死函数、`company.py` 删行逻辑、`realtime_check.py` 偏离；读 `Report.get_data` 判 IT-014 权限风险 | — |

**跨片比对结论**：

- **四片在同一根因上汇合**：片 1、片 2 各自从代码与时间线查到测试站 10 行悬空 `Expense Claim Account`，片 4 从回归日志看到 80 个报错，主会话复现确认是同一条 `LinkValidationError`（IT-001／002）。
- **TS-007 未做是 Part3、Part4 大批未通过项的上游**：片 3 的 SL-005 ①、SL-006、SL-007 ①② 演示站部分，片 4 的 TS-016 ②③⑤，都因演示站未装 App 而无从成立（IT-005）。
- **`apps.json` 锁定滞后**由片 1、片 4 各自发现：按当前清单重建会丢 `realtime_check.py` 与 `ai/`，而 hooks 与 `configure-apps.sh` 已引用它们（IT-009）。
- **`ai/queries.py`**：片 4 发现它在退路未触发时已存在，片 3 查明原因是上游 `get_report_result` 无 whitelist、HT-007 原写法不成立（IT-014／015）。

---

## 逐项确认

结论：✅ 通过／❌ 未通过（附 IT 号）／❔ 无法判定／⏸ 未通过·已裁决延迟（编号）。

| # | 清单项 | 落地否 | 生效否 | 根因消除否 | 验收标准 | 验证方式 | 结论 |
|---|---|---|---|---|---|---|---|
| TS-001 | `apps.json` 加条目、改顺序 | ✅ | ✅ | ⚠ | SL-001 ① | 读文件；四上游 `ls-remote` 与锁定 commit 全符；README 两句在 | ❌ IT-008（README 对 tag 的说法）、IT-009（frappe_china 锁定滞后） |
| TS-002 | 归位函数 | ✅ | ✅ | ✅ | SL-001 ④⑦ | 六类用例在（`test_install.py:31-83`）；`target_app_order` 喂 5 组输入全对；两站顺序与 `site_config` 镜像一致（A5） | ✅ |
| TS-003 | `setup.sh` 四处改动 | ✅ | ❔ | ❔ | SL-001 ②③④⑤ | `bash -n`；预检命令单跑：坏 tag rc=2、`v3.14.2` rc=0；`[ ] \|\| [ ] && continue` 在 `set -e` 下实跑正确；官方 App remote 状态对，但 TS-006 是手工装的，分不清是否脚本所为；端到端未跑 | ❌ IT-007、IT-008；端到端 ❔（待 IT-025） |
| TS-004 | `lock-apps.sh` 保序保 tag | ✅ | ✅ | ✅ | SL-001 ⑥ | 临时副本写入模式两次：保序、保 tag、无 `branch: HEAD`、官方 url 不变、缺条目追加末尾并警告；`--show` 显示正确 | ✅ |
| TS-005 | 报销类型科目预配 | ✅ | ✅ | ❌ | SL-002 ①～⑧ | `hr.py`、两个入口、映射在；入口 2 有间接证据（悬空行是回填写的）；只有 ⑤⑥ 有 mock 测试；①②③④⑦⑧ 无测试；删公司路径留下悬空行并让此后建公司全部失败 | ❌ IT-001、IT-002、IT-003、IT-006 |
| TS-006 | 测试站接入与 S4 回归 | ✅ | ✅ | ❌ | SL-003 ①～⑥ | ① ③ ⑤ 实测通过；② 时间线佐证、不可复测；④ 本步全量 **126/173 跑到、errors=80、EXIT=1**；⑥ 公司已清但留 10 行悬空子表 | ❌ IT-001、IT-004 |
| TS-007 | 演示站接入四个 App | ❌ | — | — | SL-004 ①②③⑥ | 演示站 `installed_apps` 仍为 `frappe, erpnext, frappe_china`；无 `保留-S5装App前/`；登记册无对应条目；⑥ 业务数据为 0（现状成立） | ❌ IT-005 |
| TS-008 | 归位检查函数与验收 | ✅ | ✅ | ⚠ | SL-004 ④⑤ | 契约字段齐；测试站 `ok=true`（expected＝actual＝「计算方式」，competitors `{hrms: 公式}`）；演示站 `ok=false`（translation 无竞争者，依赖 TS-007）；反证有两条 tabVersion 调序记录，函数输出无留证；第三条单测测的是「全缺」不是「被盖」 | ❌ IT-005（演示站）、IT-010、IT-011、IT-012 |
| TS-009 | 应用配置脚本 | ⚠ | ⚠ | ❌ | SL-005 ①、SL-007 ①② | 无 `docker/scripts/configure_apps.py`，单个 shell 内嵌 python，只能容器内跑、不读 `.env`、无 `--site/--company`；二次运行仍无条件 save；测试站 `erpnext_company` 为空；Raven Settings 非密钥字段未写；bot 字段、15 条工具名与顺序、无写类函数 ✅；`run_report` 改指包装函数未申报；README 无「配置四个 App」 | ❌ IT-013、IT-014、IT-016 |
| TS-010 | CRM 实点与看板 | ⚠ | ❔ | ❔ | SL-005 ②～⑦ | 无截图、回执无关键值；留痕显示 Deal 金额 128、未推进两档、报价单公司为 `_Test Company`(India)、联系人空；SO 与客户无删除留痕；⑥ 无证据；⑦ 无残留 ✅；无 CRM Deal Property Setter（HT-005 成立，回执未记） | ❌ IT-017 |
| TS-011 | Insights 验收 | ⚠ | — | — | SL-006 ①～③ | 测试站已装；演示站未装；用 Insights 自带单测（查 `tabToDo`）替代演示站 `/insights` 与 `tabCompany` 查询，未申报 | ❌ IT-005、IT-018 |
| TS-012 | Raven 连通、报表通道、三问 | ⚠ | ❌ | — | SL-007 ③～⑦ | ③④⑥ 已裁决延迟；⑤ `raven_dataset.py` 中文常量乱码、只有问 1 的 7 条 Deal、无干扰项、无问 2／3、无 `QUESTIONS`，`test_raven_dataset.py` 不存在——不依赖 LLM，不在 SH-P1S5006 内；⑦ 两站无 `_FCT` 残留 ✅；`ai/queries.py` 退路未触发即实现且接口与契约不符 | ⏸（③④⑥，SH-P1S5006）；❌ IT-015、IT-019 |
| TS-013 | 连通检查、转发层、局域网实测 | ⚠ | ❔ | ❔ | SL-008 ①～⑥ | `realtime_check` 有多处偏离契约；`test_realtime_check.py` 不存在；compose 端口改动与 proxy 服务 ✅（宿主 9100 由 nginx 接管、6787 只绑本机）；compose 注释、README 端口节、`save-images.sh` 未同步；本机基线 ① 未做也未登记；③④ 已裁决延迟 | ⏸（③④，SH-P1S5007）；❌ IT-020、IT-021、IT-022、IT-024 |
| TS-014 | 组网就绪文档与延迟需求 | ⚠ | — | — | SL-009 ①～③ | SH-P1S5005 已登记 ✅；map 无具体 IP ✅；README 缺独立组网段、查地址命令、准备清单 ①命令与 ④、待验点「国内能否连」与 `extra_hosts` 备用做法 | ❌ IT-023 |
| TS-015 | 空目录重建演练 | ❌ | — | — | SL-010 ①～③ | 未做，登记册无编号；② 预检命令由本步补测通过；③ 一写入就会改 frappe_china 那条 | ❌ IT-025、IT-009 |
| TS-016 | 全量回归、新基准点、常驻文件回写 | ❌ | — | — | SL-010 ④⑤⑥ | ④ 全量失败（IT-004）；⑤ 演示站 `check_app_order` 为假、无 Raven、无 `保留-S5装App后/`；⑤ 业务计数 0 ✅、`20261004_005331` 在 ✅；方案外改动自查：两仓工作区干净、文件均能对上任务 ✅（`company.py` 的删行逻辑除外，见 IT-003）；⑥ `项目概况.md`／`开发守则.md` S5 期间零改动 | ❌ IT-004、IT-005、IT-026 |

**总纲完成标准（§一）**：1 ❌；2 ❌（IT-004）；3 ❌（IT-005、IT-026）；4 AC-001 ❔（IT-017）、AC-002 测试站 ✅／演示站 ❌、AC-003 ⏸、AC-004 局域网 ⏸＋本机部分 ❌（IT-024）、AC-005～008、AC-010 随上列各项未成立。

---

## 问题详情

三格取值见流程规范 §2.3。全部状态初始为 `待裁决`。

### 回归与数据（先做，其余多项依赖它）

**IT-001 测试站 10 行悬空 `Expense Claim Account`，全量回归 80 个报错**
- 现象：`tabExpense Claim Account` 有 10 行指向已删的公司 `FCT_TEMP`、`_FCT 入口二` 与已删的 `…-FCT2`／`…-FCT3` 科目。每次 `make_cn_company` 都在 `hr.py:52` 的 `doc.save` 处报 `LinkValidationError`（框架连带校验父单全部子行）。
- 定位：TS-006 第 8 步删公司时遗留（Deleted Document 2026-10-05 20:38）。方案假设「HRMS 的 `on_trash` 会顺带删其关联记录」不成立：`hrms/hooks.py:392-402` 的 `company_data_to_be_ignored` 不含这张子表。
- 建议：删除测试站 `company IN ('FCT_TEMP','_FCT 入口二')` 的 10 行，重跑全量回归。
- 建议档位：`本Session修`｜待裁决点：是否允许改测试站数据（只动测试站，可整站重建）｜状态：已修复（见当场修清单）

**IT-002 产品缺陷：删一次中式公司，此后全站建不出中式公司**
- 现象：IT-001 的成因不限于测试站。演示站装 HRMS 后，只要删一次公司就会重现。
- 定位：`frappe_china` 无 Company `on_trash` 清理；`hr.py:46-52` 用整单 `save` 追加子行。
- 建议：二选一或并用——(a) Company `on_trash` 时（DocType 存在才做）删该公司的 `Expense Claim Account` 行；(b) 追加子行不整单保存父单。并补一条测试：删公司后能再建中式公司。
- 建议档位：`出方案修`｜待裁决点：修法取 (a)／(b)／两者｜状态：待详细修复方案

**IT-003 `company.py` 有方案外删行逻辑，回执称「没有方案外代码偏离」**
- 现象：`on_update` 非建账分支在每次保存中式公司时调 `_remove_hrms_expense_claim_account`（`company.py:58-60`、`:81-94`）。命中时删该公司**全部** `Expense Claim Account` 行且不重配，按 `_("Expense Claims")` 查科目、依赖当前语言。
- 风险（读码推断，未实跑）：从现有公司复制建账、或 HRMS 再建出 `Expense Claims` 科目时，中式公司丢掉 5 条映射。
- 建议：至少在删行后重调 `set_cn_expense_claim_accounts`；科目判定不依赖语言。或回退该逻辑。
- 建议档位：`出方案修`｜待裁决点：保留并补方案，还是回退｜状态：待详细修复方案

**IT-004 全量回归不成立；回执「170/170」查不到结果行且已过时**
- 现象：本步跑 `run-tests --app frappe_china`：测试定义 173 条，跑到 126 条，`FAILED (errors=80)`，`EXIT=1`，原因全是 IT-001。「170/170、628.498 秒」在任何日志里都没有结果行；能对上时长的那次跑在清理与最后 3 条单测之前。回执未报跳过条数（违反总纲 §九第 5 条）。
- 建议：IT-001 修完重跑，报收集、通过、跳过各几条，并与 S4 的 160 条对比。
- 建议档位：`本Session修`（随 IT-001）｜待裁决点：—｜状态：已修复（IT-027／028 修完后全量 180/180，见当场修清单）

### 演示站与收尾

**IT-005 TS-007 演示站接入未执行，也没有去向**
- 现象：演示站仍是三个 app，无 `保留-S5装App前/`，HDTH 未验；登记册无条目。D 步报「代码已落地」，把这项站点操作盖住了。Part2 回执暂缓的理由是「测试站全量回归通过前不改演示站」，同一回执又写回归已过，两者矛盾。
- 牵连：完成标准 3；AC-002 演示站部分；SL-005 ①、SL-006、SL-007 ①② 的演示站部分；TS-016 ②③。
- 建议：IT-001/004 转绿后按 Part2 执行 TS-007（核 `005331` → 备份另存 → `up.sh` → 重启 → HDTH 验证），再在演示站跑 `configure-apps.sh` 与 `check_app_order`。
- 建议档位：`新Session修`（演示站写入，须先备份、用户在场）｜待裁决点：本 Stage 内做，还是登记延迟（会推迟 S6／S7 的输入）｜状态：待新Session修

**IT-025 TS-015 空目录重建演练未做，也未登记**
- 现象：Part4 回执写「延期需求」，登记册只到 SH-P1S5007，无对应编号。SL-010 ② 的预检本步已补测通过；①③ 未验。
- 建议：做（须先修 IT-009），或登记 `SH-P1S5008`，唤醒条件建议定在「换机器或 S7 环境准备时」。
- 建议档位：`新Session修`｜待裁决点：做还是登记延迟 → **用户裁决：延迟**｜状态：延迟（SH-P1S5008）

**IT-026 TS-016 新空账基准点与常驻文件回写未做**
- 现象：无 `docker/backups/保留-S5装App后/`。`docs/项目概况.md`、`docs/开发守则.md` 自 S5 起点无改动：项目概况仍写「hrms app 未安装」（:149）、演示站状态是 S4 的（:66）、端口仍是「两侧同号」（:79）；回执「新增约定」三条未进开发守则。
- 建议：在 IT-005 之后按 TS-016 第 3、5 步做（先载入常驻文件契约）。
- 建议档位：`新Session修`（依赖 IT-005）｜待裁决点：—｜状态：待新Session修

**IT-009 `apps.json` 里 frappe_china 锁定 `1193f94`，HEAD 是 `4af8672`**
- 现象：落后的 3 个提交都已推到 origin。`hooks.app_include_js`（`realtime_check.js`）与 `configure-apps.sh` 引用的 `frappe_china.ai.queries` 只在 HEAD 里有，按现清单重建会缺文件。
- 建议：跑 `docker/lock-apps.sh` 写入（只会改这一条 commit，片 1 已在副本验过）。提交另问。
- 建议档位：`本Session修`｜待裁决点：提交许可（改完停下来问）｜状态：已修复（见当场修清单）

### Part1 细节

**IT-006 SL-002 测试未按方案落地**
- 现象：`tests/test_expense_claim.py` 不存在；⑧ 静态检查未写进 `test_scaffold.py`。现有 `test_hr.py` 3 例只覆盖 ⑤（mock）、⑥。
- 建议：按 TS-005 第 5 条补 ①～⑦（HRMS 不在时 `skipTest`）与 ⑧。
- 建议档位：`新Session修`（要在测试站建公司，先等 IT-001／002）｜待裁决点：—｜状态：待新Session修

**IT-007 `setup.sh` 第 4 段：`apps/` 下未声明的目录不再设 `core.fileMode false`**
- 定位：`setup.sh:248-291` 改成只遍历 `apps.json`，方案 TS-003 第 3 条要求这类目录「照旧只设 fileMode」。
- 建议：第 4 段后补一个循环，覆盖未声明的 git 目录。
- 建议档位：`本Session修`｜待裁决点：—｜状态：已修复（见当场修清单）

**IT-008 tag 条目的日志与 README 说法**
- 现象：方案要求 tag 条目日志说「停在 tag $ref」，实为通用的「（ref $app_ref）」（`setup.sh:231`）。`docker/README.md:121`「不进 detached HEAD」对 tag 不成立（实测 insights 为 DETACHED）。
- 建议：两处按 branch／tag 分开写。
- 建议档位：`本Session修`｜待裁决点：—｜状态：已修复（见当场修清单）

### Part2 细节

**IT-010 TS-008 第三条单测与方案不符**
- 现象：方案要测「覆盖末项被别的 app 盖掉」，实现 patch `get_hooks` 返回 `{}`（全缺）。
- 建议：改为返回 `{k: ["frappe_china.x", "other_app.x"]}`，断言 `overrides_ok` 为假。
- 建议档位：`本Session修`｜待裁决点：—｜状态：已修复（见当场修清单）

**IT-011 `check_app_order` 的 problems 与契约有偏差**
- 现象：文案为英文，没有「探针失效：须换一个撞源词」；无中式公司时未注明；`_app_translations` 用 `except Exception: pass` 吞异常（判失败不会误判通过，但与「不静默」相悖）；expected 为空分支无测试。
- 建议：按契约改中文文案、补注明；吞异常改为把异常写进 problems。
- 建议档位：`本Session修`｜待裁决点：文案是否必须照方案原话｜状态：已修复（见当场修清单）

**IT-012 TS-008 反证结果未留证**
- 现象：只有两条 tabVersion 调序记录（`DefaultValue`／`installed_apps`）证明调过序。第 c、e 步的函数输出没贴进回执，清缓存与重启也无证据。
- 建议：IT-001 修完后在测试站按 a～e 重做一次，四次输出贴进本报告的当场修清单。
- 建议档位：`本Session修`（测试站、可逆，需重启 `bench start`）｜待裁决点：是否接受现有 Version 记录作旁证、不重做｜状态：已修复（见当场修清单）

### Part3 细节

**IT-013 `configure-apps.sh` 实现形态与行为偏离方案**
- 现象：无 `docker/scripts/configure_apps.py`，也没有三个函数；脚本只能在容器内跑，不载入 `.env`、无 MSYS 处理、无 `--site/--company`。二次运行无条件 `save`、reorder 并清缓存，没有「无改动」输出（`:42-51`、`:188-189`）。缺 DocType 时静默跳过（`:19` 等）。公司按 `country=China` 判，零家时静默、多家时不报错（`:65-71`），测试站 `erpnext_company` 因此为空。三个 `RAVEN_*` 不全时整段跳过 Raven Settings，方案是非密钥字段照写、缺密钥只告警。
- 建议：按 Part3 TS-009 拆成宿主入口＋容器内脚本，补齐上述行为。
- 建议档位：`新Session修`｜待裁决点：是否接受单文件形态（只补行为、补申报偏离）→ 用户「其余按建议」，即按方案拆分；**「`RAVEN_*` 不全时非密钥字段照写」一条按延迟读法并入 SH-P1S5006**，不在本项修｜状态：待新Session修（不含已并入 SH-P1S5006 的那条）

**IT-014 `run_report` 改指自写包装，未申报；参数描述缺失**
- 现象：`run_report` 指向 `frappe_china.ai.queries.run_report`，不是方案的 `raven.ai.functions.get_report_result`。理由成立：上游函数无 `@frappe.whitelist`，而 `Raven AI Function.validate` 要求被指向函数已 whitelist，HT-007 原写法存不进去。但回执未申报；`params` 只有 type，没列 6 个报表名与过滤键；15 条工具描述是英文，`list_crm_deals` 写「submitted」，可 CRM Deal 不可提交。
- 权限：包装函数 whitelist 后，登录用户能经 `/api/method` 直接调。Query／Script 报表走 `_run`、会校验 `ref_doctype`；Report Builder 类走 `run_standard_report`，是否校验未读到（见复核建议 3）。
- 建议：追认偏离并写进方案更正；`params` 补描述；工具描述改中文。
- 建议档位：`新Session修`｜待裁决点：是否认可改指自写包装（它扩大了 `frappe_china` 的 whitelisted 接口面）｜状态：待新Session修

**IT-015 `ai/queries.py` 退路未触发就实现，4 个函数是死代码**
- 现象：`list_crm_deals`／`list_purchase_receipts`／`list_sales_orders`／`list_boms` 没挂到 bot，函数名与契约（`top_weighted_deals` 等）也不同，无单测。
- 建议：删掉这 4 个，只留 `run_report`（若 IT-014 获认可）。
- 建议档位：`本Session修`｜待裁决点：依 IT-014 的裁决｜状态：延迟（SH-P1S5006，用户裁决按延迟读法）

**IT-016 `docker/README.md` 缺「配置四个 App」一节**
- 建议：补一节：何时跑、`.env` 要填哪三个值、可重复跑。
- 建议档位：`本Session修`｜待裁决点：—｜状态：已修复（见当场修清单）

**IT-017 TS-010 证据不足，链路未按方案实点**
- 现象：无截图，回执无关键值。留痕显示：Deal 金额 128（方案 100000）；状态仍为 Qualification，没推进两档；报价单公司是 `_Test Company`(India)，联系人为空；SO 与客户无删除留痕，「自动建客户」从站上证实不了；⑥ 异常路径无证据；HT-005 成立却未记。
- 建议：测试站先有中式公司（IT-001／002、IT-013 之后），按 TS-010 第 1～8 步重做，截图存 `Spike/P1-S5-R4-TS010-*.png`。
- 建议档位：`新Session修`｜待裁决点：是否接受脚本化验证代替 `/crm` 界面实点（方案字面要界面加截图）｜状态：待新Session修

**IT-018 TS-011 用单测替代演示站验收，未申报**
- 现象：方案要求在演示站打开 `/insights`、对 `Site DB` 查 `tabCompany` 行数为 1。实做是测试站的 Insights 自带单测。
- 建议：随 IT-005 按 TS-011 第 2～3 步做。
- 建议档位：`新Session修`（随 IT-005）｜待裁决点：是否接受单测替代｜状态：待新Session修

**IT-019 三问数据集不可用，判别性测试缺失**
- 现象：`tests/raven_dataset.py` 的中文常量是 GBK 误读后再存成 UTF-8 的乱码，`Expected` 与 `build` 两边乱法还不同（如 `閸熷棙婧€` 对 `鍟嗘満`）。数据只有问 1 的 7 条 Deal，没有 08／09 干扰项，问 2／问 3 全无；无 `QUESTIONS`、不建公司。`CRM Deal` 走 naming_series，name 不会等于 `_FCT 商机 xx`，也没有 `deal_name` 字段；`organization` 填了 Company 名。`expected()` 是写死的元组，不是从常量算。`teardown` 按前缀强删全部 `_FCT` 记录，有误删同前缀测试数据的风险。`tests/test_raven_dataset.py` 不存在。这些都不依赖 LLM，SH-P1S5006 不覆盖。
- 建议：按 Part3 接口契约 §2 与 TS-012 第 1 步重写，用 Write 写入（避开 heredoc 的 GBK 坑），补五条判别性断言与 build→verify 事务测试。
- 建议档位：`新Session修`｜待裁决点：—｜状态：延迟（SH-P1S5006，用户裁决按延迟读法）

### Part4 细节

**IT-020 `realtime_check.run()` 偏离契约**
- 现象：默认 `timeout=5.0`（契约 30）并卡上限 30；缓存过期固定 30 秒（契约 `timeout+60`，`timeout=30` 时 pending 键与截止同时到期）；轮询 0.1 秒（契约 0.5）；超时 reason 改成英文，丢了「或目标用户没有打开的桌面页」；`run` 多了 `@frappe.whitelist()`。`ack` 写回的过期时间也是固定 30 秒。
- 建议：按契约改回；`run` 去掉 whitelist。
- 建议档位：`本Session修`｜待裁决点：30 秒上限与 whitelist 是改回，还是追认为方案更正｜状态：已修复（见当场修清单）

**IT-021 `tests/test_realtime_check.py` 不存在**
- 建议：按 TS-013 第 1 步写五例：不存在的 token、别的用户、正确用户置 acked、另一线程 ack 时 ok、不 ack 时 `timeout=1` 为假。
- 建议档位：`本Session修`｜待裁决点：—｜状态：已修复（见当场修清单）

**IT-022 转发层的配套改动未同步**
- 现象：`docker/compose.yaml:50-54` 注释仍是「两侧同号直通」；`docker/README.md` 端口表（:146-150）没标 6787 只绑本机，:178-191 仍教人改 frappe 服务的 9100 映射（已失效）；`docker/save-images.sh:12` 的 `IMAGES` 没加 `nginx:1.30.5-alpine`。
- 建议：按 TS-013 第 4 步补齐三处。
- 建议档位：`本Session修`｜待裁决点：—｜状态：已修复（见当场修清单）

**IT-023 README「异地终端访问」一节不全**
- 现象：缺独立的组网段（两端装客户端、加入同一网络、用组网地址访问、规则同样生效）；局域网段缺查本机地址的命令；准备清单只有三条，① 没给 `set-admin-password` 命令，④ 并进了 ③；已知待验点缺「国内能否稳定连上」与 `extra_hosts: host-gateway` 备用做法。
- 建议：按 TS-014 第 1 条四段补齐。
- 建议档位：`本Session修`｜待裁决点：—｜状态：已修复（见当场修清单）

**IT-024 本机能做的连通验收没做，延迟登记的范围不清**
- 现象：SL-008 ①（本机基线、转发层上线前后各一次）不依赖外部设备，没做也没登记。② LG-007「上线前」对照：proxy 已上线，原现场没了。SH-P1S5007 字面没写明包含 LG-007／HT-008。本步只看到宿主 9100 由 nginx 接管，上游未起，返回 502，转发通路未证。
- 建议：起 `bench start`，用本机浏览器（或宿主无头 Chrome）开桌面页跑 `run()`，原样贴证据。SH-P1S5007 的描述补上「LG-007 上线前对照（须临时停 proxy、恢复直通映射）与 HT-008」。
- 建议档位：`新Session修`｜待裁决点：上线前对照缺失是否接受 → **用户裁决：按延迟读法**，LG-007 上线前对照与 HT-008 并入 SH-P1S5007（登记册已补）；本机基线（SL-008 ①）仍待新 Session 做｜状态：部分延迟（SH-P1S5007）；本机基线 待新Session修


### 修复后回归新暴露的问题

**IT-027 测试站 `rounding_method` 被 HRMS 的测试前置改成 Banker's Rounding，S4 的一条端到端断言失败**
- 现象：修完 IT-001 后全量回归 180 条，`test_e2e_minimal.test_sales_purchase_and_return_tax_postings` 第 67 行断言红字发票税额为 -0.07，实得 -0.06（0.50×13% = 0.065，商业圆整得 0.07，银行家舍入得 0.06）。
- 定位：S4 DEC-116 规定站点用 `Commercial Rounding`，由建站脚本设。测试站现为 `Banker's Rounding`，时区为 `Asia/Kolkata`，另有 `_Test Company`（India，10-06 09:45 建）。这些都来自 `hrms/tests/test_utils.py:9-37` 的 `before_tests`：站上没有公司时，它调 `setup_complete` 建 India 测试公司，`setup_wizard.py:295` 同时把 `rounding_method` 写成 Banker's Rounding。S5 装 HRMS 前测试站没有这个钩子；TS-006 第 8 步删掉最后一家公司后，下一次跑测试就触发了它。**这是 S5 接入 HRMS 引入的回归，不是 S4 代码的问题。**
- 建议：(a) 测试站把 `rounding_method` 改回 `Commercial Rounding`（站上已有公司，HRMS 的钩子不会再触发）；(b) 另在 `FrappeChinaTestCase.setUpClass` 里把 `rounding_method` 显式设成 DEC-116 的值，随测试事务回滚，不再依赖站点状态。
- 建议档位：`本Session修`（两处都改动局部，可当场跑全量验证）｜待裁决点：只做 (a)，还是 (a)＋(b) → **用户裁决：(a)＋(b)**｜状态：已修复（见当场修清单）

**IT-028 容器重建后中文字体与 `pdftotext` 丢失，3 条 PDF 测试报错（环境问题，已当场恢复）**
- 现象：`test_statement_export.test_pdf_text_fonts_and_orientation` 三个子用例报 `FileNotFoundError: 'pdftotext'`。容器内 `fc-list :lang=zh` 为 0。
- 定位：字体与 `poppler-utils` 由 `setup.sh` 第 6.5 段装进容器，容器重建即丢。frappe 容器创建于 2026-10-06 14:17（UTC 06:17），与 D 步改 compose（转发层）同时；改完只 `docker compose up -d` 重建了容器、没跑 `up.sh`，故第 6.5 段没补装。方案 TS-013 第 4 步原写的是跑 `up.sh`。
- 处理：本步在容器内按第 6.5 段的同一命令补装（环境恢复，可随容器重建撤销；**未先问用户，在此说明**），三条测试复跑全过。
- 建议：README「端口」节已写明改端口后用 `docker compose up -d`；该处补一句「重建容器后须重跑 `docker/up.sh` 补装字体」。
- 建议档位：`本Session修`｜待裁决点：—｜状态：已修复（环境已恢复；README 已补句）

## 当场修清单

| # | 对应未通过项 | 改动位置（文件:行） | 用户确认于 |
|---|---|---|---|
| 1 | IT-001 | 测试站 `tabExpense Claim Account` 删 10 行（公司 `FCT_TEMP`、`_FCT 入口二`），现为 0 行 | 2026-10-06「其余按建议修复」 |
| 2 | IT-007 | `docker/scripts/setup.sh` 第 4 段后新增循环，未声明目录设 `core.fileMode false` | 同上 |
| 3 | IT-008 | `docker/scripts/setup.sh` 对齐日志按分支／tag／游离三种分别报；`docker/README.md:121` 改写 detached HEAD 一句 | 同上 |
| 4 | IT-009 | `docker/apps.json` frappe_china `1193f94` → `65f3b78`（本步修复提交后由 `lock-apps.sh` 写入，diff 仅此一行） | 同上；提交与推送经用户许可（2026-10-06） |
| 5 | IT-010 | `frappe_china/tests/test_install.py`：覆盖被别的 app 盖掉、探针无竞争者、探针源词缺失三条 | 同上 |
| 6 | IT-011 | `frappe_china/install.py`：`_app_translations` 收集读错误、problems 改中文并含「探针失效：须换一个撞源词」「无中式公司」注明 | 同上 |
| 7 | IT-012 | 测试站重做反证 a～e，输出见下 | 同上 |
| 8 | IT-016、IT-022、IT-023 | `docker/README.md`「端口」节重写（含异地终端访问四段、准备清单 ①～④、已知待验点、改端口三处）＋新增「配置四个 App」节；`docker/compose.yaml` 注释；`docker/save-images.sh:12` 加 `nginx:1.30.5-alpine` | 同上 |
| 9 | IT-020 | `frappe_china/realtime_check.py`：默认 30 秒、缓存 `timeout+60`、0.5 秒轮询、reason 用契约原文、`run` 去掉 whitelist、`ack` 沿用 pending 的过期时间 | 同上 |
| 10 | IT-021 | 新增 `frappe_china/tests/test_realtime_check.py`（5 例） | 同上 |
| 11 | IT-019（延迟） | `frappe_china/tests/raven_dataset.py` 文件头注明不可用、待 SH-P1S5006 重写 | 2026-10-06「按另一种读法」 |
| 12 | IT-025（延迟） | Stage 概况登记 SH-P1S5008；SH-P1S5007 描述补 LG-007／HT-008 | 2026-10-06「TS-015 划为延迟」 |
| 13 | IT-027 | 测试站 `rounding_method` 改回 `Commercial Rounding`；`frappe_china/tests/utils.py` 的 `FrappeChinaTestCase.setUpClass` 调 `_use_cn_rounding()` 设 DEC-116 的值（随事务回滚）。反向验证：站点临时改为 Banker's Rounding 后 `test_e2e_minimal` 仍过，随后恢复 | 2026-10-06「做 (a)＋(b)」 |
| 14 | IT-028 | 容器内补装 `fonts-noto-cjk`、`poppler-utils`（同 `setup.sh` 第 6.5 段）；`docker/README.md` 改端口那段补「重建容器后必跑 `docker/up.sh`」 | 环境恢复事后报告；README 随「其余按建议」 |

**定向测试**：`test_install` 16/16、`test_realtime_check` 5/5、`test_hr` 3/3、`test_statement_export` 3/3（IT-028 恢复后）。`bash -n` 两个改过的脚本通过。

**IT-012 反证输出**（测试站，2026-10-06）：

| 步 | 动作 | `ok` | `order_ok` | `translation_ok` | `actual` |
|---|---|---|---|---|---|
| 0 | 当前 | true | true | true | 计算方式 |
| a～c | 调成 `… crm, frappe_china, hrms …`，清缓存 | **false** | **false** | **false** | **公式** |
| d～e | `reorder_installed_apps`（`changed: true`），清缓存 | true | true | true | 计算方式 |

c 步 problems 为「装载顺序不对……」与「撞源词译名未由 frappe_china 胜出：「Formula」实际 '公式'，期望 '计算方式'」。e 后 `site_config.json` 的 `installed_apps` 已同步为目标顺序。本次用 `bench execute`（每次新进程），未重启 `bench start`（当时未运行）。

**修复后全量回归**（`logs/s5-r5-regression-2.log`）：180 条，通过 176，失败 1（IT-027），报错 3（IT-028，已恢复并复跑通过）。

**IT-027／028 修完后全量回归**（`logs/s5-r5-regression-3.log`，2026-10-06）：**180 条全过，跳过 0，`EXIT=0`**，耗时 11 分 19 秒。对比 S4 基线 160 条：只增不减 ✅。

## 全量回归 + 未执行项

**回归**：`bench --site test.localhost run-tests --app frappe_china`，2026-10-06 本步实跑。

| 项 | 值 |
|---|---|
| 测试定义 | 173（片 2 统计） |
| 实际跑到 | 126 |
| 结果 | `FAILED (errors=80)`，`EXIT=1`，耗时 9 分 34 秒 |
| 报错 | 80 条同一 `LinkValidationError`（IT-001），全部发生在 `make_cn_company` 的 setUp／setUpClass |
| 对比 S4 基线 160 条全过 | **不满足「只增不减」** |

**未执行项反向确认**：

- 演示站在 S5 期间未被写：`installed_apps` 与 DefaultValue 仍为三个 app；tabVersion、Error Log、Account 最新一条都在 10-01；`site_config.json` 的 mtime 是 10-04；无 Expense Claim／Raven／Insights 表；没有三问数据，没有 `_FCT` 记录 ✅
- 上游源码未改：frappe、erpnext、crm、hrms、insights、raven 的 `git status --short` 全空 ✅
- LiteLLM 相关未被意外改动：`docker/.env` 未设三个 `RAVEN_*`；测试站 Raven Settings 仍为缺省（`enable_ai_integration=0`），密钥字段空 ✅
- 外网相关：compose 与模板里没有组网地址，没有外网实测痕迹 ✅

## 总体结论

**存在未通过项**，共 26 项（IT-001～026），另有 SL-007 ③④⑥、SL-008 ③④ 已裁决延迟（SH-P1S5006／007）。

**裁决后去向**（2026-10-06 用户逐项裁决；修复回归中新增 IT-027／028）：

| 去向 | 项 |
|---|---|
| 已修复（本 Session） | IT-001、004、007、008、009、010、011、012、016、020、021、022、023、027、028 |
| `新Session修` → SB | IT-005、006、013（不含并入 SH-P1S5006 的一条）、014、017、018、024（本机基线部分）、026 |
| `出方案修` → C | IT-002、003 |
| 延迟 | IT-015、019 → SH-P1S5006；IT-025 → SH-P1S5008；IT-024 的 LG-007 上线前对照 → SH-P1S5007 |

修复后全量回归 180/180。本步状态值仍为 `有未通过项`：SB 与 C 的项未做完。

D 步的「代码已落地」与实情不符。Part2 的 TS-007、Part4 的 TS-015 与 TS-016 没做也没有去向；全量回归因 TS-006 遗留的数据失败；Part3 的配置脚本与三问数据集偏离方案或不可用。

建议的处置顺序：IT-001→004（回归转绿）→ `出方案修` 的 IT-002／003 → 其余 `本Session修` → `新Session修` 交 SB → 演示站接入（IT-005）及其下游。

## 复核建议

1. **最该先看：IT-001／002 的因果链。** 查法：`bench --site test.localhost mariadb -e "select parent, company, default_account from \`tabExpense Claim Account\`"`，可见 10 行指向不存在的公司；再看 `frappe-bench/logs/s5-r5-regression.log` 第 179 行起的 traceback，落在 `hr.py:52`。这一处代价最大：它不只是测试站脏数据，演示站装 HRMS 后删一次公司就会重现。
2. **与 D 回执声称不一致处**（逐条，均已记为未通过项）：
   - Part2「全量回归 170/170 通过」→ 实测 126/173 跑到、80 errors（IT-004）。
   - Part2 英文段「pre-existing invalid links」→ 是 TS-006 自己造成的；正文也没提多建了一家 `FCT_TEMP`（IT-001）。
   - Part1「方案未偏离」→ IT-003／006／007／008。
   - Part3「configure-apps.sh 幂等」「CRM 链路、自动建客户和预测看板已验证」→ IT-013、IT-017。
   - Part4 TS-016「完成（按现有结果收口）」→ ①②③⑤ 均未达成（IT-026）。
   - Part4 TS-015「延期需求」→ 登记册无编号（IT-025）。
3. **拿不准处**：
   - IT-014 的权限判断只读了 `Report.get_data`。Query／Script 报表经 `_run` 校验 `ref_doctype`；Report Builder 类报表走 `run_standard_report`，是否校验没读到，也没实跑。查法：用一个非 System Manager 用户 POST `/api/method/frappe_china.ai.queries.run_report`，传一张该用户无权的 Report Builder 报表。
   - IT-003 的风险是读码推断，未实跑。
   - TS-010 那张 SO 与客户：`SAL-ORD-2026-` 计数器为 1 却没有删除留痕，可能建在回滚的事务里，判 ❔。
4. **验收条件本身可疑**：SL-001 ②「预检对不存在的分支或 tag 报错退出」只在目录不存在时才走预检（`setup.sh:165` 在 else 分支）。按「已存在目录按 commit 对齐、无须查 ref」读算通过，按字面读不算。本步取前者。
5. **版本管理**：D 步的提交 `99de639`～`6edc902` 与 frappe_china 的 `1193f94`～`4af8672` 都已提交并推送；总纲 §九第 7 条要求「只写不提交、须用户许可」。本步无从核实当时是否取得了许可，请用户自己确认。
