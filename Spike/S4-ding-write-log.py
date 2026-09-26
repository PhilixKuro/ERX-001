# -*- coding: utf-8 -*-
import io
out = r'D:\ERX-001\Spike\S4-丁-译名机制对比.md'
body = '''# S4-丁 译名机制对比（调查中，边查边记）

调查代号：丁 | 日期：2026-09-27 | 状态：**进行中**
环境已核实：frappe 16.34.0 / erpnext 16.35.0（读自 `frappe/__init__.py:58`、`erpnext/__init__.py`）

---

## 阶段性硬结论（已核实）

### 结论 1：zelin 的 25 条 label 覆盖，**全部是英文改英文，一条中文都没有**

这是本次最关键的事实。逐条比对 `Reference/zelin-tech-erpnext_china/erpnext_china/fixtures/property_setter.json`
的 25 条 `property=label` 记录与官方 DocType json 里的原始 label，结果：

- 英文 -> 英文：**25 条（100%）**
- 英文 -> 中文：**0 条**
- 中文 -> 中文：**0 条**

> 白话：zelin 这 25 条**根本不是在做中文翻译**。它们是把英文名改成另一个英文名，
> 比如把 Make 改成 Vihicle Maker、把 Weight 改成 Weightage。中文界面上看到的中文，
> 是这些新英文名再被翻译机制翻出来的。所以「这 25 条算不算译名」这个问题，
> 答案在事实层面已经很清楚：它们是**改源词**，不是**给源词配译文**。

### 结论 2：Property Setter 设的新 label **会再经过翻译机制**

已核实读取端：`frappe/public/js/frappe/form/base_input.js:200`、`column.js:33`、`button.js:84`、
`grid.js:72`、`grid_row.js:550/565/593/753` 等处一律写作 `__(this.df.label, null, this.df.parent)`。
`df.label` 已经是 Property Setter 改写后的值（`frappe/model/meta.py:428-449` 的
`apply_property_setters`，`DocField` 分支在 447 行把 `label` 直接 set 进 meta 的字段对象）。
Python 侧对应 `frappe/model/meta.py:314-319` 的 `get_translated_label`，写作
`_(self.get_label(fieldname), context=self.name)`。

**所以两者是叠加关系，不是旁路。** 顺序是：先 Property Setter 改源词，再拿改后的源词去查译名表。

> 白话：Property Setter 像是给一个零件改了个新的英文学名；翻译机制像是一本英汉词典。
> 系统先改学名，再拿新学名去查词典。**改完名字还得有人把新名字也写进词典**，
> 否则界面上就直接显示那个新英文名。这意味着 zelin 这 25 条**必须配套 25 条译名**才能显示中文，
> 它自己解决不了中文问题。

### 结论 3：`context` 的默认值是所属 DocType 名

读取端第三个参数传的是 `this.df.parent`（即字段所属的 DocType 名），Python 侧传的是 `context=self.name`。
csv 第三列、po 的 `msgctxt` 都落到同一个 `源词:context` 键上（`translate.py:206-207`、
`gettext/translate.py:370-373`）。

> 白话：同一个英文词在不同单据里可以译成不同中文，靠的就是这个「场景标签」，
> 而这个标签默认就是单据的名字。这意味着「Rate 在销售税里译税率、在物料里译单价」是做得到的。

---

## 优先级链（已核实，给 file:line）

装载全部发生在 `frappe/translate.py:135-166` 的 `get_all_translations()` -> `_merge_translations()`，
用 dict `update` 逐层覆盖，**后写的赢**：

| 次序 | 来源 | file:line |
|---|---|---|
| 1（最低） | 父语言 的 app csv + mo | `translate.py:150`（`get_translations_from_apps(parent_lang)`） |
| 2 | 本语言 的 app csv + mo | `translate.py:152` |
| 3 | 父语言 的 `Translation` 记录 | `translate.py:156` |
| 4 | 本语言 的 `Translation` 记录 | `translate.py:158` |
| 5（最高） | 国家名译文 `get_translated_countries()` | `translate.py:159` |

第 1、2 层内部再分两级（`translate.py:172-187` 的 `get_translations_from_apps`）：

- 按 `frappe.get_installed_apps()` 次序逐个 app `update`，**后装的 app 覆盖先装的**（`translate.py:180-181`）
- **同一个 app 内：先 csv 后 mo**（180 行 csv、181 行 mo）=> **mo 盖 csv**

ADR-0006 §「一条随本决策生效的硬纪律」所述与此**完全一致**，已核实无误。

---

## 待续

- [ ] Python 侧 `_()` 的实现位置与 context 处理
- [ ] 各机制多维对比表
- [ ] 第二部分子问题 3、4
'''
with io.open(out, 'w', encoding='utf-8', newline='\n') as f:
    f.write(body)
print('written:', out, len(body))
