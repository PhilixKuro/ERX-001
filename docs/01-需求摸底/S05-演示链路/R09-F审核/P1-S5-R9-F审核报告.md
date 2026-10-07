# 审核报告（对象：P1-S5 代码落地 `frappe_china` ＋ `docker/` ＋ 两站配置 / 审核标准：B 需求文档 ＋ R3 开发方案 ＋ R6 开发方案 ＋ 业务规则）

**轮次**：P1-S5-R9｜**日期**：2026-10-07｜**步骤**：`plannedDev` F（audit），收口报告｜**执行者**：Claude（Opus 5.5）｜`打tag=否`
**Spec**：[F-codeAudit-plannedDev-audit.md](../../../流程体系/workflows/plannedDev/F-codeAudit-plannedDev-audit.md)＋`bricks/audit.md`＋`bricks/sharding.md`
**意图层**：[B 需求文档](../R02-需求文档/P1-S5-R2-B需求文档.md) v1.0｜**要求层**：[R3 开发方案总纲](../R03-开发方案/P1-S5-R3-C开发方案-总纲.md)＋Part1～4；[R6 开发方案](../R06-开发方案/P1-S5-R6-C开发方案.md)｜**合规基线**：[业务规则](../../../业务规则.md) v1（七条均未经专家确认）
**被审对象**：`frappe-bench/apps/frappe_china/` HEAD `4b21aae`（＝`docker/apps.json` 锁定值），S5 改动面 `03fde72..4b21aae`（19 文件，+1293／-8）；主仓库 `docker/` `c372a94..2fb2641`（10 文件，+696／-93）；站点 `test.localhost`、`erx.localhost`
**分片报告**：[Part1](P1-S5-R9-F审核报告-Part1.md)／[Part2](P1-S5-R9-F审核报告-Part2.md)／[Part3](P1-S5-R9-F审核报告-Part3.md)／[Part4](P1-S5-R9-F审核报告-Part4.md)／[Part5](P1-S5-R9-F审核报告-Part5.md)——逐项核查表、证据与盲区自述全文在各片，本报告只做汇总、跨片合并、主会话实跑与定稿

**Round 归属**：R8 E 复核 `全部通过` → 出口路由 → F。F 是主链步骤，新开一个 Round，记为 R9。

**暂缓项的处理口径**：外部设备实测（`SH-P1S5005` 外网、`SH-P1S5007` 局域网另一台设备）、LiteLLM 与三问（`SH-P1S5006`）、空目录重建演练（`SH-P1S5008`）都已裁决延迟，**本报告不把「没测」「没接」当发现**。只在两种情形下报：一是延迟之后留下的代码或文档与实情不符，会误导唤醒者；二是暂缓区以外、现在就存在的问题。暂缓区里查出的项一律建议「代码不动、补登记描述」。

## 覆盖自证（分片）

依据拆成了 R3 方案的总纲＋Part1～4，再加 R6 方案（单文件），所以按依据自身的边界分 5 片。每片一个独立的只读子 Agent：不改代码，不跑测试，站点只做只读查询。主会话负责验证门、变异、对高级与中级发现的复现，以及跨片合并。

| 片 | 范围 | 实际查了 | 跳过及原因 |
|---|---|---|---|
| 1 | R3 Part1（SL-001～002，TS-001～005） | `apps.json`、`setup.sh`、`lock-apps.sh` 全文；`install.py`、`hr.py` 中 SL-002 部分；4 份相关测试；在临时副本里复现 `lock-apps.sh` 追加行为 | 没跑测试，没跑 Ruff（容器里没装） |
| 2 | R3 Part2（SL-003～004，TS-006～008） | 两站 `installed_apps`（库、`site_config`、`tabInstalled Application` 三处）；HDTH 科目与报销行；22 类业务／测试痕迹计数；备份逐行比对；HRMS `EmployeePaymentEntry` 对 S4 路径的读码对照；两站钩子实际顺序 | 没做撞源词反证（会写站）；进程层缓存只读了码 |
| 3 | R3 Part3（SL-005～007，TS-009～012） | `configure_apps.py` 全文；两站 Raven／CRM 记录；上游 raven `sdk_tools.py`、`ai.py`、`agents_integration.py`；6 张报表按描述传参实跑 | 没给 bot 发消息（LiteLLM 未接，`SH-P1S5006`）；没跑 `configure-apps.sh`（会写站） |
| 4 | R3 Part4（SL-008～010，TS-013～016） | `compose.yaml`、转发层模板与容器内渲染结果；`realtime_check.py`／`.js` 与测试；上游 `realtime/` 三个文件；在容器内做协议层握手 | 没跑 `run()`、没停 proxy、没开终端（`SH-P1S5007`）。**首跑因 API 内容安全拦截失败、未留产物**，改用 Agent 工具重跑，要求不变 |
| 5 | R6 方案（SL-011～012，TS-017～020） | `company.py`、`hr.py` 全文；`company_defaults.json`；生命周期测试；上游 erpnext 删公司与复制建账路径、hrms 公司覆盖；全库 194 张带 `company` 列的表做悬空泛查 | 没跑测试，没亲自复现 R7／R8 的变异 |
| 主 | 验证门、变异、复现、合并 | 全量回归；2 组变异；复现 FD-001、FD-003、FD-004、FD-002、FD-013、FD-015 | 浏览器实点；外部设备；LiteLLM |

**一句话边界**：本轮查的是「S5 整体（R4 D＋R5 当场修＋SB＋R7 D）对照需求与两份方案是否落地、有没有拼不上的地方」。**没有**浏览器实点、外部设备、LiteLLM，也没有会计专家。

**审核自身留下的痕迹**（须用户裁决处置，见问题清单末节）：
- 片 3 的报表探针在测试站留下 2 条 `Error Log`（`ruekosvjr2` 10:56、`tiadsd1l5c` 10:59，分别是 Purchase Analytics、BOM Stock Analysis 执行失败）。`tabError Log` 是 MyISAM，rollback 撤不掉。
- 主会话的两组变异改过 `install.py`、`hr.py`，每次跑完都从备份还原，现在 `git status` 是空的。片 4 报告提到「审核期间工作区出现过改动」，指的就是这两组变异。

## 验证门实跑结果

| 门 | 声称值 | 实测值 | 与基线对比 | 一致否 |
|---|---|---|---|---|
| `bench --site test.localhost run-tests --app frappe_china` | 205/205（R8 E） | **Ran 205 tests in 942.777s, OK**，`EXIT=0`，跳过 0（日志 `frappe-bench/logs/s5-r9-full.log`） | S4 160 → R5 180 → R7 196 → 205，只增不减 | ✅ |
| Lint 真缺陷（Ruff 0.14.10 `--select F,E9 --ignore F401`，临时取用） | 未声称（S5 各轮都没跑） | S5 改动面 15 个 Python 文件：**1 条 F402**——`accounting/company.py:39` 循环变量 `_` 遮蔽了第 7 行导入的翻译函数 `_`（见 FD-036）；`docker/scripts/configure_apps.py`：通过 | S4 R17 为 0 | ⚠ FD-036 |
| Lint 全规则（`pyproject.toml` 口径） | — | 同一改动面 188 条：RUF001～003 全角标点 176、I001 8、W292 2、B905 1、F402 1；`format --check` 9 个文件会被重排 | 全量基线未清，属 `PH-P1019` | ⚠ 同 `PH-P1019` |
| JS 语法（`node --check realtime_check.js`） | — | 通过（片 4） | — | ✅ |
| 类型检查 | 工具链索引写「待确立」 | 不适用 | — | — |
| 前端构建 | — | 本 Stage 只加了一个不经构建的普通 js（HT-010），不涉及 `bench build` | — | — |

**变异**（主会话做，跑完从备份还原，`git status` 空）：

| 组 | 改动 | 预期 | 实测 | 结论 |
|---|---|---|---|---|
| M1 | `install.py` `reorder_installed_apps` 删掉 `changed=True` 分支里的调序、镜像同步、清缓存三行 | 有测试失败 | `test_install` **16/16 OK**（日志 `s5-r9-mut-m1.log`） | 该分支没有测试守着，坐实 FD-007 |
| M2 | `hr.py` `clear_company_expense_claim_accounts` 删掉 DocType 守卫 | SL-011 ⑤① 失败 | `test_company_hr_lifecycle` **15/15 OK**（212.963s，日志 `s5-r9-mut-m2.log`） | 守卫没有判别力，坐实 FD-007 |

## 逐项落地核查（汇总；逐条见各分片）

| 依据 | 任务 | 落地 | 生效 | 偏差／对应发现 | 查于 |
|---|---|---|---|---|---|
| R3 Part1 | TS-001 `apps.json` 七条、按装序、`official`／`tag` | ✅ | ✅ | `apps.json` 与 `install.py:5` 两处各存一份顺序，没有一致性检查（FD-035） | 片 1 |
| R3 Part1 | TS-002 归位函数 | ✅ | ⚠ | 判据只看四个业务 app（FD-006）；运行中进程靠重启（FD-005）；`changed` 分支没有测试（FD-007）；`Installed Applications` 子表未同步（FD-012） | 片 1／2 |
| R3 Part1 | TS-003 `setup.sh` 认 tag、按序装、归位、只配 upstream | ✅ | ⚠ | **不写 `socketio_port`**（FD-001）；预检只在首次克隆时跑（FD-023） | 片 1／4 |
| R3 Part1 | TS-004 `lock-apps.sh` 不改顺序与 tag | ✅ | ⚠ | 追加新 app 不写 `official`（FD-010）；保留 tag 时不核 HEAD（FD-011） | 片 1 |
| R3 Part1 | TS-005 报销科目预配（入口 1／2） | ✅ | ⚠ | 入口 2 回填漏掉复制建账的公司（FD-008） | 片 1／5 |
| R3 Part2 | TS-006 测试站接入与 S4 回归 | ✅ | ✅ | RS-002：S4 路径无语义变化；员工付款新路径没覆盖（FD-021） | 片 2 |
| R3 Part2 | TS-007 演示站接入 | ✅ | ✅ | AC-006 的 `en` 保存被收窄，但没列进偏离表（FD-026）；HRMS 改了 Employee 命名方式，回执没写（FD-025） | 片 2 |
| R3 Part2 | TS-008 归位验收（顺序、覆盖、译名、反证） | ✅ | ⚠ | `overrides_ok` 在没有竞争注册者时恒真；反证没重启进程（FD-005） | 片 2 |
| R3 Part3 | TS-009 `configure-apps.sh` | ✅ | ⚠ | 示例 `--company HDTH` 跑不通（FD-015）；夹带一个字段未申报（FD-016）；DDL 隐式提交（FD-017）；`.env.example` 注释（FD-029） | 片 3 |
| R3 Part3 | TS-010 CRM 链路与看板 | ✅ | ✅ | — | 片 3 |
| R3 Part3 | TS-011 Raven 连接与工具 | ✅（连接 ⏸ `SH-P1S5006`） | ⚠ | **报表工具对 bot 不可达，实际 14 条**（FD-004）；`debug_mode=1` 没交给 S7（FD-002） | 片 3 |
| R3 Part3 | TS-012 三问实测 | ⏸ `SH-P1S5006` | — | 登记描述不全（FD-004）；`raven_dataset` 风险描述有误（FD-028） | 片 3 |
| R3 Part3 | SL-006 Insights | ✅ | ✅ | — | 片 3 |
| R3 Part4 | TS-013 局域网连通 | ✅（终端实测 ⏸ `SH-P1S5007`） | ⚠ | 检查工具分不清「终端收到」和「本机页面收到」（FD-003）；端口文档三处不符（FD-018） | 片 4 |
| R3 Part4 | TS-014 组网就绪 | ✅ | ⚠ | 准备清单探测端口不全（FD-019） | 片 4 |
| R3 Part4 | TS-015 重建演练 | ⏸ `SH-P1S5008` | — | 演练判据没包含 `socketio_port`（FD-001） | 片 4 |
| R3 Part4 | TS-016 全量回归与收尾 | ✅ | ✅ | 项目概况「三处同号 9100」只在本机成立（FD-001）；SH-P1S5007 描述不全（FD-020） | 片 4 |
| R6 | TS-017 删公司清理 | ✅ | ✅ | 守卫查的 DocType 与另两处不一致、测试无判别力（FD-007）；测试站留 26 条悬空 `Tax Rule`（FD-013） | 片 5 |
| R6 | TS-018 保存前预配与兜底 | ✅ | ✅ | 依赖会话语言（FD-033） | 片 5 |
| R6 | TS-019 复制建账改挂 | ✅ | ⚠ | 会悄悄删掉用户手建的无号科目（FD-009） | 片 5 |
| R6 | TS-020 全量回归与收尾 | ✅ | ✅ | 残留核对只查了报销行（FD-013） | 片 5 |

## 跨片一致性（收口比对）

| # | 比对点 | 涉及片 | 结果 |
|---|---|---|---|
| 1 | 「中式公司」的判法 | 1／2／5 | **对不上**：回填与 `check_all_cn_companies` 按 `chart_of_accounts` 筛，R6 的 `is_cn_company` 沿复制链判。合并为 FD-008 |
| 2 | 归位后进程缓存 | 1／2 | 两片各自报了同一处：不调 `erase_persistent_caches`。合并为 FD-005 |
| 3 | `socketio_port` 由谁写 | 1／4 | **没有人写**：片 1 的 `setup.sh` 第 2 段只写 db／redis，片 4 依赖 9100。主会话复核：`setup.sh:103-106` 没有这一项，现值是 P1-S2-R1 手工写进 `common_site_config.json` 的，frappe `node_utils.js:20` 缺省 9000。定为 FD-001 |
| 4 | `apps.json` 的读取方 | 1／3 | 片 1 请片 3 确认 `configure_apps.py` 是否读它。主会话 grep：只有 `setup.sh`、`lock-apps.sh` 读，一致 |
| 5 | 业务 app 顺序存两处 | 1／2 | `apps.json` 条目顺序与 `BUSINESS_APP_ORDER` 目前一致，但没有检查保证。FD-035 |
| 6 | `_FCT CRM 验证` 夹具 | 1／2／3 | 三片都看到了。R8 IT-030 已裁「保留」；片 3 指出 IT-030 写的风险（teardown 会删它）与代码不符，真正的风险是 `force=True` 删 `_FCT` 前缀的物料等。FD-028 |
| 7 | Company 钩子实际顺序 | 2／5 | 两片实测一致：`validate`／`on_update`／`on_trash` 都是 hrms 在前、frappe_china 在后。LG-139 在两站都已验 |
| 8 | `company_defaults.json` 键 | 1／5 | `expense_claim_type`（Part1）与 `expense_claim_type_fallback`（R6）都由 `expense_claim_account_number` 读，一致；同一处排版瑕疵两片都报了，合并为 FD-024 |
| 9 | `realtime_check` 事件 | 4 | 只有 desk 页消费，不复用 `erx_demo_step`，与 ADR-0008 一致；`/crm` 一侧没有消费方（FD-032） |

## 集成检查

| 集成点类型 | 具体落点 | 两端一致否 | 说明 |
|---|---|---|---|
| 事件／消息 | `frappe_china_realtime_check {token, sent_at}`：`run()` → user room → `realtime_check.js` → `ack()` | ⚠ | 两端字段一致；判据按用户、不按终端（FD-003） |
| 接口契约（§13） | **演示操控的事件协议**（`erx_demo_step`，ADR-0008） | ✅ | S5 不发也不消费 `erx_demo_step`；连通检查另用自己的事件名，与 ADR-0008「不复用」一致 |
| 接口契约 | `reorder_installed_apps()` → `{changed, before, after}`；`check_app_order()` 九个键 | ⚠ | 调用方 `setup.sh` 6.2 段与开发守则一致；判别力比守则写的窄（FD-005、FD-006） |
| 接口契约 | Raven `Raven AI Function` 类型 ↔ 上游 Agents SDK 路径 | ❌ | `Get Report Result` 在 Local LLM 路径被跳过（FD-004） |
| 共享状态 | `installed_apps`：库、`site_config`、`tabInstalled Application` | ⚠ | 前两处一致，第三处是安装先后的顺序（FD-012） |
| 共享状态 | `socketio_port` ↔ compose 发布端口 ↔ 转发层模板 | ⚠ | 本机三处都是 9100；从空重建时不成立（FD-001） |
| 共享状态 | `ERPNext CRM Settings.erpnext_company` | ✅ | 演示站是 `华东弹簧有限公司`，测试站是 `_FCT CRM 验证`（IT-030 已裁保留） |
| 跨模块数据流 | 装 HRMS → `after_app_install("hrms")` → 回填 | ⚠ | 漏掉复制建账的公司（FD-008） |
| 跨模块数据流 | Company 四个钩子 ↔ HRMS 公司覆盖 | ✅ | 两站实测顺序一致（跨片第 7 项） |
| 跨模块数据流 | CRM Deal → 报价单 → 销售订单 → 自动建客户 | ✅ | 依赖一个未申报的字段（FD-016） |

## 业务规则合规核

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 执行《小企业会计准则》 | 涉及：HRMS 报销类型预配到中式管理费用科目 | 合规 | 科目号按 `company_defaults.json` 映射，兜底 `5602250`（DEC-028，**草案·待领域专家确认**） |
| BR-002 三张报表 | 涉及：HRMS 员工付款进现金流量底稿 | **草案·待领域专家确认** | 员工报销款预填「4 支付的职工薪酬」，按准则可能应是「6 支付其他与经营活动有关的现金」（FD-021，AI 推断） |
| BR-003 增值税税率 | 不涉及 | 合规 | S5 没改税模板；删公司清理的 `Tax Rule` 只删本公司的 |
| BR-004 增值税月末转出 | 不涉及 | 合规 | 月结代码 S5 没改；草稿检查不含 HRMS 单据，记在 FD-021 |
| BR-005 附加税 | 不涉及 | 合规 | — |
| BR-006 资产负债表平衡 | 不涉及 | 合规 | 全量回归中报表用例全过 |
| BR-007 价税分离 | 不涉及 | 合规 | HRMS `EmployeePaymentEntry` 对客户、供应商单据的计算路径没变（片 2 读码） |

**规则新增或变更**：本 Round 没有新增不变量。DEC-028 的兜底科目和 FD-021 的现金流量项目属 AI 拟定，都标「草案·待领域专家确认」，送审时与 BR-001～007 一并提交。

## 自证复核

| 被审产物声称 | 实际复核 | 一致否 |
|---|---|---|
| R8 E：全量 205/205 | 205/205，942.777 秒 | ✅ |
| 项目概况、SB 回执：Raven bot「15 条只读工具（列表、取单据、跑报表）」 | 记录 15 条，bot 实际拿到 14 条，跑报表不可达（主会话复核：两站 bot 都是 `Local LLM`、`openai_assistant_id` 为空，`sdk_tools.py:42-55` 对 `Get Report Result` 直接 `continue`） | ❌ FD-004 |
| 项目概况：「三处同号 9100」 | 本机成立；`setup.sh` 不写这一项，重建后是 9000 | ❌ FD-001 |
| R8 E IT-030：「teardown 会删掉 `_FCT CRM 验证`」 | teardown 不删 Company；真正的风险是 `force=True` 删 `_FCT` 前缀的物料等 | ❌ FD-028 |
| SB 回执：演示站多出 4 条 `Deleted Document` | 实得 8 条，多出的 4 条来自装 HRMS 时改 Employee 命名 | ❌ FD-025 |
| R7 回执：提交号 | 只写了 `8433978`，续做的 `a82499f` 没写 | ❌ FD-034 |
| R5／R7 回执：残留核对「无悬空」 | 报销行确实是 0，但测试站还有 26 条悬空 `Tax Rule` | ⚠ FD-013 |
| 开发守则：「以 `check_app_order` 验，`ok` 为真才算完」 | 覆盖项恒真，进程层验不到 | ⚠ FD-005 |

## 问题清单

三格取值见流程规范 §2.3；片内编号已在「来源」列注明。`用户裁决`列交付时留空。

### 中

| # | 严重程度 | 定位 | 问题描述 | 违背的标准／意图 | 建议 | 建议档位 | 待裁决点 | 状态 | 用户裁决 |
|---|---|---|---|---|---|---|---|---|---|
| FD-001 | 中 | `docker/scripts/setup.sh:101-108`；frappe `node_utils.js:20`；`docker/compose.yaml:73`；`docs/项目概况.md:83`（来源 P4-02） | `setup.sh` 从不写 `socketio_port`，新机器 `bench init` 后是缺省 9000。按 `up.sh` 从空重建后：实时服务监听 9000，转发层连 `frappe:9100` 返回 502，浏览器去连宿主 9000（Windows 保留段）。实时**静默断连**，正是项目概况所说的症状。9100 是 P1-S2-R1 手工写进去的，从没进过脚本；SH-P1S5008 的演练判据也查不出来 | AC-008「新机器重建得到同一个站」；开发守则「判据必须能区分」 | `setup.sh` 第 2 段加 `bench set-config -g socketio_port 9100 --parse`（端口从 `.env` 取，与 compose 同源）；SH-P1S5008 判据补「三处同号」 | 本Session修 | — | 已修复（见当场修清单） | 2026-10-07：按建议 |
| FD-002 | 中 | 两站 `tabRaven Bot.debug_mode=1`；方案 Part3 TS-009-4；Stage 概况长效信息 #4（来源 P3-03） | 方案要求「演示前由 S7 关掉 `debug_mode`，记进 S7 输入」，但路线文档、Stage 概况、项目概况三处都没有。开着时，报错原因会直接发进聊天 | 方案明确要求的交接项漏了 | Stage 概况「本 Stage 的长效信息」#4（交 S7 的输入）补一句「演示前把 bot `debug_mode` 置 0」 | 本Session修 | — | 已修复（见当场修清单） | 2026-10-07：按建议 |
| FD-003 | 中（中／低边界） | `frappe_china/realtime_check.py:68-77`；`docker/README.md:182-184`（来源 P4-01） | `run()` 发给 user room，**这个用户任何一个打开着的桌面页**回执都算通过。本机若以同一用户开着桌面页，终端那边不通也报通过。回执里记了 `client`（页面 Host，本机是 `localhost:8000`），但 `run()` 不判它，输出也不显示它。现在不影响任何功能，SH-P1S5007 实测时才会误判 | 开发守则「判据必须能区分它要区分的两种情形」；需求 §4.8 | 输出里打出 `client`；README 写明「测试时本机不要以同一用户开桌面页，或看 `client` 判」 | 本Session修 | 只改输出与说明，还是给 `run()` 加 `expect_client` 参数按 Host 判 | 已修复（见当场修清单） | 2026-10-07：按建议：只改输出与说明，不加参数 |

### 低

| # | 严重程度 | 定位 | 问题描述 | 违背的标准／意图 | 建议 | 建议档位 | 待裁决点 | 状态 | 用户裁决 |
|---|---|---|---|---|---|---|---|---|---|
| FD-004 | 低（片 3 定高，按暂缓口径降级） | `configure_apps.py:75-86`；上游 `raven/ai/sdk_tools.py:42-55`、`ai.py:24`；Stage 概况 SH-P1S5006；`docs/项目概况.md:103`（来源 P3-01／02／04／09） | **Raven 这块延迟之后留下的说法与实情不符**：① 报表工具 `run_report` 对 bot 不可达，Local LLM 路径跳过 `Get Report Result` 类型且不打日志，bot 实际只有 14 个工具；② 读码看，该路径一轮只执行一批工具调用，问 2、问 3 的「先列单号、再逐张取单据」走不通（未实测）；③ 报表通道并非完全只读：失败写 Error Log、跑满 15 秒会被改成 prepared 模式；④ SH-P1S5006 的描述没写这几条，也没写 IT-015／IT-019／`configure_raven` 的偏离。AI 演示整体暂缓，现在不影响任何功能，但唤醒者只读登记册，会照着「15 条含跑报表」去测 | 三层落地第 2 层；流程规范 §12（登记册是唤醒入口） | **代码不动**，补 SH-P1S5006 描述（①～④ 及出处）；项目概况「能力」节和「演示站当前状态」里的「15 条只读工具」改为「15 条记录，生效 14 条，跑报表不可达，见 SH-P1S5006」 | 本Session修 | (a) 现在就恢复自写包装（Custom Function），推翻 IT-014 的裁决；(b) 只改登记与概况，代码留到唤醒时处理。**建议 (b)** | 已修复（见当场修清单） | 2026-10-07：同意，取 (b) |
| FD-005 | 低（低／中边界） | `install.py:124-140`；`docs/开发守则.md:81`；上游 `installer.py:375`（来源 P1-05、P2-01） | `check_app_order` 的判别力比开发守则写的窄：① 没有别的 app 注册那三个 whitelisted 键，`overrides_ok` 在真调序时恒真；② 归位后不调 `erase_persistent_caches()`，两站都是 developer_mode，运行中的进程仍用旧钩子，而新起进程跑的检查照样报 `ok`。现在不出错，靠的是守则第 2 步要求重启 | 开发守则「判据必须能区分」；HT-004 | (a) 改开发守则那一节：写明 `check_app_order` 只证库、Redis 与新进程，运行中进程靠重启；`overrides_ok` 在无竞争者时恒真 | 本Session修 | 只改文字 (a)，还是 (a) 再加 (b) 在归位末尾补 `erase_persistent_caches()`（动代码，须起着 `bench start` 实测） | 已修复（见当场修清单） | 2026-10-07：(a)+(b) |
| FD-006 | 低（中／低边界） | `install.py:46-49`（来源 P1-03） | `order_ok` 只要求 `frappe_china` 排在四个业务 app 之后。不在常量里的第五个 app 装上后排在 `frappe_china` 之后，`order_ok` 仍为真。开发守则写的是「装完**任何**新 app 后」以它验 | 开发守则「判据必须能区分」；ADR-0003 | `order_ok` 改判「`frappe_china` 之后只有 `TAIL_APPS`」，补一个带未知 app 的单测 | 本Session修 | 改判据，还是收窄开发守则措辞 | 已修复（见当场修清单） | 2026-10-07：改检查 |
| FD-007 | 低 | `tests/test_install.py:85-90`；`hr.py:133`；`test_company_hr_lifecycle.py:163-172`（来源 P1-06、P5-02） | 两处测试没有判别力，**主会话变异已证实**（M1、M2 都全绿）：① 归位函数的 `changed=True` 分支没有测试；② `clear_company_expense_claim_accounts` 的守卫查 `Expense Claim Account`，同文件另两处查 `Expense Claim Type`，测试 patch 的是后者，而且先删光了行 | 开发守则「判据必须能区分」 | ① 加一例：patch 已装列表为乱序，断言调序与镜像同步以目标顺序被调用；② 守卫统一查 `Expense Claim Type`，测试改为断言没有发出删除 | 本Session修 | — | 已修复（见当场修清单） | 2026-10-07：按建议 |
| FD-008 | 低 | `accounting/hr.py:72-79`；`selfcheck.check_all_cn_companies`（来源 P1-04，跨片 1） | 回填按 `chart_of_accounts` 筛公司，复制建账的公司这个字段为空，装 HRMS 时被漏掉；R6 的 `is_cn_company` 能认出它们。目前靠下一次保存公司补上 | 需求 §4.2.2 入口 2「对**全部**中式公司补配」 | 回填改用 `is_cn_company` 判，补一例「复制建账公司 + 装 HRMS」 | 新Session修 | 自检 `check_all_cn_companies` 是否同口径一并改 | 待新Session修 | 2026-10-07：按建议；SB 开工前答待裁决点：先答「自检同口径一并改」，SB 探针实测复制建账公司自检报不过（多 `VAT`、缺 4 个 DEC-097 默认科目，即 S4 FD-008／PH-P1016 的同一缺口）后改判：**自检不改，口径不一致并入 PH-P1016**，本项只改回填 |
| FD-009 | 低 | `hr.py:89-98、114-125`（来源 P5-03） | `repoint` 把中式公司**任何**无号明细科目当成「通用科目」：用户手建一个不填科目号的科目、设为某报销类型的默认科目，下次保存公司就会被改挂，该科目无 GL 时会被**删掉且不留日志** | DEC-027 失效条件；开发守则「静默失败」 | 删除时打 warning；README「已知限制」补一句 | 新Session修 | 只补日志与 README（接受 DEC-027 的边界），还是收窄改挂判定 | 待新Session修 | 2026-10-07：按建议；SB 开工前答待裁决点：只补日志与 README，接受 DEC-027 的边界 |
| FD-010 | 低 | `docker/lock-apps.sh:92-98`（来源 P1-01） | 追加新 app 时不写 `official`，下次 `setup.sh` 会给官方 App 配一个可推送的 `origin`；HEAD 游离时写出空的 `branch`。临时副本已复现 | 开发守则「官方 App 只配只读 upstream」 | 按「无 origin、只有 upstream」推断写 `official: true`，或只警告；HEAD 游离时不写空 branch | 本Session修 | 自动推断，还是只警告由人补 | 已修复（见当场修清单） | 2026-10-07：按建议：自动推断 official 并警告 |
| FD-011 | 低 | `lock-apps.sh:81-82、35-37`（来源 P1-02） | 保留 tag 时不核 HEAD 是否还在该 tag 上，可能写出 tag 与 commit 对不上的条目；`--show` 显示的是记录值，不是仓库现状 | 开发守则「判据必须能区分」 | 保留前比对 `refs/tags/<tag>^{commit}` 与 HEAD，不等就警告；`--show` 同时显示仓库实际 ref | 本Session修 | — | 已修复（见当场修清单） | 2026-10-07：按建议 |
| FD-012 | 低 | `install.py:136-138`；两站 `tabInstalled Application`（来源 P2-02） | 归位没同步 `Installed Applications` 子表，`bench list-apps` 仍把 frappe_china 列在第 3 位，下次 migrate 才自愈 | A5 自己的理由（镜像不一致会误导排查） | 归位后调 `update_versions()`，或在开发守则注明「`list-apps` 不反映装序」 | 本Session修 | 改代码，还是只注明 | 已修复（见当场修清单） | 2026-10-07：按建议：改代码 |
| FD-013 | 低 | 测试站 `tabTax Rule`（来源 P5-01，主会话复现） | 测试站有 26 条 `Tax Rule` 指向已删公司 `FCT_TEMP`、`_FCT 入口二`（各 13 条），引用的模板也已不存在。R5 修 IT-001 时只清了报销行，TS-020 的残留核对也只查报销行。演示站是 0 | IT-002「不留悬空行」；TS-020 残留核对的意图 | 删测试站这 26 条（只限这两家已删公司）；以后的残留核对加上 `Tax Rule` | 本Session修 | 是否允许删测试站这 26 条 | 已修复（见当场修清单） | 2026-10-07：允许 |
| FD-014 | 低 | `configure_apps.py:81`（来源 P3-05） | `Purchase Analytics` 的过滤键描述漏了必填的 `doc_type`、`value_quantity`、`curves`，按描述传参会报错。该工具本身不可达（FD-004） | TS-009-4 | 并入 SH-P1S5006，唤醒时一并改 | 延迟或不修 | — | 延迟 | 2026-10-07：按建议；并入 SH-P1S5006 ③ |
| FD-015 | 低 | `docker/README.md:250`、`docker/configure-apps.sh:6`（来源 P3-06，主会话复现） | 示例 `--company HDTH` 跑不通：脚本按公司全名查（`configure_apps.py:132`），HDTH 是缩写，会报「公司 HDTH 不存在」 | TS-009-5 README 可照做 | 两处示例改为 `--company 华东弹簧有限公司` | 本Session修 | 改文档，还是让脚本也认缩写 | 已修复（见当场修清单） | 2026-10-07：按建议：改文档 |
| FD-016 | 低 | `configure_apps.py:173-180`（来源 P3-07） | 方案外夹带：脚本写了 `CRM Settings.enable_frappe_crm_data_synchronization=1`，它是自动建客户的必要前提，但方案、SB 回执、README 都没提 | F Spec 预设提示词 7 | 追认，在 README「配置四个 App」节补这一字段及原因 | 本Session修 | 追认夹带 | 已修复（见当场修清单） | 2026-10-07：按建议：追认 |
| FD-017 | 低 | `configure_apps.py:168-171、243-248、313-316`（来源 P3-08） | 首跑时 CRM 段建自定义字段会隐式提交，后面若因「已有写类工具」报错退出，rollback 撤不回 CRM 段，输出也不列已落库的改动。读码推断，未实测 | 开发守则「不静默」 | 把写类工具检查挪到最前面做只读预检，或每段写完立即打印 | 新Session修 | — | 待新Session修 | 2026-10-07：按建议 |
| FD-018 | 低 | `compose.yaml:53`；`.env.example:8-9`；`README.md:79,94`（来源 P4-03） | 端口文档三处与实情不符：compose 注释写「两处一起改」（实为三处）；`.env.example` 写「容器内仍是 9000」（实为 9100）；README「结构」节漏了 `realtime-proxy` | TS-013-4 | 三处措辞对齐 README 端口节 | 本Session修 | — | 已修复（见当场修清单） | 2026-10-07：按建议 |
| FD-019 | 低 | `docker/README.md:189`（准备清单 ②）（来源 P4-04） | 外网准备清单只探测本项目的五个端口。本机还有 LiteLLM 的 7999 与它的 postgres 5432 监听 `0.0.0.0`，按清单打勾证明不了 AC-009「只有两条可达」 | AC-009；LG-008 | 清单 ② 改为「列出全部 `0.0.0.0` 监听逐个判」，点名 7999／5432；SH-P1S5005 补一句 | 本Session修 | 同机 LiteLLM 组网时怎么处置，留到 SH-P1S5005 唤醒时定 | 已修复（见当场修清单） | 2026-10-07：按建议；LiteLLM 处置留 SH-P1S5005 唤醒时定 |
| FD-020 | 低 | Stage 概况 SH-P1S5007（来源 P4-07） | 登记描述不全：没写 SL-008 ⑥ 的终端侧与截图；没写「恢复直通映射」要重建容器的代价；「上线前对照」可改用容器内协议层探针（片 4 已实测得 `Invalid namespace`） | 流程规范 §12 | 补描述，把协议层探针写成可选替代 | 本Session修 | 是否接受协议层探针替代真终端 | 已修复（见当场修清单） | 2026-10-07：按建议；协议层探针写作可选替代 |
| FD-021 | 低 | `hrms/overrides/employee_payment_entry.py`；`fixtures/cash_flow_code.json:34-39`；`closing.py:21-30`（来源 P2-03） | HRMS 打开的员工付款路径 S4 没覆盖：员工报销款预填现金流量「4 支付的职工薪酬」（**草案·待领域专家确认**）；月结草稿检查不含 HRMS 单据；HDTH 报销应付科目为空 | 需求 §4.2.2；BR-002 | 登延迟，HRMS 报销真正启用前三件一起交会计确认 | 延迟或不修 | 唤醒条件：IM-016 开工或演示要报销时 | 延迟 | 2026-10-07：按建议；登记 SH-P1S5009 |
| FD-022 | 观察（用户改判，原定低） | `docs/开发守则.md`「工具链索引」；容器 `env/bin`、宿主 PATH（主会话） | 工具链索引把 Ruff 列为格式化与 Lint 工具，但容器和宿主机都没装，本轮 Lint 门跑不了，S5 新增的 Python 代码没过 Lint | F Spec 预设提示词 3（验证门亲自实跑） | 定下 Ruff 装在哪、锁哪个版本，补跑一次 S5 改动面 | 新Session修 | 装进 bench venv（锁版本）、装在宿主，还是在工具链索引写明「未装」 | 已修复（见当场修清单） | 2026-10-07：降为观察；临时取 Ruff 0.14.10 跑一次 Lint |

| FD-036 | 低 | `frappe_china/accounting/company.py:39`（主会话 Ruff F402） | `is_cn_company` 里 `for _ in range(10):` 把模块级导入的翻译函数 `_` 遮蔽成局部变量。函数体内现在没有调 `_()`，不出错；但以后在这个函数里加一句 `_("…")` 会拿到整数、抛 `TypeError`，形态与 S4 FD-010（F823）同类 | 开发守则「判据必须能区分」之外的代码卫生；Ruff F402 | 循环变量改名为 `_attempt` 或 `__` | 本Session修 | — | 已修复（见当场修清单） | 2026-10-07：当场修 |

### 观察

| # | 严重程度 | 定位 | 问题描述 | 建议 | 建议档位 | 待裁决点 | 状态 | 用户裁决 |
|---|---|---|---|---|---|---|---|---|
| FD-023 | 观察 | `setup.sh:156-170`（P1-07） | 预检只在首次克隆时跑；报错不区分 rc=2（ref 不存在）与 rc=128（访问不了） | 接受宽读，或报错里打出 rc | 延迟或不修 | 是否接受宽读 | 不做 | 2026-10-07：按建议：接受宽读 |
| FD-024 | 观察 | `company_defaults.json:33-34`；`setup.sh` 注释（P1-08、P5-05） | 两个键挤在一行；`setup.sh` 几处改动的注释没写需求编号 | 下次改到时顺手修 | 延迟或不修 | — | 不做 | 2026-10-07：按建议：下次改到时顺手修 |
| FD-025 | 观察 | SB 回执；演示站 `tabDeleted Document`（P2-04） | SB 回执说 4 条，实为 8 条；多出的来自装 HRMS 时改 Employee 命名方式，回执与项目概况都没写 | 留档；S8G 建员工时知悉 | 延迟或不修 | — | 不做 | 2026-10-07：按建议：留档 |
| FD-026 | 观察 | 方案 Part2 TS-007；AC-006（P2-05） | AC-006 要求 HDTH 在 `zh`、`en` 下各保存一次，方案收窄为只在 `zh` 下，没列进偏离表；`en` 由单测覆盖 | 留档 | 延迟或不修 | 是否接受单测代替 | 不做 | 2026-10-07：按建议：接受单测代替 |
| FD-027 | 观察 | `crm/hooks.py`；需求 §5.1；ADR-0004（P2-06） | CRM 还整类覆盖了 `Contact`、`Email Template`，需求与 ADR 只记了 HRMS 的 | S6／S7 改 Contact 时走 `doc_events`；补进覆盖清单 | 延迟或不修 | — | 不做 | 2026-10-07：按建议；已记进 Stage 概况长效信息 #3 交 S6／S7 |
| FD-028 | 观察 | `tests/raven_dataset.py`；R8 IT-030（P3-10，跨片 6） | 防误用只靠注释，`build` 会挑中 `_FCT CRM 验证`；IT-030 写的风险与代码不符 | 并入 SH-P1S5006（随 FD-004 一起补描述） | 延迟或不修 | — | 延迟 | 2026-10-07：按建议；并入 SH-P1S5006 ④ |
| FD-029 | 观察 | `.env.example:32-35`（P3-11） | 新加注释是英文，也没写「三个须一起设」 | 改中文，补那一句 | 本Session修 | — | 已修复（见当场修清单） | 2026-10-07：按建议 |
| FD-030 | 观察 | `realtime_check.py:41,54,79-80`（P4-05） | `run()` 退出时删键，宽限期不起作用；晚到的回执会在终端弹英文报错 | 并入 SH-P1S5007 | 延迟或不修 | 是否改为不删键 | 延迟 | 2026-10-07：按建议；并入 SH-P1S5007 ④ |
| FD-031 | 观察 | `realtime-proxy/default.conf.template:16`（P4-06） | nginx 只在启动时解析一次 `frappe`，frappe 容器重建换 IP 后可能 502。读码推断 | 加 resolver，或 README 补「重建 frappe 后重启 proxy」 | 延迟或不修 | 改配置还是补说明 | 延迟 | 2026-10-07：按建议；并入 SH-P1S5007 ⑤ |
| FD-032 | 观察 | `hooks.py:30`（P4-08） | 回执脚本只在 desk 加载，`/crm` 一侧的实时连接从局域网没验过 | 交 S7（CR-009 心跳覆盖 `/crm`） | 延迟或不修 | — | 延迟 | 2026-10-07：按建议；已记进 Stage 概况长效信息 #3 交 S7 |
| FD-033 | 观察 | `hr.py:23-25`；LG-014（P5-04） | 译名命中依赖会话语言；两站实测都是英文名，LG-014 已有答案但仍标「待验证」 | 关闭 LG-014；README 补一句 | 延迟或不修 | — | 不做 | 2026-10-07：按建议；LG-014 的答案（两站报销类型都是英文名）留档于本报告 |
| FD-034 | 观察 | R7 D 回执；提交 `a82499f`（P5-06） | R7 回执没写续做的提交号，该提交还混入了 SB 的两项 | 以后的回执写明提交号 | 延迟或不修 | — | 不做 | 2026-10-07：按建议 |
| FD-035 | 观察 | `docker/apps.json`；`install.py:5`（跨片 5） | 业务 app 顺序在两处各存一份，没有检查保证一致 | `check_app_order` 或 `setup.sh` 加一次比对 | 延迟或不修 | — | 延迟 | 2026-10-07：按建议；登记 SH-P1S5010 |

### 审核自身留痕的处置

| 项 | 内容 | 建议 | 待裁决点 | 用户裁决 |
|---|---|---|---|---|
| 测试站 2 条 Error Log | `ruekosvjr2`、`tiadsd1l5c`（片 3 报表探针所留） | 按这两个 name 正向删除 | 是否允许删 | 2026-10-07：允许；已删，见当场修清单 |

## 当场修清单

| # | 对应问题 | 改动位置 | 用户确认于 |
|---|---|---|---|
| 1 | FD-004（取 (b)） | `docs/项目概况.md`「开发环境·演示站当前状态」与「能力」表 AI 分析行，改为「挂 15 条、实际可用 14 条、跑报表不生效」；Stage 概况登记册 `SH-P1S5006` 补「唤醒时另须处理」①～⑥（并入 FD-014、FD-028 的内容） | 2026-10-07「FD-004、同意」 |
| 2 | FD-013 | 测试站 `tabTax Rule`：删除 `company IN ('FCT_TEMP','_FCT 入口二')` 且公司已不存在的 26 行。删前整行导出到 `frappe-bench/logs/s5-r9-fd013-taxrule-backup.tsv`；删后全库悬空 `Tax Rule` 为 0 | 2026-10-07「FD-013、允许」 |
| 3 | 审核留痕 | 测试站 `tabError Log`：按 name 删 `ruekosvjr2`、`tiadsd1l5c` 两行。删前导出到 `frappe-bench/logs/s5-r9-errlog-backup.tsv` | 2026-10-07「审核留痕、允许」 |

| 4 | FD-001 | `docker/scripts/setup.sh:107-110` 第 2 段加 `bench set-config -g socketio_port 9100 --parse` 并注明三处同号；登记册 `SH-P1S5008` 判据补「三处同号」 | 2026-10-07「其余按建议」 |
| 5 | FD-002 | Stage 概况「本 Stage 的长效信息」#4 补「演示前把 bot `debug_mode` 置 0」 | 2026-10-07「其余按建议」 |
| 6 | FD-003 | `frappe_china/realtime_check.py:76-81` 通过时打出「回执页面」（`client`）；`docker/README.md`「连通检查」节写明只认用户及怎么区分；登记册 `SH-P1S5007` 补同一句 | 2026-10-07「其余按建议」（待裁决点取「只改输出与说明」） |
| 7 | FD-005 | (a) `docs/开发守则.md`「装完任何新 app 后…」第 3 条后补一段：检查证明不了重启做没做、`overrides_ok` 无竞争者时恒真；(b) `frappe_china/install.py:147-149` 归位末尾补 `frappe.client_cache.erase_persistent_caches()` | 2026-10-07「FD-005、(a)+(b)」 |
| 8 | FD-006 | `frappe_china/install.py:47-50` `order_ok` 改判「`frappe_china` 之后只许有 `TAIL_APPS`」，问题文案列出排在它后面的 app；`tests/test_install.py:224` 新增 `test_check_app_order_rejects_unknown_app_after_china`；开发守则第 3 条同步一句 | 2026-10-07「FD-006、改检查」 |
| 9 | FD-007 | ① `tests/test_install.py:85` 新增 `test_reorder_installed_apps_rewrites_order_mirror_and_caches`（乱序站，断言调序、镜像、子表、清缓存、广播都按目标顺序调一次）；② `accounting/hr.py:134` 守卫改查 `Expense Claim Type`；`tests/test_company_hr_lifecycle.py:167-177` 改为断言不发任何报销表语句 | 2026-10-07「其余按建议」 |
| 10 | FD-010 | `docker/lock-apps.sh:104-121` 追加新 app 时：无 `origin` 即标 `official: true` 并警告；HEAD 在分支上写 `branch`、在 tag 上写 `tag`，都不在则不写并警告 | 2026-10-07「其余按建议」 |
| 11 | FD-011 | `docker/lock-apps.sh:36-43` `--show` 同时显示仓库实际 ref；`:88-93` 保留 tag 前核 `refs/tags/<tag>^{commit}` 与 HEAD，不等即警告 | 2026-10-07「其余按建议」 |
| 12 | FD-012 | `frappe_china/install.py:143-145` 归位后调 `Installed Applications.update_versions()` | 2026-10-07「其余按建议」 |
| 13 | FD-015 | `docker/README.md`「配置四个 App」与 `docker/configure-apps.sh:6` 示例改为 `--company 华东弹簧有限公司`，README 注明填全名 | 2026-10-07「其余按建议」 |
| 14 | FD-016 | `docker/README.md`「配置四个 App」补 `CRM Settings.enable_frappe_crm_data_synchronization` 置 1 及原因（追认夹带） | 2026-10-07「其余按建议」 |
| 15 | FD-018 | `docker/compose.yaml:53-54` 改「三处一起改」并列出三处；`docker/.env.example:8-10` 改正「容器内仍是 9000」、注明不可单改；`docker/README.md`「结构」节补 `realtime-proxy`、`configure-apps.sh`、`realtime-proxy/` | 2026-10-07「其余按建议」 |
| 16 | FD-019 | `docker/README.md` 准备清单 ② 改为列出全部 `0.0.0.0` 监听逐个判、点名 `7999`／`5432`；登记册 `SH-P1S5005` 补一句 | 2026-10-07「其余按建议」 |
| 17 | FD-020 | 登记册 `SH-P1S5007` 补 ①～③（SL-008 ⑥ 终端侧与截图、恢复直通映射的代价、协议层探针作可选替代），一并补 FD-030／031 为 ④⑤ | 2026-10-07「其余按建议」 |
| 18 | FD-022 | 临时取 Ruff 0.14.10（`pip install --target .claude/tmp-ruff`，不进 bench 环境，用完删）跑 S5 改动面，结果见「验证门实跑结果」；`docs/开发守则.md` 工具链索引的格式化／Lint 行写明「未装进 bench 环境、审核时临时取用、基线见 `PH-P1019`」 | 2026-10-07「FD-022、将为观察，…临时取一次 Ruff 0.14.10 跑 Lint」 |
| 19 | FD-029 | `docker/.env.example:32-33` 注释改中文，补「三个须一起设、密钥不进文档」 | 2026-10-07「其余按建议」 |
| 21 | FD-036 | `frappe_china/accounting/company.py:39-40` 循环变量 `_` 改名 `_attempt` 并注明原因；`test_company` 13/13、`test_company_hr_lifecycle` 15/15（日志 `s5-r9-fd036-*.log`） | 2026-10-07「FD-036、当场修」 |
| 20 | 登记去向 | Stage 概况：新增 `SH-P1S5009`（FD-021）、`SH-P1S5010`（FD-035）；长效信息 #3 补 FD-027／FD-032 交 S6／S7 | 2026-10-07「其余按建议」 |

| 22 | 提交与锁定 | `frappe_china` 提交 `acededb` 并推送；`docker/apps.json` 的 frappe_china `commit` 由 `4b21aae` 改为 `acededb`（`lock-apps.sh` 写入，其余条目无差异） | 2026-10-07「修完之后提交并推送」 |

**修后验证**：
- 全量回归 `bench --site test.localhost run-tests --app frappe_china`：**Ran 207 tests in 963.436s, OK**，`EXIT=0`（日志 `frappe-bench/logs/s5-r9-fix-full.log`）。205 → 207，新增 FD-006、FD-007① 两例。
- 变异复测（改完从备份还原、`cmp` 一致）：M1 去掉 `changed` 分支的调序与镜像 → `test_install` **1 例失败**（原 16/16 全绿）；M2 去掉清理守卫 → `test_sl011_5_1` **失败**（`Lists differ: [call('Expense Claim Account', …)] != []`，原全绿）；M3 `order_ok` 退回旧判据 → `test_install` **1 例失败**。日志 `s5-r9-remut-m{1,2,3}.log`。
- `lock-apps.sh` 在临时目录的 `apps.json` 副本上试：原样写入与原文件无差异；删掉 raven、insights 条目后写入，追加出的条目带 `official: true`，insights 带 `tag: v3.14.2`；把 insights 的 tag 改成 `v3.14.1` 后写入，打出「HEAD 不在 tag 上」警告。`docker/apps.json` 本身未改。
- 测试站实际归位一次：`reorder_installed_apps` 返回 `changed: true`，之后 `site_config` 镜像、`tabInstalled Application` 子表、全局 `installed_apps` 三处都是 `frappe, erpnext, crm, hrms, insights, raven, frappe_china`，`check_app_order` 五项全真、`problems` 空。
- **FD-005 (b) 的生效没能实测确认**：在开着 `bench start` 的测试站上把库改成 `frappe_china` 在 `hrms` 前，再广播 `erase_persistent_caches`（3 个订阅者收到）。用桌面页的脚本引入顺序当探针，广播后 70 秒仍是旧顺序；但用 `touch` 触发 web 进程重载后也看不出变化，说明这个探针本身反映不了钩子顺序，结论不成立。代码按读码与上游装 app 的做法保留；开发守则据此写明「重启不可省」，没有把 (b) 写成能代替重启。站点已归位，测试站状态与修前一致。
- Ruff 对本轮改动的 5 个 Python 文件跑 F／E9：`All checks passed!`

## 总体判断

**基本满足源头意图。** 四个 App 已装进两站，`frappe_china` 已归位，CRM 链路、Insights、删公司清理和报销映射都三层成立；全量回归 205/205。

关键缺口有三处：
1. 从空重建时实时通道会静默断（FD-001）。这不是本 Stage 引入的，但 S5 加的转发层依赖它。
2. 已延迟的 Raven 一块，登记册与项目概况写的比实际多（FD-004）。
3. 几处判据与测试的判别力比文档声称的窄（FD-003、005、006、007），变异已证实其中两处。

暂缓区（外部设备、LiteLLM、重建演练）只补登记描述，不建议动代码。

## 状态值

**`有发现`**——36 条（FD-036 为修复轮 Ruff 新出）：中 3、低 19、观察 14（FD-022 用户改判为观察）；另有审核自身留痕 1 项。

**裁决后去向**（2026-10-07）：
| 去向 | 项 | 下一步 |
|---|---|---|
| 本步当场修（19＋留痕 1） | FD-001～007、010～013、015、016、018～020、022、029、036，审核留痕 | **已修复**，见「当场修清单」，全量 207/207 |
| `新Session修`（3） | FD-008、FD-009、FD-017 | 唤起 **SB**，修完回 F 复核。FD-008、FD-009 的待裁决点 SB 开工前问 |
| 延迟（7） | FD-014、028 → `SH-P1S5006`；FD-030、031 → `SH-P1S5007`；FD-021 → `SH-P1S5009`；FD-035 → `SH-P1S5010`；FD-032 → 长效信息 #3 交 S7 | 已进登记册 |
| 不做（7） | FD-023～027、033、034 | 留档 |

## 复核建议

1. **定级最靠边界的三条**：
   - FD-004：片 3 定高，我按暂缓口径降为低。理由是 AI 演示整体延迟，现在没有任何功能受影响。不同意的话，它就该升到高，并且要推翻 IT-014 的裁决。
   - FD-003：中和低之间。它只在 SH-P1S5007 实测时才会误判。
   - FD-005：低和中之间。现在靠开发守则第 2 步的重启兜住。
2. **把握最低的一片是片 4**：首跑被 API 拦截，重跑的子 Agent 不能停 proxy、不能跑 `run()`。FD-031（nginx 只解析一次）是纯读码推断。要实证，在测试环境执行 `docker compose up -d --force-recreate frappe` 后，看 proxy 是否返回 502。这一步会重建容器、丢字体（IT-028），所以本步没做。
3. **没往哪个方向找**：没有对照 S4 的历史遗留行为逐项回看（只靠全量回归兜底）；没有查四个官方 App 自身的权限与数据暴露面（只查了 Raven 工具这一处）；`/crm`、`/insights`、`/raven` 三个独立前端没有任何实点。
4. **拿不准处**：FD-016（CRM 同步开关）算「方案外夹带」还是「方案漏写的必要步骤」，两种读法都通，我按夹带报、建议追认。FD-002 要求写进 Stage 概况长效信息 #4，那一栏属于 Stage 概况、不属于职责外的跨轮演进产物，所以我判本步可以改，不必回写路线文档。
