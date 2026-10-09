# P1-S6 开发方案 · Part1：译名基线、译名守卫、底稿改名、S4 小缺陷

**来源需求**：[B 需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) §4.2.1、§4.2.4（`PH-P1052`）、§4.3、§4.5、§4.8.1（需求 TS-001／002／006／010）｜**前置依赖**：无｜**日期**：2026-10-09｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S6-R3-C开发方案-总纲.md](P1-S6-R3-C开发方案-总纲.md)（执行纪律见总纲 §九，本 Part 不重复）

## 接口契约

```python
# ---- Spike/P1S6R4-baseline.py ——译名基线（只读，宿主上在 frappe-bench/ 下跑） ----
# 用法：PYTHONUTF8=1 python -I ../Spike/P1S6R4-baseline.py [--out ../Spike/P1S6R4-baseline.out.json]
APPS: tuple[str, ...] = ("frappe", "erpnext", "crm", "hrms", "insights", "raven", "frappe_china")  # 取站点 installed_apps 的顺序

def parse_po(path) -> list[Entry]          # Entry = (msgid, msgctxt|None, msgstr, refs:list[str])；复用 P1S6R1-merged-collisions.py 的 parse
def parse_csv(path) -> dict[str, str]      # 键：两列行为源词，三列行为 "源词:context"（同 translate.py:207-211）
def merged_dict() -> dict[str, str]        # 按 APPS 顺序叠加各 app 的 zh.po 与 csv，后者覆盖前者
def gaps() -> dict[str, list[Gap]]         # 每 app：main.pot 里 (msgid, msgctxt) 在 merged_dict 中查不到中文的条目，带 #: 出处
def collisions() -> dict[str, list[str]]   # 目标词（去首尾空白）→ ≥2 个无 context 源词
def demo_surface() -> dict[str, list[str]] # 源词 → 出处列表（四部分并集，见 TS-001 第 2 步）
def demo_collisions() -> dict[str, list[str]]  # collisions() 中 ≥2 个源词落在 demo_surface 的组
def official_overrides() -> list[tuple[str, str, str, str]]  # csv 覆盖了六个 app 官方 zh.po 的键：(键, 官方 app, 官方译文, csv 译文)
```

```python
# ---- frappe_china/translation_check.py（新增）——译名自检（总纲 A1、A2） ----
def find_problems() -> list[str]:
    """四项检查，返回问题清单（每条一句中文，含定位信息），空即通过。纯查询，不写库、不写文件。
    1. Translation 表：每条记录一行「Translation 记录：<源词> → <译文>（语言 <lang>，<owner>，<creation>）」；
       清单末尾附一次提示「在『自定义表单』里改过单据显示名时框架会隐式写一条（customize_form.py:201-209）」。
    2. .mo：frappe.get_app_path("frappe_china") 下 rglob("*.mo") ∪ get_mo_path("frappe_china", 每个 locale 目录)
       存在的文件，每个一行，附「同一 app 内 .mo 覆盖 .csv」。
    3. .po：frappe.get_app_path("frappe_china") 下 rglob("*.po")，每个一行，附「bench build 会把它编成 .mo」。
    4. 法定列头：validate_legal_labels() 返回的每个列头一行「<列头> 被译为 <_(列头)>」。"""

def run() -> list[str]:
    """供 bench --site <站> execute frappe_china.translation_check.run。
    打印「译名自检通过」或逐条问题，返回 find_problems() 的结果。不 throw（让调用方看到全部问题）。"""
```

```python
# ---- frappe_china/accounting/statements/labels.py（改） ----
def validate_legal_labels() -> list[str]:
    """不变：返回被翻译了的法定列头。
    改动只在取 Cash Flow Code 那段：except 收窄为「库未就绪」——
    frappe.db 未连接（getattr(frappe.local, "db", None) is None）时跳过取数；
    其余异常照常抛出（PH-P1030）。"""
```

```python
# ---- frappe_china/tests/translation_overrides.py（新增）——覆盖清单（总纲 A3） ----
class Override(NamedTuple):
    official: str   # 被覆盖的官方译文（取自该 app 的 zh.po；多个 app 都有时取合并后生效的那条）
    ours: str       # 本 app csv 里的译文
    basis: str      # "DEC-0xx" / "S3 术语标准 §x.x" / "演示线撞名：<目标词>" / "按钮抽检" 之一，可多个以「；」分隔

OVERRIDES: dict[str, Override]   # 键与 csv 键同形；Part1 TS-003 建空骨架＋已知条目，Part2 各任务逐条追加
```

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-001** 译名守卫 | 需求 TS-001／002；DEC-010／013；`PH-P1030`；需求 §4.2.1、§4.3 | ① 基线脚本在锁定 commit 上跑出 `P1S6R4-baseline.out.json`，含每 app 缺口数与清单、合并撞名组数、演示线撞名组清单、官方覆盖清单；缺口合计数写进 D 回执，与 5338 不同时写明差在哪个 app。② 测试站 `bench --site test.localhost execute frappe_china.translation_check.run` 打印「译名自检通过」、返回 `[]`。③ 四项反证各有一个用例且通过：事务内插一条 `Translation` → 清单含该源词；app 包目录下临时放 `x.mo` → 清单含该路径；临时放 `x.po` → 同；临时插一条把「资产」译成别的词的 `Translation`（或临时给 csv 缓存注入）→ 清单含「资产」。用例结束后临时文件与记录均已不在（用例内断言）。④ `labels.py` 在 `frappe.local.db` 为 `None` 时不抛错且不取 `Cash Flow Code`；`frappe.get_all` 抛出非连接类异常（如 `frappe.DoesNotExistError`，用 `patch` 注入）时**照常抛出**。⑤ `test_translations.py`：官方交集断言改为「交集 ⊆ `OVERRIDES` 的键」，比对范围六个 app；新增「`OVERRIDES` 每个键在 csv 中存在且译文等于 `ours`」「`OVERRIDES` 每条的 `official` 等于该键在六个 app 官方字典里的现值」「csv 无重复键」「csv 每行 2 或 3 列」四个用例，均通过。⑥ 异常路径：往 csv 尾部临时追加一条与已有键重复的行（用例内对 csv 文本做，不落盘：直接对解析函数喂文本）→「无重复键」用例能报出该键 |
| **SL-002** 底稿改名 | 需求 TS-006；DEC-015；`PH-P1060`；需求 §4.5 | ① 测试站改名前造一条草稿底稿（含 ≥1 行 `Cash Flow Item`），`bench --site test.localhost migrate` 成功；之后 `tabCash Flow Worksheet` 有该记录、`tabCash Flow` 不存在、该记录的 `Cash Flow Item` 行 `parenttype='Cash Flow Worksheet'`；`/desk/cash-flow-worksheet/<name>` 能打开。② `frappe_china` 内 `grep -rn '"Cash Flow"'`（排除 `Cash Flow Code/Item/Subtotal`、`Cash Flow Statement` 类报表名）零命中。③ 搜索栏输入「现金流量」：底稿显示「现金流量底稿」、原生报表显示「现金流量表」、自有报表显示「小企业现金流量表」（截图）。④ `test_cash_flow`、`test_statement_dataset`、`test_translations` 全过。⑤ 异常路径：补丁在**已改过名**的站上再跑一次（`bench execute` 直调补丁函数）不报错、不改任何东西；在全新装站路径上（测试中调用补丁函数时 `tabCash Flow` 不存在）直接返回 |
| **SL-003** S4 小缺陷与分隔符 | 需求 TS-010；`PH-P1035`／`1041`／`1042`／`1063`／`1052`；需求 §4.2.4、§4.8.1 | ① 结转「取消」确认框写出公司、财年与月份（前后截图）。② 漏科目检查 `balance_or_movement` 列带 `options: "currency"`、每行带 `currency`（测试断言）；界面上金额带 ¥（截图）。③ 底稿已提交、已取消时不显示「获取现金流明细」按钮（`depends_on` 断言＋截图）；草稿上点了之后表单标脏、「保存」可点（截图）。④ 明细为空、当月有现金流水时保存，报「请先点『获取现金流明细』再保存」类提示（测试断言消息）；明细不空但余额不符时仍报原来那句（测试断言）。⑤ 分隔符：zh 下 `_incomplete_detail` 输出用「；」、en 下用「; 」（测试分别设 `frappe.local.lang`）；生成结转的成功消息 zh 下用「；」、en 下用「; 」；csv 中不再有两列行 `"{0}; {1}"`。⑥ 异常路径：底稿未填公司或月份时按钮不显示（`depends_on` 原条件保留） |

**执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。**

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-001 基线脚本 | SL-001 | 否（TS-006 用它的输出） |
| TS-002 自检函数与 `labels.py` 收窄 | SL-001 | 否 |
| TS-003 测试改造与覆盖清单 | SL-001 | 否（依赖 TS-002） |
| TS-004 底稿改名与补丁 | SL-002 | 与 Part2 TS-009 可并行（总纲 §七 ②） |
| TS-005 S4 四处小缺陷与分隔符 | SL-003 | 否（改 TS-004 改名后的底稿文件） |

---

## 任务 TS-001：译名基线脚本（对应 SL-001）

### 目标
一个可复跑的脚本给出缺口、撞名、演示线面与官方覆盖四份清单，作 Part2 各任务的输入与 AC-006 的判据。

### 具体改动
新增 `Spike/P1S6R4-baseline.py`（只读），复用 [Spike/P1S6R1-merged-collisions.py](../../../../Spike/P1S6R1-merged-collisions.py) 的 `parse`，按接口契约实现。关键算法：

1. **缺口**：
   ```
   merged = merged_dict()            # 含无 context 与 "源词:ctx" 两类键
   for app in APPS[:-1]:
       for (id, ctx, refs) in parse_pot(apps/{app}/{app}/locale/main.pot):
           key = f"{id}:{ctx}" if ctx else id
           zh = merged.get(key) or merged.get(id)        # 同 translate.js:5-18 的回退
           if not zh or zh == id: gaps[app].append((key, refs))
   ```
   **`raven` 只有 `main.pot`、没有 `zh.po`**——缺口照常算，官方字典里它贡献 0 条。
2. **演示线面**（需求 §4.2.2 四部分）：
   - 部分 1：`DEMO_DOCTYPES`（从 [Spike/P1S3R1-po-demoline-direct.py](../../../../Spike/P1S3R1-po-demoline-direct.py) `import` 或复制，38 个）＋ `Routing`、`Employee` ＋ `Month End Closing Voucher`、`Cash Flow Worksheet`（改名前跑则用 `Cash Flow`）、`Bank Statement Preprocess`，展开 `Table` 子表；每个 DocType 取 json 的 `name`、字段 `label`、`Select` 选项、同目录 `{name}.js`／`{name}_list.js` 的 `__("…")` 字面量（S3 DEC-076 三判据，复用该脚本的 `harvest`）。
   - 部分 2：`crm/frontend/src/pages/{Lead,Leads,Deal,Deals,Dashboard}.vue` 及其 `import` 的 `components/` 文件（只追一层）、`raven/apps/web/src/components/features/{cmdk,settings/ai}` 下文件中的 `__("…")`／`_("…")` 字面量。
   - 部分 3：`erpnext/erpnext/workspace_sidebar/*.json` 全部 `label`；`*/*/desktop_icon/*.json` 的 `label`；本 Stage 自有侧栏与图标的 `label`（Part3 TS-010 之后重跑时才有）。
   - 部分 4：需求 §4.2.4 表的源词（脚本内常量）。
   - **LG-009**：脚本另输出「操作稿环节里打开、但不在部分 1 的 DocType」——取 `最小闭环操作稿.md` 中形如 `` `Xxx` `` 且是 DocType 名的词，与部分 1 求差；差集写进 D 回执（预期至少含 S3 的 39 与 38 之差那一个）。
3. **撞名**：`collisions()` 只取无 context 键、目标词 `strip()` 后归并；`demo_collisions()` 取组内 ≥2 源词在 `demo_surface` 里的组。
4. **官方覆盖**：csv 键 ∩ 六个 app 各自 `zh.po`（含 msgctxt 键），列出官方译文与 csv 译文。
5. 输出 `Spike/P1S6R4-baseline.out.json`：`{"commits": {app: HEAD}, "gaps": {app: [[key, refs], …]}, "gap_counts": {…}, "collision_count": n, "demo_collisions": {…}, "demo_surface_count": n, "official_overrides": […], "lg009_missing_doctypes": […]}`；stdout 打印各计数。

`commits` 取各 app 目录 `git rev-parse HEAD`，D 回执与 `docker/apps.json` 的 commit 比对，不一致即暂停反馈（需求 §4.2.1 第 2 条要以锁定 commit 为准）。

### 验证方式
跑一次，回执记各 app 缺口数、合计、撞名组数、演示线撞名组数，与 A 步的 5338／905 对照说明差额来源。

---

## 任务 TS-002：自检函数与 `labels.py` 收窄（对应 SL-001）

### 目标
需求 §4.3 的四项自检，且第 4 项不再静默缩小范围。

### 具体改动
1. 新增 `frappe_china/translation_check.py`，按接口契约。第 2 项的 locale 目录用 `frappe.gettext.translate.get_locale_dir()` 列出 `*/LC_MESSAGES/frappe_china.mo`（总纲 A2）。第 1 项按 `creation` 升序列出，最多列 50 条、超出写「另有 N 条」。
2. 改 `frappe_china/accounting/statements/labels.py:36-43`：
   ```
   if getattr(frappe.local, "db", None) is None:   # app 发现阶段无库可连
       return sorted(...)                           # 只查静态列头
   labels.update(row.cash_flow_name for row in frappe.get_all("Cash Flow Code", ...))
   ```
   删掉 `try/except Exception: pass`。
3. 约定显式化：本任务确立「站点自检函数放 app 包顶层、`run()` 打印并返回清单、不 throw」——与 `realtime_check.run` 一致，D 回执「新增约定」节记一条。

### 验证方式
测试站 `bench --site test.localhost execute frappe_china.translation_check.run` 输出「译名自检通过」；演示站同一命令**只读**跑一次（不写库），结果记回执（预期通过；若不通过，记下、不在此时修演示站——留 Part4）。

---

## 任务 TS-003：测试改造与覆盖清单（对应 SL-001）

### 目标
需求 §4.3「测试改造」四条与四项反证落成用例。

### 具体改动
1. 新增 `frappe_china/tests/translation_overrides.py`，按接口契约。初始条目：现 csv 里与官方交集的键（TS-001 第 4 步的输出；按 `test_translations.py:131` 现状应为空，若不空逐条补依据）。
2. 新增 `frappe_china/tests/test_translation_check.py`：
   - `test_clean_site_passes`：`find_problems() == []`。
   - `test_translation_record_is_reported`：`frappe.get_doc({"doctype": "Translation", "language": "zh", "source_text": "_FCT probe", "translated_text": "探针"}).insert()` 后断言清单含 `_FCT probe`；`frappe.db.rollback()`；再断言清单为空。
   - `test_mo_and_po_files_are_reported`：在 `frappe.get_app_path("frappe_china")` 下建 `_fct_probe.mo`、`_fct_probe.po`，断言两路径都在清单；`finally` 删除并断言文件不在。另一用例在 `get_locale_dir()/zh/LC_MESSAGES/` 下临时放 `frappe_china.mo`（**先断言原本不存在**，存在则 `skipTest` 并写明原因，不覆盖真文件）。
   - `test_legal_label_translation_is_reported`：沿用 `test_statement_output.py:49-66` 的做法插 `Translation`（`资产` → `Assets`）后断言清单含「资产」，`finally` 删除。
   - `test_labels_skip_db_only_when_not_connected` 与 `test_labels_raise_other_errors`：`patch.object(frappe.local, "db", None)` 时不抛错；`patch("frappe.get_all", side_effect=frappe.DoesNotExistError)` 时 `assertRaises`。
3. 改 `frappe_china/tests/test_translations.py`：
   - `:126-132` 官方字典改为 `get_translations_from_apps("zh", apps=["frappe","erpnext","crm","hrms","insights","raven"])`，断言 `set(app_translations) & set(official) <= set(OVERRIDES)`，失败时报出多出的键。
   - 新增 `test_overrides_exist_in_csv`、`test_override_officials_are_current`（`official` 与现值不符即报「上游改了译文：<键>」——需求 §5.2「这是预期的提醒」）、`test_csv_has_no_duplicate_keys`、`test_csv_rows_have_two_or_three_columns`。后两条直接读 csv 文本（`csv.reader`），不经 `get_translations_from_csv`（它已把重复键合并掉）。
   - 「无重复键」的判别力反证：把检查写成纯函数 `_duplicate_keys(rows) -> list[str]`，另一用例喂含重复键的两行，断言能报出。
   - `REQUIRED_TRANSLATIONS` 的 `"{0}; {1}"` 一条随 TS-005 改，`"No submitted Cash Flow for this month"` 一条随 TS-004 改。
4. 现有 `test_every_app_source_string_has_chinese`（`:113-117`）保留不动。

### 验证方式
`bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_translation_check` 与 `…test_translations` 全过；回执记新增用例数。

---

## 任务 TS-004：现金流量底稿改名（对应 SL-002）

### 目标
`Cash Flow` → `Cash Flow Worksheet`，已有站点经 migrate 改名、新站直接建新名（需求 §4.5）。

### 具体改动
1. **先在测试站造数据**（改代码之前）：在 `HDTH` 之外的测试公司（用测试工具 `make_cn_company`）下建一条草稿 `Cash Flow`，调 `get_cash_flow_items()` 后保存（无现金流水时手工 `append` 一行 `Cash Flow Item`，`db_insert` 落库即可）。记下 `name`。
2. 目录 `cn_tax/doctype/cash_flow/` → `cn_tax/doctype/cash_flow_worksheet/`；文件改名 `cash_flow_worksheet.{json,py,js}`，`__init__.py` 随目录走。json：`name` 改新名、`amended_from.options` 改新名、**`modified` 调大**；py：`class CashFlowWorksheet`；js：`frappe.ui.form.on("Cash Flow Worksheet", …)`。
3. 全部引用改名（子 Agent grep 所得 8 个文件，执行时**重新 grep 一遍为准**）：`cash_flow_worksheet.py`（`:38/:61/:71/:170/:244` 等 `"Cash Flow"`）、`accounting/statements/cash_flow_statement.py:120/:133/:159`、`tests/dataset.py:345`、`tests/test_cash_flow.py:55/:99/:103/:168/:209/:211`、`tests/test_statement_dataset.py:253/:259/:268/:288`、`README.md:96-112` 的目录路径。
4. 新增补丁 `frappe_china/patches/s6_rename_cash_flow_worksheet.py`，登在 `patches.txt` 的 **`[pre_model_sync]`** 段（总纲 A10）：
   ```
   def execute():
       if not frappe.db.table_exists("Cash Flow") or frappe.db.exists("DocType", "Cash Flow Worksheet"):
           return
       frappe.rename_doc("DocType", "Cash Flow", "Cash Flow Worksheet", force=True)
       frappe.reload_doc("cn_tax", "doctype", "cash_flow_worksheet")
   ```
5. csv：加 `Cash Flow Worksheet,现金流量底稿`；源词含 `Cash Flow` 的 8 条消息——`:31`（`No submitted Cash Flow for this month`）、`:114`、`:117`、`:118`、`:119`、`:125`、`:126`、`:141`——**逐条看其 `_()` 调用处，指底稿这张单据的，源词改为 `Cash Flow Worksheet`**、译文不变，代码里对应的 `_()` 同步改（`cash_flow_statement.py:74/:163`、`cash_flow_worksheet.py:40/:68/:72/:172/:286/:292`）；指报表行或泛称现金流量的（如 `:114` `Cash Flow row {0} is missing` 若指报表行）不改，D 回执逐条记判定。`Cash Flow Items`（子表字段 label）、`Cash Flow Name`、`Cash Flow Type` **不改**（不是 DocType 名）。`REQUIRED_TRANSLATIONS` 里那一条随之改键。
6. `bench --site test.localhost migrate`，再 `clear-cache`。
7. 约定显式化：「自有 DocType 改名的补丁放 `pre_model_sync`、带两道幂等判断」记进 D 回执「新增约定」。

### 验证方式
SL-002 ①～⑤。⑤ 用一个测试用例覆盖：`execute()` 在新表已存在时直接返回（断言 `rename_doc` 未被调用，`patch`）。补丁对 HT-006 的验证结论写回执。

---

## 任务 TS-005：S4 四处小缺陷与分隔符（对应 SL-003）

### 目标
`PH-P1035`／`1041`／`1042`／`1063` 与 `PH-P1052`。

### 具体改动
1. **`PH-P1035`**：`cn_tax/doctype/month_end_closing_voucher/month_end_closing_voucher_list.js:47-48` 改为
   `__("Reverse all Month End Closing Vouchers of {0}, fiscal year {1}, month {2}?", [values.company, values.fiscal_year, values.month])`；csv 第 144 行换成新源词 `…,确定冲销 {0} {1} 财年第 {2} 月的全部结转凭证？`（旧源词行删掉）。
2. **`PH-P1041`**：`accounting/statements/unmapped.py:21` 加 `"options": "currency"`；`execute()` 里 `rows.append` 的字典加 `"currency": f.currency`（`f` 是 `balance_sheet._validate_filters` 的返回，已带 `currency`，`balance_sheet.py:59-65`）。
3. **`PH-P1042`**：
   - `cash_flow_worksheet.json` 按钮字段 `depends_on` 改为 `eval:doc.company&&doc.fiscal_year&&doc.month&&doc.docstatus==0`（`modified` 调大）。
   - `cash_flow_worksheet.js` 在 `frappe.ui.form.on` 里加按钮处理函数（有同名处理函数时框架改走它，`button.js:41-42`）：
     ```
     get_cash_flow_items(frm) {
         frm.call("get_cash_flow_items").then(() => { frm.dirty(); frm.refresh_fields(); });
     }
     ```
   - `tests/test_cash_flow.py:100` 的 `depends_on` 断言改为新串；`:101-102` 关于「按钮没有 JS 处理器」的注释改写为现状。
4. **`PH-P1063`**：`cash_flow_worksheet.py` 的余额比对（原 `:284-286`）前加一支：
   ```
   if not self.items and abs(monthly_net.get("22", 0.0) - ending) > 0.01:
       frappe.throw(_("No cash flow items yet. Click Get Cash Flow Items first, then save."))
   ```
   csv 加 `…,还没有现金流水明细。请先点「获取现金流明细」，再保存。`。明细不空时原报错不变（不改校验语义）。
5. **`PH-P1052`**（总纲 A12）：`accounting/closing.py` 加本地辅助
   ```
   def _join(parts: list[str]) -> str:
       # 逐对用带 context 的分隔符拼接；context 只给本 app 用，不占全局键 "{0}; {1}"
       return reduce(lambda a, b: _("{0}; {1}", context="Month End Closing Voucher").format(a, b), parts)
   ```
   `:171-172` 与 `:396` 两处都改用 `_join`。csv 第 25 行由两列改三列：`"{0}; {1}",{0}；{1},Month End Closing Voucher`。`test_translations.py:63` 的键改为 `"{0}; {1}:Month End Closing Voucher"`，`test_app_translations_…` 里取值处随之按带 context 的键取。
6. 新增或改的用例：`test_cash_flow` 加「明细为空时的提示」与「明细不空时原提示」两例；`test_closing` 加 zh／en 两种语言下的分隔符两例；`test_unmapped`（已存在）加列 `options` 与行 `currency` 断言。

### 验证方式
SL-003 ①～⑥。截图在测试站另起的 6787 端口服务上拍（总纲 §九第 4 条），放 `Spike/P1S6R4-S4fix-*.png`。`run-tests --module` 逐个跑 `test_cash_flow`／`test_closing`／`test_unmapped`／`test_translations` 全过。
