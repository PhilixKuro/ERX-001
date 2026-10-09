# P1-S6 开发方案 · Part2：演示线档、批量档、裸渲染点、按钮抽检

**来源需求**：[B 需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) §4.2.2～4.2.6、§4.4（需求 TS-003／004／005／007）＋ [C 讨论记录](P1-S6-R3-C讨论记录.md) DEC-020～022｜**前置依赖**：Part1 TS-001～004 已完成｜**日期**：2026-10-09｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S6-R3-C开发方案-总纲.md](P1-S6-R3-C开发方案-总纲.md)（执行纪律见总纲 §九，本 Part 不重复）

## 接口契约

```python
# ---- Spike/P1S6R4-occupancy.py ——占用核查（只读，复用 P1S6R4-baseline.py 的 merged_dict） ----
def occupants(target: str) -> list[str]
    """合并字典（含当前 csv）里译为 target（strip 后比较）的全部无 context 源词。"""
def check(source: str, candidate: str, synonyms: set[str] = frozenset()) -> tuple[bool, list[str]]
    """候选词可用 ⇔ occupants(candidate) ⊆ {source} ∪ synonyms。返回 (可用, 冲突源词列表)。
    命令行：python -I P1S6R4-occupancy.py "<源词>" "<候选>" [同义源词…]"""

# ---- Spike/P1S6R4-sample.py ——批量档分层抽检（只读） ----
SEED: Final = 20261009
def stratified_sample(batch: dict[str, list[str]], n: int = 100, floor: int = 5) -> list[tuple[str, str]]
    """batch：app → 该 app 批量档键列表。各 app 配额 = max(floor, round(n × 占比))，
    配额和超 n 时从配额最大的 app 依次减 1 直到等于 n；random.Random(SEED).sample 抽取。
    返回 [(app, 键)]，同时写 Spike/P1S6R4-sample.out.csv（列：app,键,出处,译文,判定,不可用原因——后两列留空待填）。"""
```

```javascript
// ---- frappe_china/public/js/invoice_list.js（新增，doctype_list_js 下发；总纲 A5、A11） ----
// 对 Sales Invoice／Purchase Invoice 各执行一次（文件按 DocType 分别注册，见 TS-008）。
// 包装 get_indicator：只改「按 status 返回」的那种返回值的文字，带上 DocType 作 context；
// 其余分支（On Hold、Temporarily on Hold、Debit Note Issued 等）原样返回。
function wrap_indicator(doctype) {}        // 幂等：settings.__frappe_china_wrapped 为真则跳过
// 包装 onload：标准筛选的 status 控件补 df.context = doctype，清 last_options 后 set_options()。
function wrap_status_filter(doctype) {}   // 同上，幂等

// ---- frappe_china/public/js/desk_patches.js（新增，app_include_js；总纲 A5） ----
// 替换 frappe.form.formatters.Select：context 取 df.parent，缺省取 doc.doctype；
// 查不到带 context 的键时 __() 自行回退到无 context 键（translate.js:5-18），对其余 Select 无影响。
frappe.form.formatters.Select = function (value, df, options, doc) {}
```

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-004** 演示线译名 | 需求 TS-003／007；DEC-002／003／014／016／019／020～022；`PH-P1011`／`1062`；需求 §4.2.2、§4.2.4、§4.4 | ① 基线脚本重跑：`demo_surface` 内缺口 0；`demo_collisions` 中每组要么已定为唯一用词（组内源词译文两两不同），要么在 D 回执「同义保留」表里有一行写明同义依据——两者之外 0 组。② §4.2.4 点名用词表逐行：合并字典（`clear-cache` 后 `get_all_translations("zh")`）里该键的值等于表中译文——写成测试 `test_named_terms` 断言，表行全覆盖（含 `Dr`→借方、`Setup`→基础设置、`Setup:Workstation`→调机、`Payment References`／`Payment Entry Reference`→核销明细、`Cash Flow Worksheet`→现金流量底稿、`Cash Flow`→现金流量表、`Item`→物料、三个 DEC-021 词、`Business Flow`→业务流程、S3 §1.1／§1.3 收付款方向全表）。③ `Timesheet` 全族：六个 app 官方 `zh.po` 中译文含「工时表」的条目，合并后**全部**不含「工时表」、改为「工时单」且其余字不变（测试逐条比对：`official.replace("工时表","工时单") == merged`）。④ S3 的 73 组改词逐组有占用重查结论（D 回执表：原定／冲突源词／改定，无冲突写「无」）。⑤ 覆盖清单：本切片写进 csv 的每条覆盖官方的行都在 `OVERRIDES` 里（Part1 交集用例自动守住）。⑥ 按钮抽检表 20–40 词（不在区间写原因），每词有「源码实际做什么（文件:行）」，定稿后判定全「一致」。⑦ 异常路径：用一个已被他词占用的候选词跑 `P1S6R4-occupancy.py`，脚本报「不可用」并列出占用者（回执贴输出）；`Dr` 落地后测试站称谓 `Dr` 显示「借方」（DEC-022 的已知代价，截图留证） |
| **SL-005** 全量无缺口 | 需求 TS-004；DEC-001／017；RW-05；需求 §4.2.3 | ① 基线脚本重跑：各 app 缺口合计 0，例外只许出现在测试侧 `UNTRANSLATED` 白名单（白名单新增项每项写理由，如编码名、品牌名 `Raven`）。② 分层抽检 100 条（`SEED=20261009`），抽检表每行有判定；不可用 ≤ 10 条；不可用条当场改、按错误类型回扫，回扫改了哪些条写进 D 回执。③ 批量译文三条判据之三自动核：全部批量行的占位符（`{0}`、`{}`、`%s`、`%(name)s`、`{name}`）多重集合与源词相同、HTML 标签序列相同——写成 `test_placeholders_preserved`，对 csv 全部行跑（不限批量档）。④ 异常路径：不可用 > 10 条时，回执有抽检表与错误类型分布，状态停在本任务、已报用户（RW-05），**不继续** TS-008 之后的任务 |
| **SL-006** 裸渲染点 | 需求 TS-005；`PH-P1010`；S3 LG-121；需求 §4.2.6 | ① 三条出路各有实测记录「做法／结果／证据」，含两条原定做法（`states`、Property Setter）的实测（总纲 A11）。② 测试站造一张未收款的销售发票与一张未付款的采购发票：销售发票列表徽标、列表「状态」筛选下拉、表单只读 `status` 显示「未收款」；采购发票三处显示「未付款」（各一张截图）。③ 采购发票置 `on_hold=1` 无 `release_date` 时列表徽标仍显示「暂停」类原文案（官方译文），不被改成「未付款」（截图）。④ 异常路径：撤掉 `invoice_list.js`（`hooks.py` 临时注释该行、`clear-cache`）后销售发票徽标回到「未付款」——证明是补丁起的作用；完后恢复。⑤ README「desk 前端覆盖登记」节有三行（`get_indicator` 包装、`onload` 包装、`formatters.Select` 替换），每行五栏齐全 |

**执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。**

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-006 演示线档 | SL-004 | 否（TS-007 沿用其术语） |
| TS-007 批量档与分层抽检 | SL-005 | 分块翻译可并行（总纲 §七 ①）；合并与抽检串行 |
| TS-008 裸渲染点三条出路 | SL-006 | 否 |
| TS-009 改数据按钮抽检 | SL-004 | 抽检读码与 Part1 TS-004 可并行；定稿写 csv 在 TS-006 之后 |

---

## 任务 TS-006：演示线档（对应 SL-004）

### 目标
演示线面逐条结合源码译、撞名逐组定词、点名用词全部落 csv（需求 §4.2.2、§4.2.4）。

### 具体改动

**csv 分段**（需求 §4.2.5 第 5 条，本方案定下这一种）：文件内分三段，段间不留空行（csv 不支持注释），每段内按源词（不区分大小写）排序：

| 段 | 内容 |
|---|---|
| 1 | 本 app 自有源词（现有 152 行，加 Part1 新增） |
| 2 | 演示线档（本任务与 TS-008／009 写入） |
| 3 | 批量档（TS-007 写入） |

段界由测试侧常量 `CSV_SECTIONS` 记录起始源词，`test_csv_sections_sorted` 断言段内有序——段界之外不承载语义。

**步骤**：

1. **重跑基线**（Part1 TS-001），取 `demo_surface` 内的缺口与 `demo_collisions`。
2. **点名用词先落**：按需求 §4.2.4 表与 DEC-021／022 写 csv，`Dr,借方`（DEC-022）、`Setup,基础设置`、`Setup,调机,Workstation`、`Payment References,核销明细`、`Payment Entry Reference,核销明细`、`Item,物料`、`Create Chart Of Accounts Based On,科目表建立方式`、`Disable Opening Balance Calculation,不计算期初余额`、`Closed Date,实际成交日期`、`Business Flow,业务流程`、`Master Data,基础资料`、`Finance,财务`、`AI Assistant,AI 分析助手`；收付款方向照 S3 术语标准 §1.1、§1.3 逐行落（带 context 的行用三列，context 为 DocType 名）。`Unpaid`／`Paid` 的 `Sales Invoice` context 行在本步就写，生效靠 TS-008。
   - **`Closed Date` 的范围**：先 grep 六个 app 的 `main.pot` 看 `Closed Date` 出处；若不止 CRM 一处，判断其余出处是否也是「实际成交／关闭日期」语义，不是的改用 context 行（CRM 字段的 DocType 名作 context），D 回执记判定。
3. **`Timesheet` 全族**（DEC-016）：脚本列出六个 app 官方 `zh.po` 里 `msgstr` 含「工时表」的全部条目（含 msgctxt），逐条生成 `源词,原译文.replace("工时表","工时单")`（有 context 的写三列）；条目数与需求所记 erpnext 22＋HRMS 7 不同时以实取为准、回执说明。全部进 `OVERRIDES`，依据 `DEC-016`。
4. **S3 的 73 组改词**：逐组用 `P1S6R4-occupancy.py` 重查候选词；无冲突照落，有冲突改定未占用词。全部写 csv、进 `OVERRIDES`（依据 `S3 术语标准 §2.3.x`）。
5. **新冒出的演示线撞名组**：逐组按 S3 DEC-075 二分——同义（单复数、大小写、全称缩写）共用一词不改，记入回执「同义保留」表；异义的给每个源词一个唯一用词，`occupancy` 核过再写。**DEC-020 的连带**：侧栏条目沿用官方名，但若该官方名本身属演示线撞名组的异义一方，照本步定词——已知一例：`Stock Ledger`（报表）与 `Stock Ledger Entry`（单据）同译「物料凭证」，二者异义（报表与分录），须给报表另定（候选「库存台账」，子 Agent 已核未占用）；类似地查 `Stock Balance`「库存余额(收发存汇总表)」与 `Stock Ledger Invariant Check`「物料凭证与会计凭证差异表」等同族是否连带要改，D 回执记判定。
6. **CRM 的 115 条覆盖**（需求 §4.2.2 规则 4）：默认接受；本步只处理与 S3 术语标准相抵或造成演示线新撞名的那几条，写回所需译法。
7. **演示线面其余缺口**：逐条看 `refs` 出处的源码定译文；术语一律对照 S3 术语标准与本任务已定的词。
8. **必改条目**（需求 §4.2.2「已知的必改条目」表）逐条核：`Accounts Setup`、`HR Setup`、`Is Sales Item`、CRM 的 `Create Quotation`／`View Customer`／`Add Row`／商机阶段名、Raven `Agents`／`Bot`、`Accounts Receivable`／`Debtors`／`Receivable`、`Opening & Closing`、`默认成品仓(收料仓)` 括注（定位其源词后改）。
9. 新增测试 `frappe_china/tests/test_named_terms.py`：表驱动，键 → 期望译文，覆盖 SL-004 ② 的全部行与 ③ 的工时单比对；设 `frappe.local.lang = "zh"`，`clear_cache()` 后取 `get_all_translations("zh")`。
10. 每批写完 `bench --site test.localhost clear-cache`；任务收尾跑一次 `translation_check.run`。

### 验证方式
SL-004 ①～⑤、⑦；`run-tests --module frappe_china.tests.test_named_terms` 与 `test_translations` 全过。

---

## 任务 TS-007：批量档与分层抽检（对应 SL-005）

### 目标
演示线面之外的缺口全部补齐，抽 100 条测可用率（需求 §4.2.3，DEC-017）。

### 具体改动
1. 重跑基线，取剩余缺口（应全为演示线外），按 app 分块，每块 ≤ 300 条，导出 `Spike/P1S6R4-batch/in-{app}-{nn}.json`（键、出处、源码上下文三行）。
2. 每块译成 `Spike/P1S6R4-batch/part-{app}-{nn}.csv`：给译者（主 Session 或子 Agent）同一份术语表——S3 术语标准定稿词、TS-006 已定的全部演示线词、§4.2.4 用词规则（「单据用单／凭证／底稿，表留给报表」）、占位符与 HTML 原样保留。**`raven` 的设置面板条目**（`components/features/settings` 下约 900 条）同样要译，不因「管理员才看到」跳过（DEC-001 全量）。
3. 主 Session 合并：每块先过三项机检——占位符与 HTML 一致（同 SL-005 ③ 的函数）、无空译、目标词不与法定列头同名——不过的块退回重译；合并进 csv 第 3 段。
4. `python -I Spike/P1S6R4-sample.py` 抽 100 条，逐条按需求 §4.2.3 三条判据判，填 `P1S6R4-sample.out.csv`。
5. 判定（DEC-017）：不可用 ≤ 10 → 当场改，并按错误类型回扫（如某句式、某个词）——回扫用脚本在第 3 段 grep 同类，改动条目列入回执；> 10 → **停下**，回执交抽检表与错误类型分布，暂停反馈用户。
6. `UNTRANSLATED` 白名单（`test_translations.py`）只收不该译的：编码名、品牌名（`Raven`、`Frappe`、`ERPNext`、`Insights` 等原样显示的）、纯符号；每项注释理由。
7. 新增 `test_placeholders_preserved`（SL-005 ③），对 csv 全部行跑。
8. 重跑基线确认缺口 0。

### 验证方式
SL-005 ①～④。回执记各 app 批量条数、抽检配额、不可用条数与类型、回扫条数。

---

## 任务 TS-008：裸渲染点三条出路（对应 SL-006）

### 目标
`Unpaid`／`Paid` 在销售发票的三处裸渲染点显示「未收款」「已收款」（需求 §4.2.6、§4.2.4）。

### 具体改动
1. **造数据**：测试站建一张提交未收款的销售发票、一张提交未付款的采购发票、一张 `on_hold=1` 的采购发票（`make_cn_company` 下）。
2. **出路 1（列表徽标）**：
   - 先实测原定做法：Customize Form 给 `Sales Invoice` 加一行 DocType State `Unpaid`／`orange`，看徽标文字与颜色、采购发票 `On Hold` 是否被盖（对采购发票同样加）。截图留证，**然后删掉这些行**。
   - 落地做法：`invoice_list.js` 的 `wrap_indicator(doctype)`：
     ```
     const s = frappe.listview_settings[doctype]; if (!s?.get_indicator || s.__frappe_china_wrapped) return;
     const orig = s.get_indicator;
     s.get_indicator = function (doc) {
         const r = orig.call(this, doc);
         if (r && r[2] === "status,=," + doc.status) r[0] = __(doc.status, null, doctype);
         return r;
     };
     s.__frappe_china_wrapped = true;
     ```
   - `hooks.py` 加 `doctype_list_js = {"Sales Invoice": "public/js/invoice_list.js", "Purchase Invoice": "public/js/invoice_list.js"}`；文件内按 `cur_list` 无法得知 DocType，故对两个 DocType 都调用一次（幂等标记保证重复下发无害）。
3. **出路 2（标准筛选下拉）**：
   - 先实测原定做法：建一条 Property Setter（`doc_type=Sales Invoice`、`field_name=status`、`property=context`、`value=Sales Invoice`），看下拉选项。留证后删除。
   - 落地做法：`invoice_list.js` 的 `wrap_status_filter(doctype)` 包 `onload`：调原 `onload` 后取 `listview.page.fields_dict.status`，有则 `f.df.context = doctype; f.last_options = null; f.set_options();`。
4. **出路 3（表单只读 `status`）**：`desk_patches.js` 替换 `frappe.form.formatters.Select`：
   ```
   const v = frappe.form.formatters.Data(value, df);
   const ctx = df?.parent || doc?.doctype;
   return ctx ? __(v, null, ctx) : __(v);
   ```
   `hooks.py` 的 `app_include_js` 由字符串改为列表 `["/assets/frappe_china/js/realtime_check.js", "/assets/frappe_china/js/desk_patches.js"]`。`bench build --app frappe_china` 后硬刷新看效果。
5. **出路 4（四张共享子表）**：不做，回执记「无解，保留 S3 中性词」。
6. 在 README 新增「desk 前端覆盖登记」节（总纲 A6），登三行；锁定 commit 写 `docker/apps.json` 当前 frappe／erpnext 的 commit 前 8 位。
7. 反证（SL-006 ④）：临时注释 `doctype_list_js` 行，`clear-cache`、硬刷新，截徽标回到「未付款」，恢复。

### 验证方式
SL-006 ①～⑤。任一出路不可行：该渲染点保留官方原译，回执写「不可行」与证据；三条全不可行不暂停（DEC-080 继续有效），但出路 3 若发现只能改 frappe 源码才能做到，**暂停报用户**（需求 §4.2.6）。

---

## 任务 TS-009：改数据按钮抽检（对应 SL-004）

### 目标
需求 §4.4：演示线 13 张主单据上会改数据的按钮，中文说的动作与源码实际做的事一致。

### 具体改动
1. 读码列按钮：13 张单据的 `erpnext/erpnext/**/doctype/{name}/{name}.js` 里 `add_custom_button(__("…"), …)`（含 `erpnext/public/js/controllers/` 下这些单据共用的控制器），加框架通用的保存／提交／取消／修订／删除（`frappe/public/js/frappe/form/toolbar.js` 中的源词）。
2. 筛「点了会改数据」的（需求 §4.4 的口径），去重按源词计，得 20–40 词。
3. 每词一行：源词／合并字典现译／源码里实际做什么（文件:行，写到被调方法或路由目标）／判定。
4. 不一致的定稿译名写 csv 第 2 段；同一源词在不同单据含义不同的用 context 行（context 为 DocType 名，仅在该按钮的 `__()` 有 context 时才有效——**`add_custom_button(__("X"))` 不带 context**，故此类只能改无 context 行，须先查该源词其余出处，改了不误导才改，否则回执记「不可分、保留」）。
5. 覆盖官方的行进 `OVERRIDES`，依据「按钮抽检」。
6. 抽检表作 D 回执附表（需求 §4.4「随 D 回执交付」）。

### 验证方式
SL-004 ⑥。定稿后 `test_named_terms` 补这些键。
