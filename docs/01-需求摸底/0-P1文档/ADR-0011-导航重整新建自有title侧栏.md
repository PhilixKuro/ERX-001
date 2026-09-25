# ADR-0011: 导航重整——新建自有 title 侧栏，erpnext 原有 22 份一份不改

- 状态：accepted
- 日期：2026-09-25 / 决策者：用户裁决（C 步第 14 步①），Claude 提选项（含本步新开出的 D 案）
- 对应决策：DEC-062

## 上下文

CR-010 要求把导航按本项目的业务流重排，并折叠四个第三方 App 带来的无关入口。erpnext 自带 22 份 `Workspace Sidebar` 记录。

V-15 已证改 `standard=1` 的导航记录后跑 `bench migrate` 不被覆盖回原值（三张表都不被覆盖）。但 V-17（自有 app 出同名侧栏 json 时谁赢）**未验**。

## 决策

**新建自有 `sidebar_title` 的侧栏，erpnext 原有 22 份一份不改。** 直接改 DB 记录（A 案）降为开发期手段——试排布时可以直接改，定稿后落成 app 内的 json。

## 后果

**正面**
- 用自有 title 故**不依赖 V-17**（同名冲突谁赢未验），把一个未验项从关键路径上拿掉。
- 不污染上游 fork：A 案在 `developer_mode=1` 下会改写 erpnext 的 json 文件。
- **`sidebar.js:709-744` 的 `resolve_sidebar()` 四级规则第 1 条是「当前侧栏已链接到该实体则保持不变」** ⇒ 自有侧栏列全 23 环节的 DocType 后，演示全程侧栏不跳走。**这是本决策的直接收益，也是取 D 案而非其他案的实质理由。**

**负面**
- 自有侧栏要自己列全 23 个环节的 DocType，漏一个就会在那一步跳走。
- erpnext 原有 22 份仍在，CR-010 的「折叠噪音」要靠入口层面解决（见下）而非删记录。

**中性**
- **一处更正（C 步第 14 步②更正第 12 步）：D 案不需要同名 `Workspace`、也不需要 `Module Def`。** boot 侧把全部 `Workspace Sidebar` 记录装进 `sidebar_items`，键为 `sidebar_title.lower()`（`boot.py:446` + `:507`）；前端按 `workspace_title = sidebar_title.toLowerCase()` 取（`sidebar.js:286`、`:31`）；`workspace_sidebar/` 与 `desktop_icon/` 都是 **app 级目录**（`sync.py:120` 的 `app_level_folders`），不是模块内目录。**真正需要另行提供的是入口**（`Desktop Icon`）。
- 大小写约定：boot 键全小写，`label` 保留原大小写。
- **label 保持英文源词，由 csv 去译**（`boot.py:465` 是 `"label": _(item.label)`）——这是 CR-002 → CR-010 硬次序的源码确证：译名不齐则导航重整出来的是英文。

## 备选方案

**A 直接改 DB 记录** —— 最直接，改完即见效。**降为开发期手段**（不是否决）：`developer_mode=1` 下改 `standard=1` 的记录会改写 erpnext 的 json 文件，污染上游 fork。试排布阶段用它，定稿后落成 app 内 json。

**自有 app 出与 erpnext 同名的侧栏 json** —— 覆盖原有分组，客户看到的就是重排后的。**没选**：押在 V-17 未验项上（`sync.py:120` 按 app 逐个扫，同名冲突时谁赢取决于扫描顺序与 `modified` 判据的交互）；而 `boot.py:446-457` 按 name 取 ⇒ 同名即同一条，是「覆盖」而非「并存」。取 D 案用自有 title 即绕开。见 NV-044。

**重排 `Workspace` 让 `Desktop Icon` 重新生成** —— 借上游机制，不必自己建记录。**没选**：只影响首页图标网格，**不影响 `Workspace Sidebar`**（V-15 已证两者同为 json 导入路径但各是各的记录）；解决不了「按业务流重排侧栏」这个主需求。见 NV-045。

## 关联

- 依赖：ADR-0006（label 由 csv 去译，故 CR-002 须先于 CR-010）、ADR-0009（开发期用注入脚本试排布）
- 被依赖：CR-010
- 取代：无

## 失效条件

若需求改为「保留 erpnext 原有分组并各自重排」。
