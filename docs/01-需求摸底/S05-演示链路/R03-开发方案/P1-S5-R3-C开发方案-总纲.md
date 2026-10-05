# P1-S5 演示链路 —— 开发方案·总纲

**来源需求**：[R2 B 需求文档](../R02-需求文档/P1-S5-R2-B需求文档.md) v1.0（TS-001～012、AC-001～010）＋本轮 [C 讨论记录](P1-S5-R3-C讨论记录.md)（DEC-021／022）
**日期**：2026-10-05｜**编写者**：Claude（Opus 5.5）｜**执行者**：Claude（路线文档 §四 S5 的偏离：D 步执行者由 CodeX 改为 Claude）
**状态值与复核建议**：不在本文件——见 [P1-S5-R3-C回执](P1-S5-R3-C回执.md)

> **编号**：切片 `SL-`、任务 `TS-`、技术假设 `HT-` 为本方案内编号。**需求文档里也有 `TS-` 编号，二者不是一回事**，引用需求的任务一律写「需求 TS-00x」。决策 `DEC-`、遗留 `LG-` 沿用本 Stage 序号。
> **方案是只读依据**：执行进度只写 D 回执，不回写本方案（Spec 补充规则）。

## 一、概述

**要做的事**：把 CRM、HRMS、Insights、Raven 四个官方 App 按锁定版本装进测试站与演示站，让 `frappe_china` 回到它们之后；`frappe_china` 为中式公司预配 HRMS 报销类型科目，保住 S4 的科目表；CRM 的线索到销售订单链路实点通过；Raven 只读 bot 连上 LiteLLM 并实测三问；Insights 装成并跑一次查询；局域网异地终端的页面与实时通道都通，组网（外网）一段做到理论就绪。

**完成标准**（本方案的验收总口径）：

1. 各切片验收条件全部通过（§三索引，完整条件在各 Part）。
2. `frappe_china` 全量测试：S4 收口时 160 条全过，本方案新增测试另计，**只增不减**。
3. 演示站最终状态：`installed_apps` 为 `frappe, erpnext, crm, hrms, insights, raven, frappe_china`；`HDTH` 科目 266、自检全过；无测试数据残留；有一份新的空账基准点备份，`20261004_005331` 仍在。
4. 需求文档 AC-001～AC-003、AC-005～AC-008、AC-010 逐条有正向证据；AC-004 只验局域网，AC-009 随 `SH-P1S5005` 移后（DEC-022）。

## 二、Part 索引

| Part | 文件 | 内容 | 切片 | 任务 |
|---|---|---|---|---|
| 1 | [Part1](P1-S5-R3-C开发方案-Part1.md) | 版本锁定与重建脚本、`frappe_china` 归位函数、报销类型科目预配 | SL-001～SL-002 | TS-001～005 |
| 2 | [Part2](P1-S5-R3-C开发方案-Part2.md) | 测试站接入与回归、演示站接入、归位验收 | SL-003～SL-004 | TS-006～008 |
| 3 | [Part3](P1-S5-R3-C开发方案-Part3.md) | 应用配置脚本、CRM、Insights、Raven 与三问 | SL-005～SL-007 | TS-009～012 |
| 4 | [Part4](P1-S5-R3-C开发方案-Part4.md) | 局域网连通、组网就绪、重建演练、全量回归与收尾 | SL-008～SL-010 | TS-013～016 |

## 三、切片划分与验收（索引）

| 切片 | 功能点（需求编号） | 验收条件摘要（完整版在所在 Part） |
|---|---|---|
| **SL-001** 版本锁定与重建脚本 | 需求 TS-001／002／003；DEC-001／003／015；§4.2.1 五条 | `apps.json` 七条、按装载顺序排；`setup.sh` 认 tag、按 `apps.json` 顺序装、装完归位、官方 App 只有只读 `upstream`；`lock-apps.sh` 不改顺序与 tag |
| **SL-002** 报销类型科目预配 | 需求 TS-004；DEC-005；§4.2.2 入口 1、2 | 新建中式公司与装 HRMS 时各自配好 5 条；已有的不覆盖；HRMS 不在时零动作；不建 `Expense Claims` |
| **SL-003** 测试站接入与 S4 回归 | 需求 TS-005；DEC-006；RS-001／002 | 四个 App 装成；`frappe_china` 全量测试全过；新建中式公司科目 266、`zh`／`en` 各保存一次不变 |
| **SL-004** 演示站接入与归位验收 | 需求 TS-006／007；DEC-004；AC-002／006 | 装前备份；四个 App 装成；`HDTH` 保存后 266；顺序、三个覆盖、撞源词译名三条正向通过，撞源词反证一次 |
| **SL-005** CRM 链路与看板 | 需求 TS-008；DEC-007／008；AC-001 | Lead → Deal → 报价 → 销售订单，客户自动建出，币种 CNY，看板计入 |
| **SL-006** Insights | 需求 TS-009；DEC-016；AC-007 | 装成、打开、对 `Site DB` 跑一次查询有结果 |
| **SL-007** Raven 与三问 | 需求 TS-010／011；DEC-009～014／020；AC-003 | 经 LiteLLM 答复一次；bot 只挂只读工具；三问各 3 次，报告逐问记录 |
| **SL-008** 局域网异地终端连通 | 需求 TS-012；DEC-017；AC-004（局域网） | 异地终端打开单据；检查工具收到回执报通过；断开实时转发层时同一工具报失败；本机 `localhost` 照旧 |
| **SL-009** 组网就绪 | DEC-021／022 | 使用说明、准备清单、延迟需求齐备；检查工具不依赖局域网地址 |
| **SL-010** 重建演练与收尾 | AC-008／010；Stage 收尾 | 空目录按 `apps.json` 重建成功且顺序正确；全量回归；新空账基准点；常驻文件回写 |

**执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。**

## 四、关键架构决策（本方案新定，C 步职责内）

| # | 决策 | 理由 |
|---|---|---|
| **A1** | **`apps.json` 改按装载顺序排列**：`frappe, erpnext, crm, hrms, insights, raven, frappe_china`；`setup.sh` 第 6 段改为按这个顺序装，归位也以它为目标顺序 | 需求 §4.2.1 第 2／3 条要一个权威顺序；把它放在已有的清单里，不另立配置 |
| **A2** | **`apps.json` 条目新增 `"official": true`**，标出「url 就是官方仓库、无自有 fork」的 App。`setup.sh` 第 4 段对它们只配只读 `upstream`、不建 `origin`；`lock-apps.sh` 对它们读 `upstream` 的 URL | 需求 §4.2.1 第 4 条；用数据标记代替在脚本里写死四个仓库名 |
| **A3** | **`apps.json` 条目新增 `"tag"` 字段**（Insights 填 `v3.14.2`），与 `branch` 二选一；`setup.sh` 取 tag 时用它，`lock-apps.sh` 检出在 tag 上（`HEAD` 游离）时保留原 `tag`、不写 `branch: HEAD` | 需求 §4.2.1 第 1／5 条 |
| **A4** | **归位函数放 `frappe_china`**：`frappe_china.install.reorder_installed_apps(order)`，`setup.sh` 在第 6 段之后经 `bench execute` 调用 | 「`frappe_china` 必须在业务 app 末位」是 `frappe_china` 自己的约束（ADR-0003），S8G-S1 的 IM-007 自检也将断言它；函数内校验、幂等，比在 shell 里拼 JSON 可靠 |
| **A5** | **LG-010 定为同步**：归位时把 `site_config.json` 的 `installed_apps` 镜像一并改成新顺序 | 一行代码；镜像过期虽预计无害，但它是给 bench 等外部工具读的，与数据库不一致会误导排查 |
| **A6** | **四个 App 在站点上的配置（CRM 集成、Raven 连接、bot 与工具）写成可重放脚本** `docker/configure-apps.sh`，幂等，两站都跑；密钥与模型别名从 `docker/.env` 读，不进仓库 | 演示站重建、新机器、S7 造数都要重现这套配置；手工点一遍不可复现 |
| **A7** | **三问的测试数据与标准答案写成 `frappe_china/tests/raven_dataset.py`**：`build()`／`teardown()`／`expected()`。标准答案按模块内常量独立算出，`build()` 建完后反查库里的值与常量一致，否则报错 | 需求 §4.6.5 要「事先算好标准答案」；从常量算而不是从库里读，才不会把库里的错误当成标准答案 |
| **A8** | **自写查询函数（仅退路，需求 §4.6.4）放 `frappe_china/ai/queries.py`**，用 `frappe.get_list`（带权限）而非 `get_all` | `frappe_debug` 到 S7 才建；这几个查询是业务分析，客户正式库装了 Raven 也能用，不是演示操控（ADR-0013 的分界）；用 `get_list` 顺带不扩大 LG-091 |
| **A9** | **局域网连通机制**：在实时端口前加一层转发（compose 新服务 `realtime-proxy`，镜像锁版本），接管宿主的实时端口；来源不是本机名（`localhost`／`127.0.0.1`／`*.localhost`）时补请求头 `X-Frappe-Site-Name: ${SITE_NAME}`，否则原样透传。**不改上游源码**；组网地址与局域网地址走同一分支（DEC-021） | 需求 §4.8 四条约束；`authenticate.js:89-104` 优先认这个请求头 |
| **A10** | **连通检查工具** `frappe_china/realtime_check.py`＋桌面端监听脚本：本机发一条只供本检查的事件（`frappe_china_realtime_check`，带随机令牌）给指定用户，异地终端页面收到后弹提示并经页面通路回一次确认；本机在时限内收到确认报「通过」，否则报「失败」 | 需求 §4.8 要「界面可见地收到」且检查分得清通与不通；回执走页面通路，故实时通路断时必然收不到确认，反证天然成立；不复用 `erx_demo_step`（ADR-0008） |
| **A11** | **装 App 的先后**：测试站首次装按 `crm → hrms → raven → insights`（Insights 最后，RW-02），装完由归位函数把顺序调成 A1 的目标顺序；演示站与新机器重建按 `apps.json` 顺序装 | 需求 §4.3 第 1 条字面写「crm → hrms → insights → raven，Insights 最后」，两句互相矛盾；按 RW-02 取「Insights 最后装」，最终顺序由归位兜住、仍为 ADR-0003 的顺序 |
| **A12** | **新空账基准点移到 Stage 末尾**（TS-016）再出，而不是装完 App 就出（需求 §4.3 演示站第 4 条） | 演示站上还要配 CRM、Raven 与连通转发；在全部配置之后出，基准点才包含 S7 要用的完整状态 |

## 五、技术假设

| 编号 | 假设内容 | 状态 | 验证方式 | 不成立时 |
|---|---|---|---|---|
| HT-001 | `bench get-app --branch v3.14.2 <url>` 能按 tag 克隆（bench 把它拼成 `git clone --branch`，git 接受 tag） | 读码（`bench/app.py:189-194`），未实跑 | TS-006 取 Insights 时；TS-015 重建演练 | 暂停反馈 |
| HT-002 | 站上已装 `frappe_china` 时装 HRMS，框架在 HRMS 的 `after_install`（建 5 个报销类型）之后调 `frappe_china` 的 `after_app_install("hrms")` | 读码已确认（`installer.py:359-363`、`hrms/setup.py:14-26`），未实跑 | TS-006、TS-007 装 HRMS 后查 `Expense Claim Account` | 暂停反馈 |
| HT-003 | 新建中式公司时，HRMS 的两个建科目钩子被 `ignore_chart_of_accounts` 门控跳过；钩子先于或后于 `frappe_china.on_update` 跑都不建 `Expense Claims` | 读码（`hrms/overrides/company.py:100-135`、`frappe_china/accounting/company.py:34-61`） | TS-005 测试；TS-006 第 4 条 | 暂停反馈 |
| HT-004 | 调序后清缓存并重启 web／worker／实时进程，钩子与译名即按新顺序取（LG-002） | 读码一半（`cache_manager.py:281-313` 清全局键与 `client_cache`，开发模式进程内 `site_cache` 须重启） | TS-008 第 3 条撞源词正反两向 | 暂停反馈 |
| HT-005 | CRM 新建 Deal 时 `currency` 经全局默认值 `currency=CNY` 自动取 CNY（`create_new.py:80-93` 的 Link 字段取用户／全局默认） | 未验证 | TS-010 第 1 步 | 不暂停：由 `configure-apps.sh` 给 `CRM Deal.currency` 加属性默认值 CNY（L0），重验 |
| HT-006 | Raven 经 `OpenAI Compatible` 连 `http://host.docker.internal:7999/v1`，用户给的模型别名支持工具调用 | 部分：容器到 LiteLLM 健康检查 200；工具调用未验证 | TS-011 第 3 步 | 暂停反馈（模型归用户，DEC-011） |
| HT-007 | `Custom Function` 指向 `raven.ai.functions.get_report_result`，AI 传入报表名与过滤条件即可拿到列与行（LG-006） | 读码（`functions.py:256-283`、`sdk_tools.py:38-41`），未实跑 | TS-011 第 5 步 | 不暂停：记 LG-006 不通，按需求 §4.6.4 走 A8 退路 |
| HT-008 | 转发层补 `X-Frappe-Site-Name` 后，局域网来源的实时连接过得了命名空间与来源两项校验，且实时服务回访页面端口鉴权成功 | 读码（`authenticate.js:13-40、89-104`、`realtime/utils.js`）＋部分实测（容器经局域网地址访问页面端口 200） | TS-013 | 暂停反馈 |
| HT-009 | 四个 App 的 Python 依赖在容器 Python 3.14 下可装、互不冲突 | 已验证（容器内 `pip install --dry-run` 全部可解析、`pip check` 无冲突；`blurhash-python` 源码编译成功） | — | — |
| HT-010 | `frappe_china` 在 `app_include_js` 里引一个不经构建的普通 js 文件，桌面端能直接加载（`sites/assets/frappe_china` 已链到本 app 的 `public/`） | 读码＋目录核对 | TS-013 第 1 步 | 暂停反馈 |
| HT-011 | HRMS 整类覆盖 `Payment Entry` 后 S4 的 160 条测试仍全过（RS-002） | 未验证 | TS-006 第 3 步 | **暂停反馈，不装演示站** |
| HT-012 | 组网环境下：国内可连；容器能以组网地址回访本机页面端口；防火墙放行（LG-013） | 暂缓（DEC-022） | `SH-P1S5005` 唤醒时 | 届时按 Part4 TS-014 写下的备用做法改 |
| HT-013 | `bench get-app` 取四个 App 时顺带 `pip install` 与前端构建都能完成（依赖已由 HT-009 验过，构建未验） | 未验证 | TS-006 第 1 步 | Insights 失败 → SL-006 异常路径；其余三个失败 → 暂停反馈 |
| HT-014 | CRM 看板的「预测收入」图不以 `enable_forecasting` 为显示条件（后端查询不读它，前端未查） | 未验证（读前端源码时网络中断，未读完） | TS-010 第 6 步 | 不暂停：`configure_crm` 改为开启 `enable_forecasting`（三问数据与实点数据本就填了金额与日期），重验 |
| HT-015 | LiteLLM 的请求日志里能取到每次对话的 `tool_calls` | 未验证 | TS-012 第 4 步 | 不暂停：报告「工具调用」列写「未取到」，判定只看回答（Part3 已写明） |
| HT-016 | Windows 防火墙对局域网入站放行宿主的页面端口与实时端口（Docker Desktop 发布端口时自加规则） | 未验证（只测过容器经宿主局域网地址回访） | TS-013 第 3 步 | 暂停反馈：入站规则属本机安全设置，由用户定 |

## 六、相对需求文档的偏离与更正

| 需求原文 | 本方案 | 依据 |
|---|---|---|
| §4.2.1 第 1 条「`ls-remote --heads` 预检失败即中止」 | 不成立：查不到也退出 0，预检不拦 tag。真正要改的是预检加 `--exit-code` 并同时查 `refs/heads/` 与 `refs/tags/` | C 讨论第 1 步②#6 |
| §4.2.1 第 5 条只提 `branch` 写成 `HEAD` | 另一处：`lock-apps.sh` 按 `origin` 取 URL，官方 App 只有 `upstream`，取到空串后条目对不上 | `lock-apps.sh:41-50` |
| §4.3 第 1 条「crm → hrms → insights → raven，Insights 最后」 | 自相矛盾；取 Insights 最后（A11） | RW-02 |
| §4.3 演示站第 4 条「装完即出新基准点」 | 移到 Stage 末尾（A12） | — |
| §4.4 第 3 条「源词取哪个、测试行用后撤不撤」 | 用已有的 `Formula`：`frappe_china` 译「计算方式」、HRMS 译「公式」；**不加测试行**；反证在测试站做 | C 讨论第 1 步②#8 |
| §4.6.3「报表通道的权限校验未查清」（RS-012） | 读码查明：`_run` 校验 `ref_doctype` 的 `report` 权限 | C 讨论第 1 步②#5 |
| §4.8／AC-004「局域网与外网两种都验」、AC-009 | 只验局域网；组网一段理论就绪，外网实测登 `SH-P1S5005` | DEC-022 |
| §4.9 CR-015 1–2.5 人日 | **1–1.5**（外网实测移出）；本 Stage 合计 **6.5–11**（Raven 常规值 6.5–9） | DEC-019 失效条件「外网连通机制在 C 步定后可再收窄」 |

## 七、并行开发说明

本 Stage 大部分任务在同一个 bench、同两个站点上操作，**不标并行**。唯一可并行的是 Part1 内 TS-005（`frappe_china/accounting/`）与 TS-003／TS-004（`docker/`）：两组改的文件不相交。执行者为单人时按序号顺序做即可。

## 八、执行顺序

```
Part1  TS-001 apps.json ─→ TS-002 归位函数 ─→ TS-003 setup.sh ─→ TS-004 lock-apps.sh
                                  TS-005 报销科目预配（与 TS-003/004 文件不相交）
          │
Part2  TS-006 测试站：取 App、装、归位、S4 全量回归 ──(HT-011 不过即停)──┐
          │                                                          │
       TS-007 演示站：备份、up.sh 装、HDTH 保存 ─→ TS-008 归位验收（反证在测试站）
          │
Part3  TS-009 configure-apps.sh ─→ TS-010 CRM ─→ TS-011 Raven 连接与工具 ─→ TS-012 三问实测
                               └─→ （TS-006 已装 Insights）TS-010 之后的任意时点做 SL-006 验收，见 Part3
Part4  TS-013 局域网连通 ─→ TS-014 组网就绪 ─→ TS-015 重建演练 ─→ TS-016 全量回归与收尾
```

## 九、执行纪律（给执行者，随方案走）

1. **切片前反查**：执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。
2. **假设先验**：任务依赖 §五中「未验证」的假设时，先验掉再写；不成立按该行「不成立时」处理，写「暂停反馈」的就停下来报用户。
3. **中断续跑**：开工即建 D 回执（每个 Part 一份），预填全部任务为「未开始」；每做完一个任务当场回写。中断后从第一个未完成的任务续做，**不回写本方案**。
4. **站点安全**：
   - TS-006 之前与期间**不得对 `erx.localhost` 做任何写操作**；**TS-007 之前不得跑 `docker/up.sh`**（`setup.sh` 第 6 段会把 `apps/` 下的 app 装到演示站）。TS-006 取 App 用手工命令（见 Part2）。
   - TS-007 动演示站前**先核 `20261004_005331` 那套备份仍在 `docker/backups/` 根目录**，再备份；两步都做完才装。
   - 三问测试数据、CRM 实点单据只在 `test.localhost` 上建，测完清掉；演示站只做配置，不留业务单据。
   - 重启 `bench start` 的进程属本地可逆操作，可直接做，在回执里记一笔。
5. **测试纪律**（沿用 S4）：自有测试不 import `erpnext.tests.utils`；涉及语言的断言显式设 `frappe.local.lang`；会触发 `frappe.log_error` 的测试，清理只删能证明是自己造的行。依赖 HRMS 的测试在 HRMS 未装时 `skipTest` 并写明原因，**回执里分开报「通过」与「跳过」的条数**。
6. **密钥**：LiteLLM 密钥、模型别名、演示用新口令只放 `docker/.env`（不进 git），不写进任何文档、回执、日志、测试数据。
7. **版本管理**：主仓库与 `frappe_china` 仓库的改动都只写不提交；提交、推送、打 tag 均须用户许可（CLAUDE.md「版本管理操作规则」）。四个官方 App 的目录不做任何改动。
8. **不静默**：查不到、算不出、对不上一律报错或告警，不输出空列表了事（开发守则「静默失败」）。
9. **最后一个任务（TS-016）做全量回归**，并复核演示站最终状态（§一完成标准第 3 条）。
