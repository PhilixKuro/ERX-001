# Rev-P1S4R2 — V-25／V-26 两条判定的对抗式复核

**性质**：对另一个 agent 写下的两条 spike 判定做**独立重验**，目标是**推翻**它们。不采信原探针的任何结论、任何数字、任何行号。

**站点**：`erx.localhost`，公司 `华东弹簧`（唯一一家）。容器 `erx001-frappe-1`。
**探针**：`Rev-P1S4R2-a-facts.py`／`-b-cache.py`／`-c-inject.py`／`-d-runtime.py`／`-e-rowlevel.py`，原始输出在 `Spike/Rev-out/`。
**写入**：全部在事务内、`finally` 里 `rollback()`，**五份探针无一处 `frappe.db.commit()`、无一处 `frappe.enqueue`**。临时模板 `module` 全部留空。

**基线逐项核对（跑完后独立再查一遍）**：
GL Entry **22**／Stock Ledger Entry **12**／Account **95**／Company **1**／Financial Report Template **6**／Fiscal Year 仅 **`2026`**／PCV **0**／Account Closing Balance **0**。
FRT 六张全是出厂模板名，`ZZ%` 残留 **0** 条，导出目录无残留文件。演示数据未被触碰。

---

## 总判定

| 判定 | 原结论 | 复核结论 | 一句话 |
|---|---|---|---|
| **V-25** | `go`（缺口成立） | **成立** | 结论对，机制对，且我补跑了原探针**没验的那个组合**（中文段标签＋双栏＋两会计年度），结论更强而不是更弱。但**两处引文不准**，其中一处行号是空行 |
| **V-26** | `no-go`（命题被证伪） | **成立** | 两列并存为真。而且原探针的**判据设计有一个它自己没意识到的漏洞**，我用另一个判据把漏洞补上了——补上之后结论不变 |

**两条都站得住。没有任何一处发现会翻转依赖它们的方案判断。** 下面把「哪些是我亲手复现的」「哪些是原报告说过头的」分开列清。

---

## 一、V-26：`no-go` —— **成立**

### 1.1 我亲手复现的决定性数字

裸 GL 独立重算（**纯 SQL，不经引擎、不经原探针的任何 helper**，`Rev-out/a-facts.json` → `independent_triple`）：

| 量 | 值 | 判据 |
|---|---|---|
| Income 净额（debit−credit） | **−1045.0** | `销售 - HDS` 单条，2026-09-21 |
| Income 反号后 | **1045.0** | `revenue_equals_1045` = **true** |
| Expense 净额 | **325.5** | `销货成本 - HDS` 325.77 ＋ `结转库存的费用 - HDS` −0.27 |
| | | `cost_equals_325_5` = **true** |
| 1045.0 − 325.5 | **719.5** | `difference_equals_719_5` = **true** |

**与原探针 `raw_gl_pl_movement_by_month` 的 `{"2026-09": -719.5}` 逐位吻合**（−1045.0＋325.5 = −719.5）。
**注意 325.5 是两个科目的净额**，不是单一科目余额——原报告写「成本 325.5」没错，但没提它由 325.77 与 −0.27 抵出，看数的人可能对不上 GL 明细。

引擎侧我自建三段模板重跑（`Rev-out/d-runtime.json` → `DECISIVE_V26_reproduced`），净利润行：

| 月份 | `Closing Balance` 段 | `Period Movement` 段 | `Opening Balance` 段 |
|---|---|---|---|
| Aug 2026 | 0.0 | 0.0 | 0.0 |
| **Sep 2026** | **719.5** | **719.5** | 0.0 |
| **Oct 2026** | **719.5** | **0.0** | **719.5** |
| **Dec 2026** | **719.5** | **0.0** | **719.5** |

四项断言全 true，且 `matches_raw_gl_719_5` = true。**与原探针的 `DECISIVE` 键逐位一致。**

### 1.2 ⚠ 原探针判据的漏洞，以及我怎么补的（本次复核最有价值的一条）

**审计任务书自己点出的疑虑成立，但比它设想的更严重，而且原探针有第二个漏洞它自己没说。**

**漏洞一（任务书已点出）**：站点只有一个月有账 ⇒ 「一个只会**重复上次值**的列」也能通过 `cumulative_holds_after_sep`。原探针 seg1 里 Sep 的 `Closing` 与 `Movement` **都是 719.5**（因为 opening = 0），**该期内两者无从区分**，「累计」这个语义并未被真正观测到。

**漏洞二（原探针未察觉）**：seg1／seg2 都把累计行放 seg_0、单月行放 seg_1。这个设计**无法区分**：
- (i) `balance_type` 按**行**生效 ← 它要证的
- (ii) `balance_type` 按**段**生效，引擎只是取了每段第一条 Account Data 行的值

**两种假设对 seg1／seg2 的输出预测完全相同。** 而整条 `no-go` 就压在 (i) 上。

**我用的补救判据（不写任何 GL）**：本站点 GL 分布在**两天**——`2026-09-20` 与 `2026-09-21`（`a-facts.json` → `all_gl_entries`）。把区间起点卡在**两天之间**（`Date Range` 2026-09-21…12-31），取一个两天都有账的**资产**科目（`存货 - HDS`：09-20 +750.0，09-21 净 −325.5）：

| 量 | 实测值 |
|---|---|
| `Opening Balance`（Sep） | **750.0** |
| `Period Movement`（Sep） | **−325.5** |
| `Closing Balance`（Sep） | **424.5** |

`750.0 + (−325.5) = 424.5` ⇒ `closing_equals_opening_plus_movement` = **true**，`closing_differs_from_movement_in_first_period` = **true**，`rules_out_repeat_last_value` = **true**。

**这个判据能区分它声称区分的两件事**：「重复上次值」造不出 424.5，「只重复发生额」也造不出 424.5。**在同一个期间内** closing = opening + movement，是滚动求和的直接证据。机制侧对应 `_calculate_running_balances()`（`financial_report_engine.py:679-704`）逐期 `closing_balance = current_balance + movement` 并把它当作下期 opening——**这是结构性保证，与本站点数据无关**。

**漏洞二的补救（`Rev-out/e-rowlevel.json` → `DECISIVE_row_level`）**：建一张**完全不含 `Column Break`** 的模板（`column_breaks` = 0 ⇒ 只有一个段），放六条 Account Data 行，**同一批科目、只有 `balance_type` 不同**：

| 行 | balance_type | Sep 2026 实测 |
|---|---|---|
| STOCK as OPENING | Opening Balance | **750.0** |
| STOCK as MOVEMENT | Period Movement | **−325.5** |
| STOCK as CLOSING | Closing Balance | **424.5** |

`three_types_differ_in_ONE_segment` = **true**，`so_balance_type_is_row_level` = **true**。
**三个值来自同一张模板、同一个段、同一次运行的三条行** ⇒ `balance_type` 不可能是段级或报表级。**假设 (ii) 被证伪，(i) 成立。**

### 1.3 `balance_type` 是行级字段 —— 独立坐实（两条互不依赖的证据）

**DocType 侧**（`a-facts.json`）：
- `tabDocField` 里 `fieldname='balance_type'` **只有一行**，`parent` = **`Financial Report Row`**，`fieldtype` = Select，`options` = 三选一
- `Financial Report Row` 的 `istable` = **1**（子表）⇒ 每行一份取值，天然行级
- `Financial Report Template`（`istable` = 0）**没有** `balance_type` 字段
- `tabCustom Field` 里叫 `balance_type` 的 **0 条** ⇒ 无定制覆盖
- 字段数 **21／7**，与 DocType JSON 的 `field_order` 长度一致，**两个数都对**

**引擎侧**：`balance_type` 的全部 11 处用法（`grep` 全文）都在**取值**路径上，且都以「行」为单位：
- `:371` `"balance_type": row.balance_type` —— 从**模板行**取
- `:403` / `:419` 每个 `request`（= 一条 Account Data 行）各算一次 `get_ordered_values(period_keys, balance_type)`
- `:60-66` `PeriodValue.get_value()` 按 `balance_type` 从 **opening／closing／movement 三个并存字段**里三选一
- `:1770-1771` 明细行 `getattr(parent_row, "balance_type", "Closing Balance")`

**⇒ `opening`／`closing`／`movement` 在 `PeriodValue` 上同时存在，按行各取所需。** 这是 `no-go` 的结构性根据。

**顺带一条比原报告更强的产品侧证据**：出厂模板 `Horizontal Balance Sheet (Columnar)` **自己就在同一个段内混用两种 balance_type**——`idx 4…22` 全是 `Closing Balance`，`idx 26`（`Net Profit/(Loss) for the Year`）是 `Period Movement`，而该段的 `Column Break` 在 `idx 27`（在它们**之后**）。⇒ **行级粒度是出厂模板正在用的东西，不只是探针造出来的。** 另有 4 张出厂模板的 `distinct_balance_types` > 1。

### 1.4 `accumulated_values` 不存在于本报表 —— 比原探针查得更广

原探针只数了 3 份 js。**空的 grep 只等于「没找到」**，所以我换成「先列目录、再全量扫」：

**全量扫描**（`c-inject.json`）：两个已安装 app（frappe、erpnext）下 **7552 个** `.py/.js/.json/.html/.md`，`accumulated_values` 命中 **恰好 11 个文件**：

| 文件 | 次数 |
|---|---|
| `financial_report_engine.py` | 8 |
| `financial_statements.py`（py 基座） | 20 |
| `balance_sheet.py` / `.js` | 13 / 1 |
| `profit_and_loss_statement.py` / `.js` | 14 / 1 |
| `cash_flow.py` | 13 |
| `gross_and_net_profit_report.py` / `.js` | 8 / 1 |
| 两份 test | 1 / 3 |

**`custom_financial_statement.js` 与 `public/js/financial_statements.js` 都不在名单里** ⇒ 原探针那两个 0 **确认为真**。目录列举也确认了 `custom_financial_statement/` 只有 4 个文件、`public/js/` 里只有一份 `financial_statements.js`，**没有被 grep 漏掉的兄弟文件**。

**能不能从别处注入？逐条查（都是空集）**：

| 可能的注入口 | 实测 |
|---|---|
| `tabReport`（DB 里的实际记录，非磁盘 json） | `json`／`query`／`javascript`／`report_script` **全为空串**；193 张 Report 无一张的存储代码提到该 key |
| `Report Filter` 子表 | 本报表 **0 行**；全库仅 1 行且不含 `accumulated` |
| `Report Column` 子表 | 本报表 0 行，全库 0 行 |
| frappe **Custom Report**（可带 `custom_filters`／`custom_columns`） | 全库 **0 张** Custom Report；无一张 `reference_report` 指向本报表 |
| Property Setter（182）／Client Script（0）／Server Script（0）／Custom Field（12）／Dashboard Chart（49）／Number Card（50）／Workspace（19） | 逐份 `as_dict()` 序列化后搜索，**flagged 全为空** |
| 两个 app 的 `hooks.py` | 均不提 `financial_report`／`custom_financial`／`accumulated` |
| 非 erpnext 文件提到 `report_template` | **0 个** ⇒ 无第三方猴补丁 |

**同义词扫描**（`accumulated`／`cumulative`／`ytd`／`year_to_date`／`running_balance`／`accumulate`）也没扫出第二个开关。

**⇒ 「`filters.get("accumulated_values")` 在 FRT 路径上恒为 `None`」在本站点当前状态下确认为真**，命中 `:711-715` 的 `continue`（行号逐行核对无误，注释原文与引用一致）。

### 1.5 我额外做了一件原探针没做的事：**显式传入该开关，看它是否真的拉平全表**

原报告断言「那个开关只在被显式传入时才拉平全表」。这是**推论**，它没跑。我跑了（`d-runtime.json` → `EXPLICIT_accumulated_values_effect`）：

| 传入值 | `Closing` 列（Oct） | `Movement` 列（Oct） | 两列还有差别？ |
|---|---|---|---|
| **不传**（真实路径） | 719.5 | 0.0 | **是** |
| `accumulated_values=0` | 0.0 | 0.0 | **否** |
| `accumulated_values=1` | 719.5 | 719.5 | **否** |

**断言坐实，而且是实测坐实的**：显式传入任一值，两列都被拉平成同一个数，「一列累计一列单月」当场失效。**这恰好反向印证了 `no-go` 的成立条件**——它成立**正因为**这个 filter 不存在于本报表。若哪天有人给 FRT 报表加上这个 filter，V-26 的结论就会翻转。**这是一条原报告没写、但对方案有实际约束力的事实。**

### 1.6 `Closing Balance` 是滚动余额 —— 复现，且回退分支是**实录**而非推断

原探针靠「PCV 0 条 ⇒ 所以走回退」来推断。我把三个函数**包了一层探针**，让运行时**记录实际走了哪条分支**（`d-runtime.json` → `DECISIVE_seg2_reproduced.branches_taken`）：

```
{"branch": "_get_opening_balances_from_gl", "earliest_date_literal": "1900-01-01",
 "n_accounts": 34, "first_period_from": "2026-10-01"}
{"branch": "_get_gap_movements", "from_date": "1900-01-01", "to_date": "2026-10-01",
 "nonzero": {"存货 - HDS": 424.5, "销售 - HDS": -1045.0, "销货成本 - HDS": 325.77, ...}}
```

**`_get_closing_balances(PCV)` 一次都没被调用** ⇒ 走的确实是 `1900-01-01` 那条回退。**这比原探针的推断强一级：不是「应该走这条」，是「实录走了这条」。**

区间挪到全部 GL 之后（2026-10-01…12-31）：`Closing`(Oct) = **1045.0**，`Movement`(Oct) = **0.0**，`Opening`(Oct) = **1045.0**。**区间内零笔账而 Closing 报 1045.0** ⇒ 复现原探针的 `DECISIVE_seg2`。

**PCV 0 条、Account Closing Balance 0 行**——两个都用裸 SQL 独立确认。

### 1.7 V-26 项下我**没能**独立确认的，以及为什么

| 未验项 | 为什么 | 属哪类 |
|---|---|---|
| **年结 PCV 能否让累计列从本年起算** | **站点安全红线**。规则 2 要求：写入前先 grep 路径上的 `commit`／`enqueue`，命中就不跑、只报。我 grep 了：`period_closing_voucher.py:300,571` 有 **`frappe.enqueue`**；`process_period_closing_voucher.py:131,285,462,612` 有 **`frappe.db.commit()`**（带 `# nosemgrep`）。本站点 `use_legacy_controller_for_pcv` = **1**，走 `make_gl_entries()`，其 enqueue 有 GL>100000 的门槛（本站点 22 条，不会触发），**但 `commit` 分支在 `Process PCV` 上，一旦走到 rollback 救不回来**。⇒ **不跑，只报。** 与原探针同样未验，但我的理由是**已查证的硬阻断**，不是「没碰」 | **缺手段**（受安全规则阻断） |
| **多月有账时逐月累计是否正确递增** | 站点全部 GL 只落在 **2026-09-20／09-21 两天**（裸 SQL 逐条确认，`gl_month_x_roottype` 只有 `2026-09` 一个键）。**跨月累计验不了。** 我用「同期内 closing = opening + movement」把「是否真累计」这一层补上了（§1.2），但那是**期内**证据，**不等于跨月证据** | **原始证据不足** |

**须明说的边界**：`DISCRIMINATOR` 证明了 closing 是**滚动求和**，也证明了值能跨期带过去（`Opening`(Oct) = `Closing`(Sep) = 424.5，`opening_oct_equals_closing_sep` = true）。但「**多个不同月份各有发生额时，逐月累计值正确递增**」这件事，本站点**没有数据可验**。任务书说另有探针在测多月情形——我不重复，只把边界钉死在这。

---

## 二、V-25：`go` —— **成立**

### 2.1 六个列头逐字复核

我用出厂模板 `Horizontal Balance Sheet (Columnar)`、事务内建 FY2025、`Fiscal Year` 2025→2026、`Yearly` 重跑（`d-runtime.json` → `V25_six_labels_char_for_char`）：

| fieldname | label | 与原报告 |
|---|---|---|
| `seg_0_account` | `Equity & Liabilities` | ✓ |
| `seg_0_dec_2025` | `Equity & Liabilities - 2025` | ✓ |
| `seg_0_dec_2026` | `Equity & Liabilities - 2026` | ✓ |
| `seg_1_account` | `Assets` | ✓ |
| `seg_1_dec_2025` | `Assets - 2025` | ✓ |
| `seg_1_dec_2026` | `Assets - 2026` | ✓ |

`all_match` = **true**，行数 **34**，与原探针一致。`dec_2026` 列有实值（Inventories 424.5／Cash & Bank 295.0／TOTAL 719.5）。
**`dec_2025` 全零**——合理（FY2025 无账），但这意味着**「两个会计年度」这一维只验到了列头形态，没验到跨年取数**。原报告说「数字有实值」对，但那是 2026 那一列。

### 2.2 模板层无列名字段 —— 独立坐实

`Financial Report Row` **21** 个字段、`Financial Report Template` **7** 个字段，两个数都对（DocType JSON 的 `fields` 长度、`field_order` 长度、`frappe.get_meta()` 三路一致）。
含 `label`／`header` 的字段：**两边都是空集**。我把判据放宽到 `caption`／`title`／`heading`／`column_name`：**仍然是空集**。

`financial_statements.py` 内 `label = ` 赋值点 **恰好 7 处**（`:89/92/95/97/152/154/156`），全部由 `periodicity` ＋ 日期算出，**无一处读模板**。原报告的「7 处」**数对了**。

### 2.3 我补跑了原探针**自陈未验**的那个组合，结论更强

原报告复核建议第 3 条自陈：「自建模板给 `Column Break` 填**中文** `display_name` 后列头长什么样，**没在双栏 BS ＋ 两会计年度那个组合上单独验过**」。我验了（`d-runtime.json` → `V25_chinese_segment_labels`），两段分别填 `年初余额`／`期末余额`，BS，两会计年度，`Yearly`：

| fieldname | label |
|---|---|
| `seg_0_account` | **`年初余额`** ← 逐字，无后缀 |
| `seg_0_dec_2025` | **`年初余额 - 2025`** |
| `seg_0_dec_2026` | **`年初余额 - 2026`** |
| `seg_1_account` | **`期末余额`** ← 逐字，无后缀 |
| `seg_1_dec_2025` | **`期末余额 - 2025`** |
| `seg_1_dec_2026` | **`期末余额 - 2026`** |

**⇒ V-25 成立，但须把表述收得更准。** 原报告写「引擎**必然**在其后追加 ` - {期间}`」——**不完全准确**：
- **项目列（`seg_N_account`）拿到的是逐字中文，没有后缀**（`:1724`，走 `segment.label` 原值）
- **只有期间列（`seg_N_<期间键>`）被追加后缀**（`:1727-1728`）

**而法定「年初余额／期末余额」要的是放数字的那两列** ⇒ 逐字合规**确实做不到**，**结论不变**。但「必然追加」这句话字面上不成立，B 步若照抄会留下一个可被证伪的判据。单会计年度（`G` 运行）也一样：`年初余额`／`年初余额 - 2026`／`期末余额`／`期末余额 - 2026`。

### 2.4 我另外界定了一条原报告没说的边界：**后缀只在多段时出现**

单段模板（**完全不含 `Column Break`**）实测列头（`e-rowlevel.json` → `single_segment_column_labels`）：
`Account`／`Sep 2026`／`Oct 2026`／`Nov 2026`／`Dec 2026` —— **`any_label_has_dash_period` = false，`uses_seg_prefix` = false**。

机制：`SingleSegmentFormatter.get_columns()`（`:1692-1697`）**原样返回 `base_columns`**，只改 `align`；拼接只发生在 `MultiSegmentFormatter.get_columns()`（`:1713-1732`）。
**⇒ `段标签 - 期间标签` 是「双栏」这个形态的代价，不是引擎的普遍行为。** 这一条对「要不要用双栏」是有意义的事实，原报告没有分离出来。

### 2.5 探针产物（`-2025` 前导横线）—— 确认是探针造的

原报告声明这是自己造的，**确认无误**，且理由比它写的更硬：

- `get_period_list` 的 `accumulated_values` 默认值是 **`False`**（`financial_statements.py:31`）
- 引擎全文 **`get_period_list(` 只有一个调用点**（`:280`，即 `_initialize_context`），参数列表逐行核对：`from_fiscal_year`／`to_fiscal_year`／`period_start_date`／`period_end_date`／`filter_based_on`／`periodicity`／`company=` —— **确实没有 `accumulated_values`**，也没有 `ignore_fiscal_year`
- 成因坐实：`ignore_fiscal_year=True` 时 `:76-78` 被跳过 ⇒ `from_date_fiscal_year_start_date` 不存在 ⇒ `:95` 的 `get_label(...)` 收到 `None` ⇒ `:154` `formatdate(None)` 得空串 ⇒ `"" + "-" + "2025"`
- **全仓库只有两个地方传 `ignore_fiscal_year=True`**（`fixed_asset_register.py:188`、`exponential_smoothing_forecasting.py:72`），**两个都不传 `accumulated_values`** ⇒ **该组合在产品里无处可达，不可能是产品 bug**

**「累计标签分支是死代码」——比原报告的证据更强的实测**：我在 FRT 路径上**显式传入** `accumulated_values=0/1`（§1.5 那两次运行），期间列标签**一字不变**（仍是 `CLOSING - Jan 2026` …）。因为 `_initialize_context` 压根不把 filter 转给 `get_period_list`。
**唯一被显式传入影响到的是 `:1418` 那个 `get_columns(...)` 调用**：`accumulated_values=0` 时多出 3 个 `Total` 列（`seg_N_total`），列数 39 → 42。**这是原报告完全没提到的一个副作用**，但它只在显式传入时出现，真实 UI 路径不会。

### 2.6 V-25 项下我**没有**独立确认的

| 项 | 状态 |
|---|---|
| **`Custom API` 管不了列头** | **与原报告同样只读了代码，我没实跑。** 我核了 `:1185` 的签名与上下文（`_process_api_row`，返回值绑给 `values`，随后 `RowData(row=row, values=values)`，并按 `reverse_sign` 逐元素取反 ⇒ 确实是**按期间排的扁平数值列表**），**代码契约支持该结论**，但**没有真写一个 Custom API 方法跑一遍**。任务书说另有探针在跑这条，我不重复。**这是两条判定里唯一仍然纯读码的部分** |
| **中文段标签在 Monthly＋多段下的列数** | 未单独跑；`Yearly` 双段两会计年度已跑 |

---

## 三、逐条载荷性主张 → 是否独立确认 → 用什么手段

| # | 主张 | 独立确认 | 手段 |
|---|---|---|---|
| 1 | `balance_type` 是**行级**字段 | **是** | `tabDocField` 唯一一行、parent = `Financial Report Row`、`istable`=1；无同名 Custom Field；引擎 11 处用法全按行；**外加单段三类型实测三值互异** |
| 2 | 三种 balance 值在 `PeriodValue` 上**并存** | **是** | `:52-66` 源码 ＋ 单段模板同时取出 750.0／−325.5／424.5 |
| 3 | `accumulated_values` 在 FRT 报表上不存在 | **是** | 7552 文件全量扫 → 恰好 11 个文件，两份目标 js 均不在内；DB 侧 Report／Report Filter／Custom Report／Property Setter／Client Script／Server Script 全空；两 app hooks 不涉 |
| 4 | 故命中 `:711-715` 的 `continue` | **是** | 行号逐行核对；注释原文一致；不传时两列有别、显式传入即被拉平（反向验证） |
| 5 | 引擎数与裸 GL 逐位吻合（1045.0／325.5／719.5） | **是** | 纯 SQL 独立重算，三个等式全 true |
| 6 | 累计列确实**累计**而非重复上次值 | **是（原探针未能证明，我补上了）** | 区间卡在两个 GL 日之间：closing 424.5 = opening 750.0 + movement (−325.5) |
| 7 | `Closing Balance` 是**滚动**余额，非本年累计 | **是** | Oct 区间零笔账仍报 1045.0；**运行时实录**走 `_get_opening_balances_from_gl`，`_get_closing_balances(PCV)` 从未被调用 |
| 8 | PCV 0 条、ACB 0 行 | **是** | 裸 SQL 两路确认 |
| 9 | 六个列头逐字 | **是** | 重跑出厂模板，`all_match` = true，34 行 |
| 10 | 21／7 个字段、无 label/header 字段 | **是** | DocType JSON ＋ `field_order` ＋ `get_meta()` 三路一致；判据放宽到 caption/title/heading 仍空集 |
| 11 | `financial_statements.py` 内 label 赋值 7 处、全由日期算 | **是** | 带行号全量列出 |
| 12 | 段标签来自 `Column Break.display_name` | **是** | `:1570` 赋值 ＋ 出厂模板两个 break 的 `display_name` 与实测逐字吻合 ＋ 自建中文模板实测生效 |
| 13 | `-2025` 是探针产物、非产品 bug | **是** | 唯一调用点参数列表；全仓库仅两处传 `ignore_fiscal_year=True` 且都不传该开关 |
| 14 | FRT 路径下累计标签分支是死代码 | **是（比原证据更强）** | 显式传入 0/1，期间标签一字不变 |
| 15 | 年结 PCV 能让累计列从本年起算 | **否——我未验；已由 V-27 证伪（见 §七）** | **受站点安全规则阻断**：PCV 路径带 `frappe.enqueue` ＋ `frappe.db.commit()`。按规则「不跑、只报」 |
| 16 | 多月有账时逐月累计正确递增 | **否——验不了** | 站点全部 GL 仅 2026-09-20／09-21 两天 |
| 17 | `Custom API` 管不了列头 | **否——只读码；且已由 V-30 判定为说过头（见 §七）** | 与原报告同一弱点；签名与上下文只支持「**返回值**管不了列」，不支持更强的「管不了列」 |

---

## 四、发现的说过头与不准确处（含**不影响判定**的）

| # | 出处 | 原文 | 实测 | 影响判定？ |
|---|---|---|---|---|
| 1 | V-25 回报 §2、待验表 | `segment.label` 取自 `Column Break` 的 `display_name`（**`:1712` 一带**） | **`:1712` 是空行。** 实际赋值在 **`:1570`**（`_organize_into_segments`），`:1543` 初始化 | 否。机制对，行号错 |
| 2 | V-25 回报 §2、待验表 | 「引擎**必然**在其后追加 ` - {期间}`」 | **不完全准确**。项目列 `seg_N_account` 拿到**逐字原值**（`:1724`），**只有期间列**被追加（`:1727`）。因法定要的是数值列，**结论仍成立** | 否，但表述须改 |
| 3 | 待验表、V-25 回报 | 出厂模板「3 个 `Column Break`／**2 个 `Section Break`**」 | **3 个 Section Break**（idx 1／45／53）。原探针自己的 json 里 `section_breaks` 就是 3 条，叙述写成 2 | 否，纯笔误 |
| 4 | V-26 回报 §1 | 「`华东弹簧` 损益类 GL **仅 3 条**、全在 2026-09-21」 | 损益 GL 3 条为真。但**全站 GL 22 条中 8 条是 `is_cancelled=1`**，未取消的 14 条，分布在 **09-20 与 09-21 两天**。「全在同一天」只对损益类成立，对全站不成立——**而这个两天分布正是我补救判据的基础**，原探针没利用它 | 否，但漏掉了可用的判据 |
| 5 | V-26 回报 §2 | 「营业成本（**325.5**）」 | 是**两个科目的净额**：`销货成本` 325.77 ＋ `结转库存的费用` −0.27。直接对 GL 明细会对不上 | 否 |
| 6 | V-26 回报 §3 | 「那个开关只在被显式传入时才拉平全表」 | 结论**正确**，但原报告是**推论**、未跑。我实跑坐实：传 0 或 1 都会让两列相等 | 否，反而加固 |
| 7 | V-26 回报 §4 | `Monthly` 下「共 **26** 个可见列」 | 两段模板 26 列**为真**（原探针自己的 json 可核）。但这是**段数的函数**：我的三段模板是 **39** 列。「26」不是引擎属性，是「2 段 × 13」 | 否，但易被误读为固定值 |
| 8 | 两处 | 显式传 `accumulated_values=0` 会多出 `seg_N_total` 列（39→42） | 原报告完全未提。只在显式传入时出现，真实路径不会 | 否 |
| 11 | V-25 回报 §3、待验表 | 「`Custom API` **管不了列**的数量与名字」 | **表述过强。** `:1185` 的签名只支持「**返回值**管不了列」——但它把 `self.period_list` **本体**传给了被调方（`periods=self.period_list`），被调方可就地修改。后续 V-30 实测证实：改返回值不行，**就地改 `periods` 列表可以改列**。准确表述是「Custom API 的**返回值**是行级取数出口」 | 否（V-25 命题问的是**模板层**，Custom API 属自写代码接管列轴，不是模板层入口） |
| 12 | V-26 回报 §四·补 | 「② 上年末做过年结 PCV」则 `Closing` = 本年累计 | **已被后续 V-27 证伪**：已提交年结 PCV 后 A／B 两组逐位相同，损益 `Closing Balance` **不**重新起算。见 §七 | 否（V-26 判定不变），但**「能用」的边界比原报告与我都写得更窄** |
| 9 | 待验表「站点安全」 | 「全部写入都在事务内并 `rollback()`」 | **确认为真**，我还额外查了原探针 V-25 建 FY2025 留下的 **redis 缓存残留**（`FiscalYear.on_update` 会删 `fiscal_years` 缓存键）：`cache_hash_fiscal_years` = **空**，`*fiscal*` 键 **0 个**，`_get_fiscal_years()` 只返回 2026，无幻影年度。**回滚干净，无缓存污染** | 否，加固 |
| 10 | V-26 回报 §四·补 | 「② 上年末**做过年结 PCV** 把损益科目结平」则 Closing = 本年累计 | **未验，且有一处原报告没注意的复杂性**：`_apply_standard_filters()` (`:723-735`) **主动排除 PCV 产生的分录**（`~is_pcv | account.isin(closing_heads)`，注释自陈「BS 留存收益保留、P&L 冲回分录被滤掉」）。**这个排除逻辑与「PCV 让累计从本年起算」是否兼容，我没能验证**（受 §1.7 安全阻断）。原报告把这条写成「代码路径存在（`:536-547`）」——**该行号区间落在 `_get_opening_balances` 内，引用无误**，但它**只覆盖了读 PCV 的那一半**，没覆盖 `:735` 这个过滤器 | 否（本来就标为未验），但**未验项比原报告描述的更复杂** |

---

## 五、复核建议（本次审计自身的边界与拿不准处）

### 5.1 我这次审计的边界

1. **单站点／单公司／单会计年度／GL 仅两天有账。** 与原探针同一个观察窗，我**没有扩大数据面**（扩大就得写 GL，不在只读授权内）。凡「多期行为」的结论都只是**期内**证据加**代码结构**推断。
2. **年结 PCV 整条路径未碰**，理由是**已查证的硬阻断**（`frappe.enqueue` ＋ `frappe.db.commit()`）。这是「配模板」路线**最关键的未验项**，两次独立审计都没能验——**它需要一个可丢弃的站点，不能在演示站点上做。**
3. **`Custom API` 仍是纯读码**（我和原探针同一弱点）。任务书说另有探针在跑，我未重复。
4. **我没有从 HTTP／UI 层跑过报表**，只走了 `FinancialReportEngine().execute()` 这个 Python 入口。查了前端链路（`query_report.js` 的 `set_route_filters` 只对**已声明的 filter** 生效、`get_filter_values` 只回传**已声明的 filter**）⇒ 浏览器用户无法注入未声明的 `accumulated_values`。但**这一条是读码结论，未实跑**。另：`Report.get_data()` 路径上有 `frappe.db.commit()`（`frappe/core/doctype/report/report.py:511`，`enable_prepared_report`）与 `frappe.enqueue`（`query_report.py:418`），**故我刻意不走那条路**——若将来要从 HTTP 层验，须先评估这两处。
5. **我改动了 5 个进程内方法**（`_get_opening_balances_from_gl` 等三个包了探针层）以实录分支。包装在 `finally` 里已还原，且是**进程内**行为，不影响站点。但须声明：**被包装的运行结果来自被包装的代码**——我只在外层加了记录，未改返回值（`return _orig_...(self, ...)`），可从 `d-runtime.json` 的数值与未包装的 `e-rowlevel.json` 逐位一致来交叉印证。

### 5.2 拿不准处

1. **`Closing Balance` ↔「本年累计金额」的映射仍是人选的。** 我核实了原报告这条自陈为真：上游没有任何字段叫「本年累计」。我把**代价**查得更清了（滚动余额、依赖年结、且年结路径本身还有 `:735` 的 PCV 排除逻辑没验），但**是否接受这个代价是判断题**，不在本审计射程。
2. **「多月累计是否正确递增」这个缺口，我认为比两份原报告写的更要紧。** 原报告把它列为「站点只有一个月有账，验不了」，语气像次要边界。但它与 §5.1 第 2 条（年结 PCV）合起来，**恰好是「配模板」路线唯一没被任何证据覆盖的区域**，而那正是法定利润表「本年累计金额」列的核心语义。我能证明的是「引擎在做滚动求和」（结构性），**不能证明「跨月累计在任意数据下都对」**。
3. **`26 列` 这个数字我建议 B 步不要引用。** 它是「段数 × (期间数+1)」的一个实例。要引用应写成公式或写清前提。
4. **`V25-out/column-headers.json` 里 `get_columns_Yearly` 的 `-2025`／`-2026`**（非 `period_labels_*` 那两键）也带前导横线，成因同 §2.5。原报告只声明了 `period_labels`，**没提 `get_columns_*` 两键也被污染**。看 json 的人若直接读 `get_columns_Yearly` 会再被绊一次——**这两键应视为无效数据，真实列头看 `engine_columns_two_FY_yearly`。**

### 5.3 对 `SH-P1S4002` 两条判据的复核后表述

| 判据 | 复核后 |
|---|---|
| ① 列头逐字合规 | **缺口成立。** 段标签那一半由模板控制、**能写成逐字中文**，且**项目列能拿到逐字原值**；但**放数字的期间列必然带 ` - {期间}` 后缀**（仅多段时如此，单段无后缀）。⇒ 法定两列做不到逐字合规 |
| ② 同表一列累计一列单月 | **不成立（命题被证伪），且证伪比原报告更扎实**：`balance_type` 经单段三类型实测确认为**行级**；三个 balance 值在 `PeriodValue` 上并存；累计语义经「closing = opening + movement」独立坐实，已排除「重复上次值」这个替代解释。**附带条件依旧**：`Closing Balance` 是滚动余额，等于「本年累计」须靠年结 PCV，而**那条路径两次审计都未验** |

---

## 六、探针与原始输出清单

| 文件 | 作用 | 写入 |
|---|---|---|
| `Rev-P1S4R2-a-facts.py` → `Rev-out/a-facts.json` | 基线、裸 SQL 重算 1045/325.5/719.5、DocField／DocType 元数据、出厂模板行结构 | 无 |
| `Rev-P1S4R2-b-cache.py` → `Rev-out/b-cache.json` | V-25 回滚后的 redis `fiscal_years` 缓存残留检查 | 无 |
| `Rev-P1S4R2-c-inject.py` → `Rev-out/c-inject.json` | 7552 文件全量扫 ＋ DB 侧全部注入口 ＋ 行号逐条核对 | 无 |
| `Rev-P1S4R2-d-runtime.py` → `Rev-out/d-runtime.json` | 9 次真引擎运行：复现 V-26／判别器／seg2 分支实录／V-25 六列／中文段标签／显式传开关 | 事务内，已回滚 |
| `Rev-P1S4R2-e-rowlevel.py` → `Rev-out/e-rowlevel.json` | 单段混合 balance_type（行级 vs 段级判别器）＋ 单段列头 | 事务内，已回滚 |

五份探针源码**全部 ASCII**（中文只以 `\uXXXX` 出现，实测 `nonascii_bytes = 0`），符合纪律。
**无 heredoc**（中途试过一次，被 GBK 坑清空了文件，已改回 Write 工具重写——此坑与 MEMORY.md 里已记的那条一致）。

**站点影响声明**：五份探针**全部写入动作只有 4 次 `insert()`**（3 张临时 FRT ＋ 1 个 Fiscal Year），全在事务内、`finally` 里 `rollback()`。**无一处 `delete`／`frappe.delete_doc`／`db_set`／`set_value`／`set_single_value`／`log_error`／`commit`／`enqueue`**，**未跑任何「清理」步骤**（只靠 rollback）。**`Error Log` 未被本审计的任何探针读或写**。

---

## 七、与后续探针（V-27／V-30）的关系 —— 本报告须让位的两处

本审计完成后另有两条结果到达，**都落在我 §三 表里标为「未能确认」的那两格上**。此处如实记录，避免本报告与它们相互矛盾：

| 后续结论 | 对本报告的影响 |
|---|---|
| **V-27 = `no-go`**：已提交的年结 PCV **并不**让损益 `Closing Balance` 重新起算，A／B 两组逐位相同 | **补上了我 §三 第 15 项、§5.1 第 2 条的空缺，且方向是证伪。** ⇒ V-26 回报 §四·补里那句「② 上年末做过年结 PCV 则 Closing = 本年累计」**已被证伪**；我 §四 表第 10 行只说「未验、且比原报告描述更复杂」（并点出 `:735` 主动排除 PCV 分录这个复杂性）——**现在应直接读作：该条件不成立**。⇒ **`Closing Balance` 这个累计列从第二个会计年度起取到的是错数。** 我 §5.2 第 2 条说「这是配模板路线唯一未被覆盖的区域」，**该区域现已被覆盖，答案是否**。本报告对 V-26 的「成立」判定不变（原命题「同表做不到两列」确实被证伪），但**「能用」的边界比我写的更窄** |
| **V-30**：`Custom API` 的**返回值**确实管不了列，**但就地改动 `periods` 列表能改列** | **我 §三 第 17 项、§2.6 的自陈不足被坐实，且结论须收窄。** 我只核了 `:1185` 的签名（`values` 绑定为扁平数值列表），那**只支持「返回值管不了列」**。V-25 回报与待验表写的「`Custom API` **管不了列**」——**表述过强**，因为 `frappe.call(method, filters=..., periods=self.period_list, row=row)` 把 `self.period_list` **本体**传了进去，被调方可就地改它。⇒ 应加入 §四 的说过头清单。**但这不翻转 V-25 的判定**：V-25 命题是「**模板层**能否控制列头成逐字中文」，而 `Custom API` 那条属「自己写代码接管列轴」，不是模板层入口 |

**⇒ 两条后续结论都不翻转本报告的两个判定，但各收窄一处表述。** 我 §三 表里那两格「未能确认」的理由也随之更新：第 15 项从「缺手段」变成「**我缺手段，但已由他人证伪**」；第 17 项从「只读码」变成「**只读码，且读得出的结论比原报告写的弱**」。
