# ADR-0003: App 装载顺序——自有 app 末位

- 状态：accepted（**2026-09-28 修订**，随 [ADR-0013](ADR-0013-自有app按域分为frappe_china与frappe_debug.md)：单 app 改两个 app 后，「决策」节改写为现行形态，原决策保留在该节末尾；其余各节原文不动，其中的 `erx_core` 读作 `frappe_china`。见文末「修订记录」）
- 日期：2026-09-25 / 决策者：用户裁决（C 步第 5 步①），Claude 提选项；2026-09-28 修订的顺序由用户在 P1-S4-R1 A 步第 8 步 ① 给出
- 对应决策：DEC-054；修订对应 DEC-109／DEC-113

## 上下文

四处独立机制都取 `installed_apps` 的顺序，而该顺序等于装载先后（`installer.py:379-383` 是 `installed_apps.append(app_name)` 后写回全局值）。四个第三方 App（CRM／HRMS／Insights／Raven）与自有 app 的相对位置因此是架构决策，不是操作细节。

四处机制逐一：

| 机制 | 源码位置 | 取值 |
|---|---|---|
| 区域覆盖 `regional_overrides` | `erpnext/__init__.py:152` | `[-1]` |
| whitelisted 方法覆盖 | `frappe/__init__.py:1577-1580` | `[-1]` |
| DocType 类覆盖 | `base_document.py:110-125` | `[-1]` |
| 译名 csv | `translate.py:179` | 后装的覆盖先装的 |

## 决策

**现行（2026-09-28 修订）**：装载顺序定为 **`frappe → erpnext → CRM → HRMS → Insights → Raven → frappe_china → frappe_debug`**。四处 `[-1]` **全归 `frappe_china`**。`frappe_debug` 虽在末位，但**不在四处机制里注册任何条目**，故一处也不夺。

- **`frappe_debug` 的守法约束**（由本修订推出）：不注册 `regional_overrides`／`override_whitelisted_methods`／`override_doctype_class`；它若带 `translations/zh.csv`，其中不得有与 `frappe_china` 同键的行。**它一旦注册了其中任何一项，就会因位于末位而赢下那一处。** 具体守法手段（如干脆不带 csv）留 S7 的开发方案。
- **交接约束**（DEC-113）：S5 新装的四个官方 app 会排到 `frappe_china` 之后。**S5 装完后须让 `frappe_china` 回到全部业务 app 之后，并实测覆盖生效。** ⚠ **「重装」不是一条命令能完成的**：`install-app --force` 对已装的 app 不改位置（`installer.py:319` 放行后仍走 `add_to_installed_apps`，`:381` 的守卫使其不再追加）。**手段留 S5 的 C 步定**：`bench uninstall-app` 会删掉该 app 模块下全部 DocType 并删表（`installer.py:548-553`），并删除挂在该模块下的记录（`:510-516`，凡带 `Module Def` 链接字段的 DocType 都算），现金流单据等数据随之丢失；另一条路是直接改 `installed_apps` 全局值，**未验证**。

**原决策（2026-09-25，已由上文取代，保留备查）**：装载顺序定为 `frappe → erpnext → CRM → HRMS → Insights → Raven → erx_core`，即自有 app 末位。四处 `[-1]` 全归 `erx_core`。

## 后果

**正面**
- 四处 `[-1]` 全部自己赢：区域覆盖、whitelisted 覆盖、类覆盖、译名 csv。CR-002 的「译名全量无缺口」因此可达。
- **位置一旦设定即稳定**——`add_to_installed_apps` 有 `if app_name not in installed_apps` 守卫，故第三方 app 升级重装**不改变它的位置**。

**负面**
- 将来装任何**新** app 都会追加到 `erx_core` 之后并夺走末位。**这正是 IM-007 升级后自检要守的第一件事。**

**中性**
- 该顺序是隐式约定，不体现在任何配置文件里，只体现在安装操作的先后。故它的守护完全依赖 IM-007 的自检，没有第二道防线。

## 备选方案

**B 自有 app 紧跟 erpnext 装**（在四个第三方 App 之前）—— 自有 app 先落位，后装的第三方 app 不影响它的模块加载。**没选，且是否决级缺点**：四处 `[-1]` 全部让给第三方 App，Raven／HRMS 的译名会盖掉自有 `zh.csv`，CR-002 的「全量无缺口」直接失守。见 NV-031。

**C 不规定顺序，靠 `Translation` 记录兜底** —— 不依赖装载顺序这个隐式约定。**没选**：只覆盖四处中的一处。`Translation` 能兜译名（`translate.py:155-158` 确实在全部 app 之后 update），但**兜不了 `regional_overrides` 与两种覆盖 hook**——那三处没有 DB 层逃生门；且 914 组撞名全靠 DB 记录意味着几千条记录进 fixtures，比 csv 难维护。见 NV-032。

## 关联

- 依赖：~~ADR-0001、ADR-0002~~ → **ADR-0013**（2026-09-28 起）
- 被依赖：ADR-0004（不用类覆盖这条约束的前提是类覆盖的 `[-1]` 归我们）、ADR-0006（译名 csv 的 `[-1]`）、ADR-0007（whitelisted 覆盖的 `[-1]`）
- 取代：无

## 失效条件

将来装任何新 app 会夺走 `frappe_china` 的位置——这正是 IM-007 自检要守的；**自检断言的对象由「`erx_core` 在末位」改为「`frappe_china` 在全部业务 app 之后，且其后只有 `frappe_debug`」**。另：`frappe_debug` 若注册了四处机制中的任一项（见上「守法约束」）。

## 修订记录

| 日期 | 改了什么 | 来源 |
|---|---|---|
| 2026-09-28 | 「决策」节改为两 app 的顺序与 `[-1]` 归属；补 `frappe_debug` 守法约束与 S5 交接约束（含 `--force` 不改位置、卸载即删表两条读码事实，**均未实测**）；「关联」「失效条件」随改。「上下文」「后果」「备选方案」原文不动 | P1-S4-R1 A 步第 8 步 ①②（用户裁决）；P1-S4-R6 B 步落成 |
