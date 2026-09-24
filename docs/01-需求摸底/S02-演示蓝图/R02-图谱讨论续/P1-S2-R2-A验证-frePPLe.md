# P1-S2-R2 A 步验证：frePPLe 能否补 ERPNext v16 的 CRP 缺口

克隆位置：`D:\ERX-001\Reference\frepple`（`--depth 1`，经 Clash 代理拉取成功；直连被 reset）。
仓库版本 `9.19.0`（`pyproject.toml:6`），最后一次提交 `c8d40c6` **2026-09-23**（今天）——**活跃度证实**。

## ① 许可证判定：Community = MIT，无商业使用障碍

**读到的事实**：

- `COPYING`（仓库根，实际打开读过）：开头明写 `The frePPLe software has **dual licensing**`，随后是**完整的 MIT 许可证正文**（Permission is hereby granted, free of charge…）。**全文无 AGPL/GPL 字样。**
- `doc/license.rst` 把双许可结构写死为三层：
  - **Community Edition** —— MIT，"allows any use of the software (**including reuse within proprietary software**)"；
  - **Enterprise Edition** —— 专有商业许可，且 "**The source code of the extensions is not redistributed**"；
  - 另有 commercial OEM license（供不愿受 MIT 条款约束者购买）。
- **Enterprise 代码不在本仓库**：`doc/installation-guide/linux-binaries.rst:41` 指向另一个仓库 `github.com/frePPLe/frepple-enterprise/releases`（仅客户可取）。因此**本次克隆到的全部代码都是 Community/MIT**，仓库内**没有** Enterprise-only 的目录混杂。
- `bin/license.xml` 是一份 Community Edition 的许可文件（`<customer>Community Edition users</customer>`，valid_till 2030-01-01），Enterprise 才需要替换它（`doc/installation-guide/docker-container.rst:180`）。

**判定**：本项目（商业交付给多家弹簧厂）用 Community 版**无法律障碍**。义务只有 MIT 那一条：分发时随附许可证正文与版权声明。GitHub API 的 `NOASSERTION` 是双许可声明扰乱了自动识别，**不是** AGPL 污染——与本项目此前遇到的"根 LICENSE 是 AGPL"情形不同。

**一处需留意（非阻塞）**：`AUTHORS:36,47` 及 `freppledb/common/static/js/i18n/grid.locale-*.js` 里的第三方前端库（jqGrid/jQuery 系）标注 `Dual licensed under the MIT or GPL Version 2` ——双许可可择 MIT，故不传染。

## ② connector 查实：⭐ 仓库里**没有** ERPNext connector 代码

这是本次最重要的发现，且与"官方有 connector 文档页"给人的印象相反。

**读到的事实**：

- 全仓库搜 `erpnext`（`grep -ril`，排除 `.git`）**只命中两个文件，都是文档**：`doc/erp-integration/erpnext-connector.rst` 与 `doc/erp-integration/index.rst`。搜 `frappe` 命中 **0** 个代码文件。
- `doc/erp-integration/erpnext-connector.rst` **全文只有 9 行**，原文：

  > A integration with ERPNext is available as a **third-party application** https://github.com/msf4-0/ERPNext-Frepple-Integration
  > The frePPLe team **contributes to and endorses** this development, **but we are not owning or actively maintaining this connector.**

  即官方文档页本身就是一个**转手指路页**，指向的正是本项目已判定停更的那个 msf4-0 仓库。
- 对比：真正由官方维护的 connector 是 **Odoo**——`freppledb/odoo/` 有 31 个文件、**4533 行 Python**，含 import/export 管理命令、migrations、views、tests，以及独立的 `doc/odoo-connector/` 文档章节。ERPNext 一行代码都没有。
- 另有一个通用骨架 `freppledb/erpconnection/`（`erp2frepple.py` / `frepple2erp.py`），`doc/erp-integration/generic-erp-connector.rst` 说明它是 "a **skeleton** piece of code that **needs to be tailored** to match your ERP data model"，实现方式是**直连 ERP 数据库跑 SQL、导出 CSV**。

**"Community 还是 Enterprise"这一问不成立**：connector 既不在 Community 也不在 Enterprise，它**是第三方的**。形态是**装在 ERPNext 侧的 Frappe app**（`bench get-app frepple https://github.com/msf4-0/ERPNext-Frepple-Integration.git`，见该仓库 README），而非 frePPLe 侧的模块。所以"Community 版 MIT 很宽松"**对 connector 这件事没有覆盖力**。

**第三方 connector 的实际状态**（GitHub API 查得 `pushed_at`）：

| 仓库 | 最后推送 | ★ |
|---|---|---|
| `msf4-0/ERPNext-Frepple-Integration`（官方文档指向的） | **2022-02-21** | 30 |
| `msf4-0/IRPS-Enhanced-Frepple-Integration` | 2022-09-04 | 1 |
| `msf4-0/ERPNext-Frepple-Enhanced-Integration` | 2022-10-04 | 3 |
| `msf4-0/ERPNext-Frepple-Enhanced-Integration-Version-1.3` | **2023-12-21** | 1 |

**对任务前提的一处修正**：任务背景称该 connector "停更 4 年半（2022-02-21）"——对官方文档指向的主仓库成立，但存在一个更新的分支 `Version-1.3`（2023-12-21），仍停更约 2 年 9 个月，且只有 1 star。**无论取哪一个都无人维护。**

**支持的 ERPNext 版本：未查实（倾向于"从未声明"）**。读过主仓库与 1.3 的 README，**通篇没有任何 ERPNext / Frappe 版本号声明**，只说 "Installed ERPNext and successfully launched it on the localhost"。同组织另有 `ERPNext_version-12_update-1.2` 仓库，**推断**其开发基线在 ERPNext v12–v14 时代。对 **v16.35.0 + Frappe 16.34.0 的兼容性无任何正面证据**。

**数据同步方向与粒度**（据 1.3 README 功能列表，未读代码）：

- ERPNext → 连接器：一键 import 数据（README 未逐项列出 Item/BOM/Workstation，**粒度未查实**）；
- 连接器 → frePPLe 软件：export，再在连接器内跑 plan（constraints 可配）；
- frePPLe → ERPNext：回写 **manufacturing orders / purchase orders / distribution orders**，并**双向同步 WO/PO 状态**；
- 另有 iframe 把 frePPLe 界面嵌进 ERPNext。

架构上它**在 ERPNext 里复刻了一套 frePPLe 的 doctype 做中转站**（README 自称 "middle station"，用于两边数据模型映射）。这是重资产设计：ERPNext 升级与 frePPLe 升级**两头都会震它**。

**API 调用方式（v1/v2、`/api/resource` vs `/api/method`）：未查实。** 未读 connector 源码（它不在本次克隆范围内）。按本项目已查明的 v1 路径仍可用这一事实，**即便它用老路径也不一定是障碍**——真正的风险在 doctype 字段与 ORM 行为的跨版本漂移，不在 URL 前缀。

## ③ 部署代价与 Windows Docker 复杂度增量

**读到的事实**：

- frePPLe 是独立服务：C++ 求解器（`src/model/` 下 `solver.cpp`、`resource.cpp`、`load.cpp` 等）+ Django + **PostgreSQL**。`contrib/docker/docker-compose.yml.in` 为两个容器：Apache webserver（映射 `9000:80`）+ `postgres:16`，两者各 `reservations: memory 4096M`。
- **`requirements.txt` 最后一行钉的是 frePPLe 自己 fork 的 Django**：`https://github.com/frePPLe/django/archive/refs/tags/frepple-9.18.tar.gz`。不是标准 Django，不能简单 pip 装，也意味着**升级受 frePPLe 节奏约束**。
- 官方另提供预构建镜像 `ghcr.io/frePPLe/frepple-community`（README "Download" 节），可绕过自行编译 C++ 这一大坑。

**增量评估（推断，基于本项目已记录的 Windows Docker 平台坑）**：+2 个容器、**+第二套 RDBMS（PostgreSQL 与现有 MariaDB 并存）**、名义 +8GB 内存预留、+1 个对外端口（9000，需对照 Windows 端口保留段核）。加上连接器本身要在 ERPNext 侧 `bench get-app`，即**同时改动 ERPNext 容器与新增 frePPLe 栈两侧**。复杂度增量属"中高"，但不涉及新的平台坑类别。

**能力侧一处关键限制（读到的事实，非推断）**：`doc/model-reference/setup-matrices.rst:5-15` 明写——Community Edition 的求解器**尊重**换型矩阵，但 "**does NOT do any effort to reduce the setup times**"，且 "does NOT have all logic to handle the complexities of propagating setup changes. **Your mileage will vary.**" 换型优化要靠 Enterprise 的高级求解器。另 `doc/modeling-wizard/inventory-planning/index.rst:7`：库存计划**仅 Enterprise**。

对弹簧制造尤其要紧：**换型（线径/卷簧机调机）优化正是该行业痛点，而这恰好落在 Community 版明确声明不做的那一格。** frePPLe Community 能给我们的是真正的有限产能排产（资源/负荷/换型矩阵被尊重），**但不是换型最优化**。

## ④ 一句话结论

frePPLe Community 的许可证干净（MIT，商业售卖无障碍）、有限产能模型是真的、项目今天还在提交，**技术上确实能补上 ERPNext v16 缺失的 CRP**；但**最主要的反对理由是：frePPLe 官方根本没有 ERPNext connector——官方文档页只有 9 行、把人转手指向第三方，而那个第三方（含其最新 1.3 分支）已停更 2 年 9 个月至 4 年半、1–30 star、从未声明支持任何 ERPNext 版本，对 v16 更无一字**；走这条路等于**我们自己从零承接并长期维护这套集成**（官方唯一可参照的样板是 4533 行的 Odoo connector，以及一个要自己填 SQL 的通用骨架）。

## ⑤ 拿不准 / 未查实

1. **connector 的 API 调用方式与 v16 兼容性细节**——未克隆 msf4-0 仓库、未读其源码。URL 前缀不是主要风险，doctype 字段漂移才是，但**两者都没验**。
2. **同步粒度是否覆盖 Workstation / Routing / Operation**——这决定它能否真正喂出 CRP。只读到 README 的功能标题，**未见字段级清单**。若它只同步 Item/BOM 而不同步工作站与工艺路线，则 CRP 补不上。**这是下一步最该验的一条。**
3. **frepple.com 官方文档站未能直接抓取**（WebFetch 报域名无法校验为安全，被网络策略拦）。已用仓库内 `doc/` 源文件替代——`doc/erp-integration/erpnext-connector.rst` 就是该文档页（9.19.0）的源码，**故文档与代码此处并无冲突：文档自己就承认没有官方 connector**。但官网页面上是否另有版本声明或 Enterprise 标注，未直接目视。
4. **`src/model/` 下 C++ 有限产能逻辑只看了文件名与文档描述，未读实现**。"产能约束是真的"这一条依据是文件存在 + `setup-matrices.rst` 的行为描述，**不是代码级验证**。
5. **Windows Docker 下 PostgreSQL 与 MariaDB 并存、9000 端口是否落在保留段**——未实测。
