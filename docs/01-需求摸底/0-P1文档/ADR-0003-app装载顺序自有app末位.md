# ADR-0003: App 装载顺序——自有 app 末位

- 状态：accepted
- 日期：2026-09-25 / 决策者：用户裁决（C 步第 5 步①），Claude 提选项
- 对应决策：DEC-054

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

装载顺序定为 **`frappe → erpnext → CRM → HRMS → Insights → Raven → erx_core`**，即自有 app 末位。四处 `[-1]` 全归 `erx_core`。

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

- 依赖：ADR-0001、ADR-0002
- 被依赖：ADR-0004（不用类覆盖这条约束的前提是类覆盖的 `[-1]` 归我们）、ADR-0006（译名 csv 的 `[-1]`）、ADR-0007（whitelisted 覆盖的 `[-1]`）
- 取代：无

## 失效条件

将来装任何新 app 会夺走末位——这正是 IM-007 自检要守的。
