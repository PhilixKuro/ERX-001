# ADR-0006: 译名全走 csv 单一来源，`Translation` 降为开发期草稿纸

- 状态：accepted（**2026-09-28 补充两条机制事实**，决策本体不变，见文末「补充」与「修订记录」。文中 `erx_core` 自 [ADR-0013](ADR-0013-自有app按域分为frappe_china与frappe_debug.md) 起读作 **`frappe_china`**）
- 日期：2026-09-25 / 决策者：**用户推翻 A 案前提** → Claude 改判（C 步第 7 步）
- 对应决策：DEC-057

## 上下文

CR-002 要求界面译名全量无缺口。Frappe 有两档译名机制：app 内 `translations/{lang}.csv`（`translate.py:179`，后装的 app 覆盖先装的）与 `Translation` DocType 记录（`translate.py:155-158`，在全部 app 之后 update，故优先级最高）。

Claude 原推 A 案「两档并用」——csv 做批量基线、`Translation` 做精修与撞名裁决，理由是客户现场可自助改译名。**用户推翻了该案的三条前提**：① 客户不改译名；② 现场可改这个能力只为开发期便利，不强求；③ 终态是内置形式。

前提被推翻后 Claude 改判。改判时另查出一条机制事实，使 A 案的缓解措施在机制上做不到：**csv 不支持注释、也不支持第四列**（`translate.py:196-219` 只认 2 或 3 列，长度 1 或 ≥4 落进 `elif item:` 被记成 "Bad translation"），故「双层歧义在 csv 内标注消解」这个设想无法实现。

## 决策

译名**全走 `erx_core/translations/zh.csv` 单一来源**。`Translation` DocType 降为开发期草稿纸——可以用它试译法，但**用后即删**，并配一条自检纪律：**演示前与交付前断言 `Translation` 表为空**。

## 后果

**正面**
- 单一来源，同一个词只有一处定义，不存在两层优先级的歧义。
- csv 在 git 里可 diff、可 review，译名演进史可查。
- 配 IM-007 的 `after_migrate` 自检守住「`Translation` 表为空」，双层不会悄悄回来。

**负面**
- 失去「客户现场自助改译名」这个能力。按用户推翻的前提①②，这不是损失。
- 改译名须改 csv 并跑一次 `bench build`／migrate，开发期比直接改 DB 记录慢一档。

**中性**
- **本 app 每语言只有一个 csv**（`translate.py:190-193` 路径拼死），故全部译名挤在一份文件里。文件会长，且无法用注释分区（csv 不支持注释）。分区只能靠行序与前缀词，属实现约定。

**一条随本决策生效的硬纪律：自有 app 内只放 csv，不放 po／不生成 mo。** 依据 `translate.py:180-181` —— **同一个 app 内的装载次序是先 csv 后 mo**，即自有 app 一旦生成 mo 文件就会**盖掉自己的 csv**。这不是跨 app 的 `[-1]` 竞争（那条见 ADR-0003），是同 app 内后者胜出，与装载顺序无关，故末位装载救不了它。**因此 `erx_core` 的构建流程里不得出现 `bench` 的编译译名动作**，须写进 app 的 README 与交付检查表。

## 备选方案

**A 译名两档并用**（csv 做批量基线 + `Translation` 做精修与撞名裁决）—— 现场可改、可标注撞名裁决理由。**没选**：用户推翻其前提后只剩开发期便利，而代价是常设双层；且**其缓解措施机制上做不到**——csv 不支持注释也不支持第四列，双层歧义无法在 csv 内标注消解；A 还等于先建双层再并回一层，而迁移会掉条目。见 NV-035。

**译名全走 `Translation` 记录 + fixtures** —— 全在 DB 里，改完即生效。**没选**：4813 个 doc；**且 fixtures 是强制覆盖语义**（`data_import.py:362`）⇒ 客户现场改的译名下次 migrate 被抹回，**与「现场可改」这个优点自相矛盾**。见 NV-036。

## 关联

- 依赖：ADR-0003（译名 csv 的 `[-1]` 归 `erx_core` 是本案可行的前提）、ADR-0005（本案是「按语义分派」的一个实例）
- 被依赖：ADR-0009（导航重整时 label 保持英文源词、由 csv 去译）
- 取代：无

## 失效条件

若将来需要「客户现场自助改译名」这个能力。

## 补充（2026-09-28）

两条机制事实，出自 P1-S4-R1 A 步第 6 步议题 ③（丁调查，A 步核实）。**不改变决策**，但约束 CR-002 的做法与本决策那条自检纪律的读法。

**① Property Setter 改 `label` 与 csv 译名是叠加，不是旁路。** `meta.py:446-449` 先把 Property Setter 的新 `label` 写进 meta；前端一律 `__(df.label, null, df.parent)` 读改写后的值（`base_input.js:200`、`column.js:33`、`grid_row.js:550` 等），Python 侧 `get_translated_label()` 同理（`meta.py:314-319`）。即**先改源词、再拿改后的源词查 csv**。

- 推论：同一个英文词在不同 DocType 里要译法不同，**用 csv 第三列 `context` 即可**（`translate.py:207-209` 把 3 列行的键拼成 `源词:context`，与读取端 `f"{msg}:{context}"` 严格对应），**不必借 Property Setter 改英文源词**。
- 判据（DEC-105）：改名是为了让中文说得对 → csv；是为了让这个格子装另一样东西（业务语义变了）→ Property Setter。zelin 那 25 条 `label` 覆盖按此分四批，由 S6 的 CR-002 消费。

**② 「自定义表单」改 DocType 名会隐式写一条 `Translation`。** 管理员在「自定义表单」里给 DocType 改标签时，frappe 不写 Property Setter，而是 `insert` 一条 `Translation` 记录（`customize_form.py:201-209`；`label` 只在 `docfield_properties` 里，`doctype_properties` 无 `label`）。

- 后果：**会触发本决策「演示前与交付前断言 `Translation` 表为空」那条自检**，而改的人不知道自己写了翻译记录。
- 读法：该自检报出非空时，先查记录的 `source_text` 是否为 DocType 名——若是，来源是「自定义表单」，处置是把该译名移进 csv、删掉记录，**而不是判定有人绕过了单一来源**。自检的报错文案宜点明这一来源（形态留 S6 的开发方案）。

## 修订记录

| 日期 | 改了什么 | 来源 |
|---|---|---|
| 2026-09-28 | 头部加 `erx_core` → `frappe_china` 的读法指针；新增「补充」节两条机制事实。决策、后果、备选方案原文不动 | P1-S4-R1 A 步第 6 步 ③（缺口清单 #17）；P1-S4-R6 B 步落成 |
