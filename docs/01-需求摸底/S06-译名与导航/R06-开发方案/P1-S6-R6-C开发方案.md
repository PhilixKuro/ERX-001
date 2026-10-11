# P1-S6 译名与导航 —— 开发方案（R6：E 报告回流修补）

**来源**：[R5 E 确认报告](../R05-确认/P1-S6-R5-E确认报告.md) 的 `出方案修` 各项——IT-005（含 IT-003、006～009、012）、IT-020（含 IT-021），及经 DEC-031／037 并入的 IT-010、011、022、025；本轮 [C 讨论记录](P1-S6-R6-C讨论记录.md) DEC-028～038。需求依据不变：[R2 B 需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) v1.0。
**日期**：2026-10-11｜**编写者**：Claude（Opus 5.5）｜**执行者**：Claude（S6 概况的偏离：D 步执行者由 CodeX 改为 Claude）
**状态值与复核建议**：不在本文件，见 [P1-S6-R6-C回执](P1-S6-R6-C回执.md)

> **与 R3 方案的关系**：R3 方案（[总纲](../R03-开发方案/P1-S6-R3-C开发方案-总纲.md)＋Part1～4）仍是 S6 的主方案，本方案只**补和改**下列各节点名的部分，其余照旧有效。总纲 §九执行纪律对本方案同样适用（第 3 条的回执命名改为本方案 §八）。
> **编号**：接 R3 续编——切片 `SL-011` 起、任务 `TS-016` 起、技术假设 `HT-016` 起。E 报告的 `IT-` 编号照引。
> **路径**：`frappe_china/…` 指 `frappe-bench/apps/frappe_china/frappe_china/…`；`Spike/…` 指主仓库根下 `Spike/`。

## 一、概述

**要做的事**：R4 批量档的译文整体不可用（实测 5852 行中 5325 行坏，C 讨论记录第 1 步 ⑬），故把批量档整批作废重译，并补上 R4 漏做的演示线定词、按钮抽检与逐屏核。具体：

1. 先立四道**质量守卫**（繁体、逐词直译、占位、中英混排）进测试，重建覆盖清单，修基线与占用脚本；
2. **csv 清场**：只留本 app 自有源词、点名用词与有决策依据的覆盖行，其余全部删除，全表按源词排序；
3. **演示线档**逐条定词（演示面上无官方译文的 527 个键），演示撞名 191 组逐组判，收付款方向全表与 73 组改词复查落 csv，按钮抽检重做；
4. **批量档**整批重译（约 5500 条），分层抽检 100 条；
5. **逐屏核 v2**：按 DEC-032～034 重定屏清单与判据，测试站反证整条链，演示站核完出新基准点。

**完成标准**：

1. 本方案各切片验收条件全部通过；
2. R3 方案中被本方案替换的验收条件（见 §六）以本方案为准，未替换的照 R3；
3. `frappe_china` 全量测试只增不减（R5 E 实跑 242 条为基线），Node 用例 29 条为基线；
4. 演示站最终状态同 R3 总纲 §一第 4 条，基准点为本轮新出的那一份。

## 二、关键架构决策（本方案新定）

| # | 决策 | 理由 |
|---|---|---|
| **A15** | **csv 的保留规则**（DEC-038）：只留四类行——① 本 app 自有源词（`_app_source_strings()` ∪ `REQUIRED_TRANSLATIONS` 的键）；② `NAMED_TERMS` 的键；③ 经 TS-017 判为「保留」的覆盖行；④ 本轮 TS-019～021 新写的行。其余在 TS-018 一次删掉 | 不靠检测器挑行，检测器漏掉的坏行不会留下来 |
| **A16** | **覆盖官方的批量行一律删除回落官方**，不重译 | 需求 §4.3「批量档补的是缺口、不覆盖官方」；R4 批量档覆盖官方的 190 行无任何决策依据 |
| **A17** | **四道质量守卫写成测试**，放新文件 `frappe_china/tests/test_translation_quality.py`，对 csv 全部行跑；例外只许出现在 `QUALITY_EXCEPTIONS`（键 → 理由） | E 报告：规则初筛、逐屏核、全量回归三道检查都没拦住坏译文；守卫进测试后，再次批量写入时当场失败 |
| **A18** | **繁体的判法**：译文含 GB2312 以外的汉字即判繁体 | 实测六个 app 官方 `zh.po` 的简体用字全部在 GB2312 内（0 个例外），而 R4 混入的 zh_TW 行有 1603 行命中，E 报告手列字集命中的 1397 行全部被覆盖（HT-016） |
| **A19** | **白名单拆成数据模块** `frappe_china/tests/translation_whitelist.py`：`UNTRANSLATED: dict[str, str]`（键 → 不译理由）；`test_translations.py` 与基线脚本都从这里读 | IT-006：白名单原先只作用于本 app 源词，基线脚本看不见 |
| **A20** | **csv 全表按源词排序**（不区分大小写，再按 context），不分段（DEC-030）；用例 `test_csv_sorted` 断言 | DEC-030；R3 Part2 TS-006 的三段规定与 `CSV_SECTIONS` 作废 |
| **A21** | **逐屏核 v2 的判据分三类**（DEC-033）：英文词、繁体字、`title` 属性中的英文与繁体；`aria-label` 不计。ERPNext 自带英文默认数据记在单独字段 `default_data`，**不使 pass 变假**，在核对表单列、进延迟需求 | DEC-033 |
| **A22** | **确认框只截不确认**：每个可提交 DocType 的「提交」「取消」确认框，截图后点「否」关闭（DEC-034） | 截确认框不改数据；取消的连带校验（已有下游单据时拒绝）发生在点「是」之后，与确认框文案无关 |

## 三、技术假设

| 编号 | 假设内容 | 状态 | 验证方式 | 不成立时 |
|---|---|---|---|---|
| HT-016 | 六个 app 官方 `zh.po` 的简体用字都在 GB2312 内，故「含 GB2312 外汉字」可作繁体判据 | **已验证**（C 步实跑：官方简体用字 1313 个，GB2312 外 0 个；见 C 回执） | — | — |
| HT-017 | csv 源词带首尾空白时（如 `Role Allowed to over bill `）照原样作键生效：`get_translation_dict_from_file` 只 strip 译文、不 strip 源词 | 读码（`frappe/translate.py:203-211`） | TS-019 第 6 步：测试站打开 `Accounts Settings` 看该字段 label 显示中文 | 不暂停：该键进白名单并写理由「上游 label 带尾空格，csv 键配不上」 |
| HT-018 | 子 Agent 分块重译、主 Session 合并后，分层抽检不可用 ≤ 10 条 | 未验证 | TS-021 抽检 | 按 DEC-017：> 10 停下报用户 |
| HT-019 | 删掉覆盖官方的批量行后，这些键显示官方译文（合并字典按 app 顺序叠加，csv 无该键即取官方） | 读码（`frappe/translate.py:172-187`） | TS-018 验证方式 | 暂停反馈 |
| HT-020 | 每个可提交 DocType 的提交、取消确认框都经 `frappe.confirm`，点「否」不改数据 | 读码（`frappe/public/js/frappe/form/form.js:902-903,1068-1071`） | TS-023 第 7 步截图后查 `docstatus` 不变 | 暂停反馈 |

R3 的 HT-008（从自有侧栏进入、经「创建」时侧栏保持）本轮按 IT-021 实测，见 TS-023。

## 四、切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-011** 译名质量守卫 | IT-003、IT-006（白名单范围）、IT-009（占用脚本）、IT-001 的基线可跑部分；A17～A19 | ① `test_translation_quality.py` 四个守卫用例对当前 csv 全部通过；每个守卫有一条判别力用例——构造一行该类坏译文（繁体「帳戶」、逐词「登录 带 密码」、占位「中文：A0」、混排「上传 Photo」），断言该守卫报出它，且报出内容含源词。② `QUALITY_EXCEPTIONS`、`UNTRANSLATED`、混排的 `ALLOW` 每项有非空理由，用例断言。③ 覆盖清单：每条 `basis` 取自允许的依据形态（`DEC-0xx`／`S3 术语标准 §x.x`／`演示线撞名`／`按钮抽检 IT-010`），用例断言；`ours` 本身过四道守卫；csv 与官方的交集 ⊆ 清单键，失败时断言消息列出「交集 − 清单」与「清单 − 交集」两个差集。④ 基线脚本带 `--allow-unlocked` 时在 HEAD 与锁不一致的工作树上跑完，输出里 `commits.unlocked` 列出不一致的 app；不带时照旧拒跑（异常路径）。⑤ 占用脚本读合并字典：`python -I Spike/P1S6R4-occupancy.py "Stock Ledger" "物料凭证"` 报不可用、占用者含 `Stock Ledger Entry`（E 报告 IT-009 的反例） |
| **SL-012** 批量档整批重译 | IT-005、IT-006（缺口）、IT-012；DEC-028～030、038；A15、A16、A20 | ① TS-018 清场后 csv 只含 A15 四类行，脚本输出各类行数，删除行数 = 原行数 − 保留行数。② 覆盖官方的批量行删除后，抽 5 个键在测试站 `clear-cache` 后经 `get_all_translations("zh")` 取到官方译文（HT-019）。③ 重译完成后基线重跑：六 app 缺口合计 0，例外只在 `UNTRANSLATED`。④ 分层抽检 100 条（`SEED=20261011`），由**不参与该块翻译**的子 Agent 按需求 §4.2.3 三条判据加 DEC-029 逐条判，抽检表每行有判定与理由；不可用 ≤ 10，不可用条当场改并按错误类型回扫（回扫列表进回执）。⑤ 异常路径：不可用 > 10 时停在 TS-021，回执交抽检表与错误类型分布，报用户，不进 TS-022。⑥ `test_csv_sorted` 通过；把两行次序对调后该用例失败（判别力，在用例内构造） |
| **SL-013** 演示线定词补齐 | IT-007、008、009（重查表）、010、011；DEC-031、035、036 | ① 演示面上无官方译文的键（C 步实测 527 个，D 开工重跑为准）逐条有译文，回执附「源词／出处／译文」表。② 基线 `demo_collisions` 每组：组内源词译文两两不同，或在回执「同义保留」表里有一行写同义依据（S3 DEC-075 判据），两者之外 0 组；E 点名的 `Stock Ledger`／`Stock Ledger Entry`、`Is Paid`／`Paid`、`Payment Type`／`Type of Payment`、`Paid Amount`／`Payment Amount` 四组逐组写判定。③ S3 术语标准 §1.1、§1.3 收付款方向全表落 csv（无 context 的 `Unpaid` 除外，DEC-036：显示官方「未付」），每行进 `NAMED_TERMS`；另进 `Settings` → 设置（保留官方，断言官方值）、无 context 的 `Paid` → 已付款（断言官方值）。④ S3 的 73 组改词有占用重查表（原定／冲突源词／改定，无冲突写「无」），用修好的占用脚本跑，脚本输出附回执。⑤ 按钮抽检表重做：列「源词／现译／源码实际做什么（文件:行，写到被调方法）／判定／定稿」，20–40 词；`Payment` → 收付款（DEC-035）；定稿与现译不同的词全部写进 csv 与 `NAMED_TERMS`，表中定稿列与合并字典逐词一致（脚本比对，输出附回执）。⑥ `Dr` 在测试站称谓下拉显示「借方」的截图（IT-011）；占用脚本对已占用候选词的反例输出贴回执 |
| **SL-014** 逐屏核 v2 与演示站收尾 | IT-020、021、022、025；DEC-032～034；A21、A22；R3 SL-010 ②～⑥、⑧ | ① `screens.json` 覆盖需求 §4.9 表一、表二每一行，状态按 DEC-032 展开：新建单据两态（空白、保存后），由上游「创建」生成的单据两态（预填、保存后）；回执附「§4.9 行 → 屏 id」映射表，每行至少一屏、无空映射。② 演示线 15 个可提交 DocType（§五 TS-023 第 7 步表）各有提交确认框与取消确认框截图各一张，截后 `docstatus` 不变。③ 演示站逐屏核 `result.json` 每屏 `pass=true`（英文词、繁体、`title` 三类均为空）；发现问题的屏补 csv 后复跑通过，回执列补了哪些键。`default_data` 非空的屏，核对表列出词与记录，进延迟需求。④ 由「创建」进入的屏走菜单点击（不用 `set_route`），每屏记 `sidebar_title`；侧栏被换走的屏写明路径与原因（HT-008）。⑤ `Spike/P1S6R6-sidebar-dupes.py` 按 R3 Part4 签名在演示站返回 `{}`；`HDTH` 下科目 Link 下拉搜「应收」与 `Account.account_type` 选项列表两张截图，「应收账款」各只出现一次（IT-022）。⑥ 判别力整链反证（测试站，IT-025）：分别临时造三种失败——自有侧栏加一条英文 label 条目（不加 csv）、csv 临时加一行繁体译文、给一个按钮 `title` 临时设英文——各跑一次 `screen-check` 报 `pass=false` 并列出该词；三处随即恢复，`git -C frappe-bench/apps/frappe_china status --short` 为空。⑦ 新基准点按 R3 总纲 A14：备份 A → 造数核屏 → 测试态备份另存 `保留-S6R6测试态/` → 恢复 A（显式时间戳）→ 若期间改过 csv 或代码则 migrate 后另出基准点备份 → 另存 `保留-S6收尾/`；恢复后 `Translation` 0 行、造数前缀查无记录、`check_app_order` 为真、科目 266 |
| **SL-015** 全量回归与回写 | R3 SL-010 ⑦；R3 Part4 TS-015 | ① `frappe_china` 全量测试通过，条数 ≥ 242＋本方案新增，通过、跳过分开报；Node 用例 ≥ 29 条全过。② 测试站与演示站 `translation_check.run` 均返回 `[]`。③ 常驻文件按实况回写（项目概况的备份基准点、译名现状；开发守则补「批量写 csv 前先跑质量守卫」），写前载入常驻文件契约。④ 回执报 S6 工作量实耗与增量，供 Stage 收口按 RW-09 回写路线文档 |

**执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。**

## 五、任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-016 基线脚本可跑、占用脚本改读合并字典、白名单拆模块 | SL-011 | 否 |
| TS-017 质量守卫测试与覆盖清单重建 | SL-011 | 否 |
| TS-018 csv 清场与排序 | SL-012 | 否 |
| TS-019 演示线定词补齐 | SL-013 | 否 |
| TS-020 按钮抽检重做 | SL-013 | 读码部分可与 TS-017～019 并行；写 csv 在 TS-019 之后 |
| TS-021 批量档整批重译与抽检 | SL-012 | 分块翻译可并行（§七）；合并与抽检串行 |
| TS-022 逐屏核 v2 脚本与测试站反证 | SL-014 | 脚本编写可与 TS-021 并行；反证在 TS-021 之后 |
| TS-023 演示站逐屏核与新基准点 | SL-014 | 否 |
| TS-024 全量回归、常驻文件、工作量 | SL-015 | 否 |

---

## 任务 TS-016：基线脚本可跑、占用脚本改读合并字典、白名单拆模块（对应 SL-011）

### 目标
让本方案依赖的两个脚本在当前工作树上能跑出正确结果；白名单单一来源。

### 具体改动

1. **`Spike/P1S6R4-baseline.py`**：加参数 `--allow-unlocked`。
   ```python
   def commits(allow_unlocked: bool) -> dict:
       # 返回 {"heads": {app: sha}, "unlocked": {app: [head, locked]}}
       # allow_unlocked 为假且 unlocked 非空 → raise（原行为）；为真 → 打印告警、照常返回
   ```
   apps.json 锁本身不改（IT-001 仍属 SB）。
2. **白名单**：新建 `frappe_china/tests/translation_whitelist.py`，`UNTRANSLATED: dict[str, str]`，先迁入现有 `UTF-8`、`GB18030` 两项并写理由；`test_translations.py` 改为 `from frappe_china.tests.translation_whitelist import UNTRANSLATED` 并用其键。基线脚本 `gaps()` 读该文件（按路径 `importlib` 载入，不 import frappe），命中键不计缺口，输出加 `whitelisted` 计数。
3. **`Spike/P1S6R4-occupancy.py`**：`occupants()` 改用基线脚本的 `merged_dict()`（按路径载入），返回合并字典里 strip 后译文等于目标、且无 context 的全部源词；命令行用法不变。

### 验证方式
SL-011 ④⑤；`run-tests --module frappe_china.tests.test_translations` 全过。

---

## 任务 TS-017：质量守卫测试与覆盖清单重建（对应 SL-011）

### 目标
四道守卫进测试；覆盖清单只剩有依据的条目，依据写真实来源（IT-003）。

### 具体改动

1. **新建 `frappe_china/tests/test_translation_quality.py`**：
   ```python
   STOPWORDS: Final[frozenset[str]]       # is the to a of and for in on with you your this be are can not will from by an or if it that has have do
   ALLOW: Final[dict[str, str]]           # 混排白名单：缩写、品牌、按键名 → 理由（如 "SQL": "查询语言名"）
   QUALITY_EXCEPTIONS: Final[dict[str, str]]  # csv 键 → 理由；每项须写为何该行虽命中守卫仍可用

   def _strip_markup(text) -> str          # 去占位符（复用 test_translations._PLACEHOLDER）、HTML 标签、**…** 强调
   def find_placeholder(rows) -> list[str] # 译文以「中文：」开头或含「???」
   def find_traditional(rows) -> list[str] # 译文含 CJK 统一汉字且该字 encode("gb2312") 失败（A18）
   def find_word_by_word(rows) -> list[str]# 译文含汉字，且（_strip_markup 后含 STOPWORDS 中的英文词 或 匹配 [一-鿿] +[一-鿿]）
   def find_mixed(rows) -> list[str]       # 译文含汉字，_strip_markup 后仍有 [A-Za-z][A-Za-z0-9]+ 词，且不在 ALLOW、非全大写缩写
   # 每个函数返回 "键 => 译文" 字符串列表，已扣除 QUALITY_EXCEPTIONS
   ```
   四个用例各断言对 csv 全表返回 `[]`；四条判别力用例各喂一行构造坏行断言命中（SL-011 ①）；一条用例断言三张表每项理由非空。
2. **覆盖清单重建**（`tests/translation_overrides.py`）。对现有 218 条逐条判：
   | 判定 | 条件 | 处置 |
   |---|---|---|
   | 删 | `ours` 命中任一守卫 | 清单删该条；csv 该行在 TS-018 删除，回落官方 |
   | 留 | `ours` 过守卫，且能指出决策：`Timesheet` 全族（DEC-016）、`NAMED_TERMS` 里的键、S3 术语标准表行、R4 TS-014 用户批准的整句修复（DEC-026） | `basis` 改写为真实依据 |
   | 删 | `ours` 过守卫但指不出决策 | 同第一行；若 TS-019 判它属演示撞名须定词，届时重新进清单 |

   判定结果写回执附表（键／官方／ours／判定／依据）。
3. **`test_translations.py`**：交集断言改为
   ```python
   extra, missing = official_overlaps - set(OVERRIDES), set(OVERRIDES) - official_overlaps
   self.assertFalse(extra or missing, f"覆盖了官方但未登记：{sorted(extra)}；登记了但未覆盖：{sorted(missing)}")
   ```
   新增 `test_override_basis_forms`：每条 `basis` 匹配 `^(DEC-\d{3}|S3 术语标准 §[\d.]+|演示线撞名|按钮抽检 IT-010)`（可带后缀说明）；每条 `ours` 过四道守卫。

### 验证方式
SL-011 ①～③。此时 csv 里批量行仍在、守卫用例**预期失败**——本任务只要求四条判别力用例、理由用例与覆盖清单用例通过；守卫对全表通过放在 TS-018 之后验。回执写明这一时序。

---

## 任务 TS-018：csv 清场与排序（对应 SL-012）

### 目标
按 A15 一次删掉批量档与无依据的覆盖行，全表排序（DEC-030）。

### 具体改动
1. 新脚本 `Spike/P1S6R6-csv-prune.py`（宿主 `python -I` 跑，直接改 csv）：
   ```python
   def keep_keys() -> set[str]   # A15 ①②③：自有源词（复用 test_translations._app_source_strings 的取法）∪ REQUIRED_TRANSLATIONS ∪ NAMED_TERMS ∪ OVERRIDES（TS-017 重建后）
   def prune(rows) -> tuple[list, dict]   # 返回保留行与 {类别: 行数}；删除行另写 Spike/P1S6R6-pruned.csv 留档
   def sort_rows(rows) -> list   # key=(源词.casefold(), context or "")
   ```
   写回时用 `csv.writer(lineterminator="\n")`，与现文件一致。
2. `test_translations.py` 新增 `test_csv_sorted`（A20）与其判别力断言（在用例内对调两行验失败）。
3. 测试站 `clear-cache` 后跑 `test_translations`、`test_named_terms`、`test_translation_quality`。

### 验证方式
SL-012 ①②⑥；此时四道守卫对全表通过（SL-011 ① 的全表部分在此验）。缺口数此时会升到约 5500，属预期，回执记下基线重跑数字。

---

## 任务 TS-019：演示线定词补齐（对应 SL-013）

### 目标
演示面逐条定词、撞名逐组判、收付款方向与 73 组改词落地（需求 §4.2.2、§4.2.4；E 报告 IT-007～009、011）。

### 具体改动
1. 重跑基线（`--allow-unlocked`），取 `demo_surface` 中合并字典无中文的键（C 步实测 527）。按出处分块（每块 ≤ 150），每块导出 `Spike/P1S6R6-demo/in-{nn}.json`（键、`#:` 出处、出处前后各 3 行源码）。
2. 逐条定译文：主 Session 或子 Agent 译，给同一份术语表——S3 术语标准定稿词、`NAMED_TERMS`、需求 §4.2.4 用词规则、本任务已定的词；输出 `part-{nn}.csv`，主 Session 合并前先过四道守卫与占位符检查，不过的退回。
3. **撞名 191 组**：脚本把 `demo_collisions` 导成表（目标词／源词／各源词出处），逐组判同义或异义（S3 DEC-075）。异义的给唯一用词，候选先跑占用脚本；覆盖官方的进 `OVERRIDES`，依据「演示线撞名」。同义的进回执「同义保留」表，写依据。
4. **收付款方向**：S3 术语标准 §1.1、§1.3 逐行落 csv（带 context 的写三列，context 为 DocType 名）；**无 context 的 `Unpaid` 不写**（DEC-036）。全部进 `NAMED_TERMS`；覆盖官方的进 `OVERRIDES`，依据 `S3 术语标准 §1.1`／`§1.3`。
5. **73 组改词**：逐组跑修好的占用脚本，出重查表；无冲突照落，有冲突改定未占用词。
6. **HT-017**：测试站打开 `Accounts Settings`，看 `Role Allowed to over bill ` 字段 label；显示中文则照写 csv 键（带尾空格，csv 字段加引号保住空格），否则进白名单写理由。其余 22 条残余缺口（E 报告 IT-006 所列）同法逐条处置：译或进白名单写理由。
7. **IT-011**：测试站称谓下拉截 `Dr` 显示「借方」；占用脚本跑一个已占用候选词，贴输出。
8. 每批写完 `clear-cache`；任务收尾跑 `translation_check.run` 与三个译名测试模块。

### 验证方式
SL-013 ①～④、⑥。

---

## 任务 TS-020：按钮抽检重做（对应 SL-013）

### 目标
按需求 §4.4 重做抽检表（E 报告 IT-010）。

### 具体改动
1. 读码列按钮：需求 §4.4 的 13 张单据 `.js` 与 `erpnext/public/js/controllers/` 共用控制器里的 `add_custom_button(__("…"), …)`，加 `frappe/public/js/frappe/form/toolbar.js` 的保存／提交／取消／修订／删除。每词记**全部**调用行与被调方法，写到方法定义处（文件:行）。
2. 筛「点了会改数据」的（需求 §4.4 口径），按源词去重，20–40 词，不在区间写原因。
3. 表列：源词／现译（合并字典取，`clear-cache` 后）／源码实际做什么／判定／定稿。E 报告点名的 `sales_invoice.js:378/402`、`purchase_invoice.js:155`（实为「从…获取物料」）、`work_order.js:944` 逐行重核。
4. `Payment` → 收付款（DEC-035），进 `OVERRIDES`，依据「按钮抽检 IT-010」。其余定稿与现译不同的：按 R3 Part2 TS-009 第 4 条判能否改无 context 行；能改的写 csv、进 `NAMED_TERMS`，覆盖官方的进 `OVERRIDES`。
5. 写脚本比对表中定稿列与合并字典，输出附回执。

### 验证方式
SL-013 ⑤。

---

## 任务 TS-021：批量档整批重译与抽检（对应 SL-012）

### 目标
演示面之外的缺口全部重译（DEC-038），抽检达标（DEC-017／029）。

### 具体改动
1. 重跑基线，取剩余缺口（应全为演示面外），按 app 分块，每块 ≤ 300 条，导出 `Spike/P1S6R6-batch/in-{app}-{nn}.json`（键、出处、出处前后各 3 行源码）。
2. 每块派子 Agent 译成 `part-{app}-{nn}.csv`。**给译者的指令**（随块下发，原文写进 `Spike/P1S6R6-batch/README.md`）：
   - 简体中文、大陆用词；禁止取 `zh_TW.po` 原文或繁体字，禁止逐词对译、禁止中英夹杂（`ALLOW` 里的缩写与品牌除外）；
   - 术语表：S3 术语标准定稿词、`NAMED_TERMS`、TS-019 已定的全部演示线词、需求 §4.2.4 用词规则；
   - 占位符与 HTML 原样保留、次序不变；长段 Markdown 保留标记；
   - 每条看出处那几行源码再定译文，拿不准的在第三列外另输出 `doubt-{app}-{nn}.txt` 列出键与原因。
3. 主 Session 合并：每块先过四道守卫、占位符与 HTML 检查、无空译、不与法定列头同名；不过的整块退回重译。合并后排序（A20）。
4. `doubt-*.txt` 里的键由主 Session 逐条看源码定稿。
5. 抽检：`Spike/P1S6R4-sample.py` 改种子为 `SEED=20261011`、输出 `Spike/P1S6R6-sample.out.csv`，按 app 分层抽 100 条。另派一个**未参与任何一块翻译**的子 Agent 逐条判：需求 §4.2.3 三条判据，加「繁体或台湾用词即不可用」（DEC-029）；每条写理由。
6. 判定（DEC-017）：不可用 ≤ 10 → 当场改，并按错误类型回扫（脚本在全表 grep 同类），改动列入回执；> 10 → **停下**，回执交抽检表与错误类型分布，暂停反馈用户（SL-012 ⑤）。
7. 重跑基线确认缺口 0（例外只在 `UNTRANSLATED`）。

### 验证方式
SL-012 ③～⑤。回执记各 app 条数、块数、退回次数、抽检配额、不可用条数与类型、回扫条数、实耗人日。

---

## 任务 TS-022：逐屏核 v2 脚本与测试站反证（对应 SL-014）

### 目标
判据扩为三类（A21），屏清单按 DEC-032／034 重定，整链反证（IT-025）。

### 具体改动
1. **`Spike/P1S6R4-visible-text.cjs` → 另存 `Spike/P1S6R6-visible-text.cjs`**（旧文件不改，供 R4 证据复现）：
   ```javascript
   function extractVisibleText(dataSelectors) {}   // 同旧版，但不再收 aria-label（DEC-033）
   function findTraditional(entries) {}            // 页面里无 gb2312 编码器：用 TS-017 守卫同一判据生成的字表
                                                   // Spike/P1S6R6-trad-chars.json（官方 zh_TW 用字 − 官方 zh 用字，HT-016 依据）注入页面后比对
   function findEnglish(entries, allow) {}         // 同旧版，对 text、placeholder、title 三类都跑
   ```
   注：浏览器端无法直接判 GB2312，故改用字表；字表由脚本从六 app 的 po 生成，生成脚本与字表都进 `Spike/`。
2. **`Spike/P1S6R6-screen-check.js`**（基于 R4 版）：`result.json` 每屏输出 `{id, stage, state, pass, english, traditional, title_issues, default_data, sidebar_title, screenshot}`；`pass = english、traditional、title_issues 皆空 且 sidebar_ok`。`screens.json` 顶层加 `default_data: {词: {doctype, name, reason}}`——命中的词进 `default_data` 字段、不进 `english`；脚本启动时经 REST 查每个 `doctype/name` 存在，不存在即报错退出（防止拿它当万能白名单）。
3. **`Spike/P1S6R6-screens.json`**：按需求 §4.9 两张表逐行展开，`state` 取 `blank`／`saved`／`prefilled`／`dialog`／`list`／`report`；「由上游创建」的屏用 `steps` 点「创建」菜单项（选择器用 `.inner-group-button[data-label]` 与菜单项文字，`frappe/public/js/frappe/ui/page.js:550-585`），不用 `set_route`。末尾附确认框屏（TS-023 第 7 步）。
4. **反证（测试站 6787）**：SL-014 ⑥ 三种失败各造一次、各跑一次只含该屏的 `screens-proof.json`，结果存 `Spike/P1S6R6-proof/`；随即恢复并核 `git status` 为空、`clear-cache`。
5. 先在测试站把全部屏跑通（修脚本自身问题），测试站数据可用 `Spike/P1S6R4-closed-loop.py` 的做法造。

### 验证方式
SL-014 ①、⑥；测试站全屏跑通（结果不作验收，只作脚本可用证据）。

---

## 任务 TS-023：演示站逐屏核与新基准点（对应 SL-014）

### 目标
在演示站按 v2 判据核完全部屏，留下干净的新基准点（R3 总纲 A14）。

### 具体改动
1. **核旧基准点**：`docker/backups/` 根目录与 `保留-S6收尾/` 下 `20261010_232619` 的 4 个文件都在。
2. **上线**：演示站 `migrate`、`bench build --app frappe_china`、`clear-cache`，重启 `bench start` 进程；跑 SL-015 ② 的演示站一半与 `check_app_order`。
3. **备份 A**：`docker/backup.sh`，记时间戳 `{A}`。
4. **造数**：按 `最小闭环操作稿.md` 环节 1–23（`HDTH` 下，CRM 线索、商机在 `/crm` 里建）；脚本可沿用 `Spike/P1S6R4-closed-loop.py`，前缀改 `_S6R6`。需界面经「创建」生成的单据，在逐屏核的 `steps` 里经界面做。
5. **逐屏核**：`node Spike/P1S6R6-screen-check.js http://localhost:8000 Spike/P1S6R6-screens.json Spike/P1S6R6-screens/`。不通过的屏：补 csv（测试站先验、再同步演示站 `clear-cache`）后对该屏复跑。补了 csv 的，全部完成后跑 `test_translation_quality` 与 `test_translations`。
6. **侧栏与「应收」**：写 `Spike/P1S6R6-sidebar-dupes.py`（R3 Part4 接口契约的签名），演示站 `bench execute` 跑；截两张「应收」图（SL-014 ⑤）。
7. **确认框**（DEC-034，A22）：下表每个 DocType 取一张已保存草稿截提交确认框、取一张已提交单据截取消确认框，截后点「否」，查 `docstatus` 不变（HT-020）：

   | # | DocType | # | DocType |
   |---|---|---|---|
   | 1 | BOM | 9 | Work Order |
   | 2 | Purchase Order | 10 | Stock Entry |
   | 3 | Purchase Receipt | 11 | Job Card |
   | 4 | Purchase Invoice | 12 | Delivery Note |
   | 5 | Payment Entry | 13 | Sales Invoice |
   | 6 | Quotation | 14 | Month End Closing Voucher |
   | 7 | Sales Order | 15 | Cash Flow Worksheet |
   | 8 | Production Plan | | |

   演示线另用到的 `Stock Reconciliation`（期初）、`Journal Entry` 若在本轮造数中出现，一并截，回执注明。
8. **测试态备份**：`docker/backup.sh`，4 个文件另存 `docker/backups/保留-S6R6测试态/`。
9. **恢复 A**：`docker/restore.sh {A}`（显式），`migrate`、`clear-cache`；查 `Translation` 0 行、`_S6R6` 前缀记录 0、`tabCash Flow Worksheet` 0 行。
10. **新基准点**：第 5 步改过 csv 或代码则 A 已过时，`migrate`、`clear-cache` 后另出备份 C；4 个文件另存 `保留-S6收尾/`。回执写明最终基准点时间戳，并确认根目录最新一套即它。

### 验证方式
SL-014 ②～⑤、⑦。截图与 `result.json` 放 `Spike/P1S6R6-screens/`。

---

## 任务 TS-024：全量回归、常驻文件、工作量（对应 SL-015）

### 具体改动
1. 测试站全量 `run-tests --app frappe_china`，报收集、通过、跳过；宿主 `node --test frappe_china/tests/*.cjs`。
2. `git status --short`（主仓库与 `frappe_china`）逐个文件对上本方案任务；六个上游 app 目录 `status` 为空。
3. 常驻文件——**先载入 `docs/流程体系/常驻文件契约.md`**：
   - `docs/项目概况.md`：「开发环境」节演示站状态与备份基准点（新基准点、`保留-S6R6测试态/`）；「已知限制」译名条按本轮结果改写（不宣称 Stage 完成）；
   - `docs/开发守则.md`：「译名自检时机」节补「批量写 csv 前后跑 `test_translation_quality`；批量译文不得取 `zh_TW.po`」。
4. 回执报 S6 本轮实耗人日与相对路线文档 11.25–18 的增量（RW-09），**本任务不改路线文档**，交 Stage 收口。

### 验证方式
SL-015 ①～④。

## 六、相对 R3 方案的替换

| R3 原文 | 本方案 | 依据 |
|---|---|---|
| Part2 TS-006「csv 分段」三段与 `CSV_SECTIONS`、`test_csv_sections_sorted` | 全表排序、`test_csv_sorted` | DEC-030；A20 |
| Part2 TS-006 第 2 步「`Unpaid`／`Paid` 的 `Sales Invoice` context 行…；收付款方向照 S3 逐行落」 | 无 context 的 `Unpaid` 不写，显示官方「未付」 | DEC-036 |
| Part2 TS-007 全部 | 本方案 TS-021 | DEC-038 |
| Part2 TS-009 第 4 步 `Payment` 一类「不可分、保留」 | `Payment` → 收付款 | DEC-035 |
| Part2 接口契约 `occupants()`「合并字典（含当前 csv）」 | 落实为读 `merged_dict()` | IT-009 |
| Part4 SL-010 ②③④⑧ 与 TS-014 | 本方案 SL-014、TS-022／023 | DEC-032～034；IT-020～022、025 |
| Part4 TS-014 第 7 步测试态备份目录 `保留-S6R4测试态/` | `保留-S6R6测试态/` | 区分两轮测试态 |
| 总纲 §九第 3 条回执命名 `P1-S6-R4-D回执-Part{N}.md` | `P1-S6-R7-D回执.md`（见 §八） | 新一轮 D |

## 七、并行开发说明

| 可并行组 | 任务 | 各自写入范围 |
|---|---|---|
| ① | TS-019 第 2 步、TS-021 第 2 步的分块翻译 | 每块写自己的 `Spike/P1S6R6-{demo,batch}/part-*.csv`，互不相交；**合并进 `zh.csv` 只由主 Session 做** |
| ② | TS-020 第 1～3 步（读码出表） | 只读 erpnext／frappe 源码，产物是回执附表 |
| ③ | TS-022 第 1～3 步（写脚本与屏清单） | 只写 `Spike/P1S6R6-*`，不碰 csv 与站点 |
| ④ | SB（附属 R5）余项 IT-001、013、017、018、026、027 | 不碰 `zh.csv`；IT-013 用测试站造发票，与本方案 TS-022 测试站跑屏错开时间即可。IT-001 改 `docker/apps.json` 锁，完成后本方案的 `--allow-unlocked` 可不再带 |

## 八、执行顺序与回执

```
TS-016 脚本可跑／白名单 ─→ TS-017 守卫与覆盖清单 ─→ TS-018 清场与排序
                                                        └─→ TS-019 演示线定词 ─→ TS-021 批量重译与抽检 ──(不可用 > 10 即停)
              TS-020 按钮抽检（读码并行，写 csv 在 TS-019 后）──┘                     │
              TS-022 逐屏核 v2（脚本并行，反证在 TS-021 后）────────────────────────────┤
                                                                                       └─→ TS-023 演示站 ─→ TS-024 收尾
```

D 步为 **R7**，回执 `R07-代码/P1-S6-R7-D回执.md`（不拆 Part），开工即建、预填 TS-016～024，逐任务当场回写（`bricks/receipt.md`）。D 完成后回 E 复核（R8），E 复核范围为本方案全部切片，加 R5 报告中 `本Session修` 与 SB 各项的复核。
