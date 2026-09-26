# S4-己 方案对比：抄 zelin 报表代码 vs 按官方规范自建

> 调查代号「己」。命题：项目负责人质疑「绕 zelin 的坑、且坑无法事先估」，提出
> **不完全照抄 zelin 代码、只作思路参考，结合财政部等官方规范按标准方式构建报表逻辑**。
> 本文回答：两条路各自的代价与收益。
>
> 硬约束：只读。未改 `Reference/`、`frappe-bench/`；未跑 bench、未建公司、未动站点；无 git 操作；
> 未读 `Reference/saoxia-erpnext_china`。
>
> **状态：进行中（边查边写）**

---

## 0. 前置：三份清单的已读要点

| 来源 | 关键结论 |
|---|---|
| `Spike/S4-G1a-财税核心清单.md` | 266 节点科目表已实测可信；缺陷集中在 600 行胶水层；**§3.8 指出 zelin 置 `ignore_chart_of_accounts=True` 把 v16 新增的 `sync_financial_report_templates` 一起跳过了**，作者称其为「本批对做中国财税影响最大的一条」 |
| `Spike/S4-G1b-DocType与Report清单.md` | 三张报表是真实现；**§5-D 单栏 13 列疑取同值（未实测）**；**§5-E 两份 `example_data.json` 的科目号必须与本项目科目表逐一对齐，否则报表数字全 0 且不报错（静默失败）** |
| `Spike/S4-G1c-资源清点与缺陷核实.md` | 9 条缺陷逐条核实；缺陷 5（`get_chart` 返回 56761 字符原文）已可执行复现；**N-2 `Common Accounts` 是半截改造** |

**G1b §5-E 这一条是本次对比的关键**：zelin 报表的正确性依赖「客户的科目号配置」，而那份配置是则霖自家客户的，
抄过来必须逐行改。也就是说 **zelin 的报表代码抄过来并不自带「能算对」的行次配置**。

---

## 1. 官方规范的事实

（待填）

## 2. v16 原生 `Financial Report Template` 引擎能力评估

（待填）

## 3. 三条路对比

（待填）

## 4. 事实性结论

（待填）

## 5. 复核建议

（待填）

---

## 1. 官方规范的事实（进行中）

### 1.1 现金流量表要不要编（**已有首个权威指向，待二次印证**）

| 事实 | 来源 | 可信度 |
|---|---|---|
| 《小企业会计准则》**第九章 财务报表**，「财务报表至少应当包括下列组成部分：（一）资产负债表；（二）利润表；（三）现金流量表；（四）附注。」 | `book.hjyweb.cn/accounting/se/cass/00.html`（会计便利店知识库转载财会〔2011〕17号正文） | 中（非官网原文，是转载。**须二次印证**） |

⇒ 初步结论：**现金流量表在必编之列**（第九章，条文编号待核）。这否掉了「若不强制要求、现金流工作量性质就变了」这个假设的乐观分支。

### 1.2 「2024」这个年份（**进行中**）

已核实的否定证据：
- **财政部会计司「政策发布」栏目（`kjs.mof.gov.cn/zhengcefabu/`）在其列出的 2023–2026 条目中，无任何《小企业会计准则》的修订/修改/废止/新版发布。** 该栏目同期发布的是注册会计师法、企业会计准则第30号、可持续披露准则等，**不含小企业会计准则**。
- 市面上确有「小企业会计准则 2024年版 / 2025年版」的**图书**（立信会计出版社等，见 UIBE 图书馆 OPAC 条目）—— 这是**出版物年度版次**，不等于准则本身被修订。

⇒ 倾向结论：**准则正文仍是 2011 年的财会〔2011〕17 号，从未修订**；「(2024)」是 **zelin 自己的科目表文件命名**，不是准则版本号。待补最终印证。

### 1.3 现金流量表必编 —— **已二次印证，官方政府来源**

| 事实 | 来源 | 可信度 |
|---|---|---|
| 《小企业会计准则》**第七十九条**：「小企业的财务报表至少应包括下列组成部分：资产负债表、利润表、现金流量表、附注。」并明确现金流量表**编报期为月报、年报** | **上海市财政局**（政府官网）`czj.sh.gov.cn/zys_8908/hdjl_9149/zxft_9164/20230616/529d5fa528994c179cd9c6894cfbe7ce.html`，2023-06-16《〈小企业会计准则〉——会计核算中应关注的有关问题》 | **高（省级财政局官网）** |
| 同条文的另一独立转载 | `book.hjyweb.cn/accounting/se/cass/00.html` | 中 |

⇒ **结论确定：小企业会计准则下现金流量表是必编报表，无免编例外。** 该政府页面明确「未提及任何可简化或免编的情形」。
**这否掉了任务书里「若不强制要求、现金流那部分工作量性质就变了」的乐观分支** —— 现金流量表必须做。

---

## 2. v16 原生 `Financial Report Template` 引擎能力评估（执行端已查，读码结论，**未实测**）

> 证据基于 `frappe-bench/apps/erpnext/erpnext/accounts/doctype/financial_report_template/financial_report_engine.py`（2044 行）
> 与 `financial_report_validation.py`。以下每条均给出 file:line。**全部为静态读码，未跑站点。**

### 2.0 任务书那条关键说法：**成立，且读取端确实是通用的**

任务书说 `financial_report_validation.py:403` 是 `set(self.account_meta._valid_columns)` ⇒ Account 任何列都能当筛选条件。**核实成立**：

- **定义端/校验端**：`financial_report_validation.py:401-403` `AccountFilterValidator.__init__`，
  `self.account_fields = account_fields or set(self.account_meta._valid_columns)`；
  `:467-469` 用它做字段白名单，字段名不在 set 里就 throw `Field '{0}' is not a valid Account field`。
- **读取端（关键，这才是本项目七次翻车的那一侧）**：`financial_report_engine.py:867-879` `_build_simple_condition`
  用 **`getattr(table, field_name, None)`** 动态取 pypika 列 —— **没有写死字段名分支，没有按列序号取值**。
  算子来自 frappe 全量 `OPERATOR_MAP`（`frappe/database/operator_map.py:138-161`）。

⇒ **两侧都查过，通用筛选成立。** 这是本次调查最重要的一条正面事实。

### 2.1 六个子问题逐个答

| # | 子问题 | 答案 | 证据 |
|---|---|---|---|
| 1 | **左右双栏**能不能表达 | **能，且是真双栏**（不是仅分列数据） | 执行端有完整处理链：`:1213-1214` Column Break 产占位 → `SegmentOrganizer._organize_into_segments`(`:1539-1581`) 切段 → `:1385-1388` 段数决定 formatter → `MultiSegmentFormatter.get_columns`(`:1713-1732`) **为每段复制一整套列**、字段名加 `seg_N_` 前缀 → `format_row`(`:1701-1711`) 按行下标横向配对 → 前端 `erpnext/public/js/financial_statements.js:92-104` 正则解析段号。`horizontal_balance_sheet_(columnar)` 有三处 Column Break（`:32`/`:418`/`:754`）。**代价**：每段各自带一个「项目」列，布局是 `[项目\|金额…][项目\|金额…]` |
| 2 | **行次名称改中文** | **直接把中文写进模板 `display_name` 即可，不走译名机制** | `:1631-1647` `_get_row_data("display_name")` → `:1646-1647` 直接进输出，**全程无 `_()` 包裹**。其它消费点 `:1528`/`:1570`/`:1834`/`:1551` 同样不过翻译。唯一过 `_()` 的是 `:1788`，那是「科目明细子行」翻译 Account 自己的名字，与模板 `display_name` 无关。**反面**：同一套模板无法靠译名文件多语言切换 |
| 3 | **合计公式** | **够用，且支持多层合计** | 求值用 `frappe.safe_eval`（`:1343-1355`），可用函数 `abs round min max sum sqrt pow ceil floor`（`:1313-1323`），支持 Python 三元表达式（自带模板实证 `horizontal_balance_sheet_(columnar).json:915`）。真实合计样例：`:683` `A_STOCK + A_TRADE_RECEIVABLES + A_OTHER_RECEIVABLES + A_ST_INVESTMENTS + A_CASH_BANK + A_OTHER_CA` —— 与「流动资产合计 = 货币资金 + 应收账款 + …」完全同型。多层合计（合计的合计）靠**拓扑排序**（`:1267-1301` Kahn）支持，`:725` 即是。环检测在保存时报错（`financial_report_validation.py:240-284` 三色 DFS）。**作用域全局、允许前向引用**（`:1133` 单一平坦字典；`:1239-1265` 分类+拓扑而非按行序）|
| 4 | **一行汇总多个科目** | **能，三种方式** | ① 多值 in：`["account_number","in",["1001","1002","1012"]]` → `:879` `func_in` → `isin`（`operator_map.py:151`）② 多条 or：`{"or":[[...],[...]]}` → `_build_logical_condition`(`:881-904`)，`reduce` 且 **and/or 可递归任意深度**(`:890`) ③ 前缀 like。**坑**：`:876-877` 值里没 `%` 会自动改成 `%值%` 两侧通配 ⇒ 纯前缀必须自己写 `1001%`，否则 `1001` 变 `%1001%` 会误匹配 `21001`。聚合在 Python 侧（`:409-428`），非 SQL SUM |
| 5 | **现金流量表**与中国直接法差多少 | **引擎做不了直接法** | 自带 `standard_cash_flow_statement_(ifrs)` 是**间接法**（`:35` 从 Income/Expense 起算，`display_name`=`Profit before tax`；`:86` 折旧调整；`:188/:205/:222` 营运资本变动），走的是同一套 Account Data。**引擎无按「现金科目的对方科目」分类取数的能力**：`_get_gl_movements`(`:642-677`) 只 `select(gl_table.account)` + `groupby(account)` + `Sum(debit-credit)`；**无 GL Entry 自连接、无 `against`/`voucher_no`/`party` 引用（engine 内 grep 零命中）、无凭证级遍历**；`_parse_account_filter` 筛的是 **Account 表不是 GL Entry** |
| 6 | **`account_category` 要不要逐个贴标签** | **不必贴。按科目号取数可行** | `account_category` 在引擎里**无特殊地位**：只出现在 `FormulaFieldExtractor`(`:907-953`) 与 `FormulaFieldUpdater`(`:956-1029`) 两个与取数无关的工具类（用于模板导出写 `account_categories.json` 固件、以及分类重命名批改模板）。**取数路径完全不碰它** —— `_parse_account_filter` → `build_condition` → `_build_simple_condition` 对所有字段一视同仁。`account_number` 是 Account 真实列（`account/account.json:56`），在 `_valid_columns` 内。ERPNext 自己的测试覆盖了按号取数：`test_financial_report_engine.py:1362`（`'["account_number","like","1000"]'`）、`:1366-1369`（`>= > <= <`）、`:1527`（`'["account_number","like","%100%"]'`）|

**⇒ 第 6 问的答案直接砍掉一大块工作量**：不需要给 266 个科目逐个贴 `account_category`。
这同时意味着 **G1a §3.2／§3.8 那条「zelin 漏 `account_category`、绕过 v16 财报模板同步」的严重度要下调** ——
漏 `account_category` 不妨碍用原生引擎按科目号配中国报表。（`sync_financial_report_templates` 被跳过仍是问题，但那是另一回事。）

### 2.2 引擎的两个硬阻断（**对方案选择是决定性的**）

#### 阻断一：资产负债表「年初余额 / 期末余额」并排两列 —— **原生引擎做不到**

列定义**不由模板控制**，而是复用旧函数（`:1414-1422`）：
```
base_columns = get_columns(periodicity, period_list, accumulated_values, company)
```
`get_columns` 在 `erpnext/accounts/report/financial_statements.py:663-724`：固定产 `account` 列，然后
**`for period in period_list` 每期一个 Currency 列**（`:702-711`）。**模板里没有任何字段能定义列。**

关键约束：`balance_type`（Opening / Closing / Period Movement）是**行级属性**（`financial_report_row.json:66-72`），
一行只用一个 balance_type（`:419`）。**列轴是时间，不是 balance_type。**

⇒ 中国资产负债表法定的「年初余额 / 期末余额」是**同一期间的期初与期末**，
引擎找不到把 balance_type 映射成列的机制。**这是原生引擎表达中国 BS 格式的硬缺口。**
（利润表「本期金额 / 上期金额」**没有这个问题** —— 那是两个期间，天然两列。）

#### 阻断二：现金流量表直接法 —— **原生引擎做不到**（见上表第 5 问）

唯一逃生口是 `Custom API` 行（`:1178-1199`）：自己写白名单且允许 GET 的方法返回各期数值，
签名 `method(filters=..., periods=..., row=...)`，须返回与期数等长的数值列表。
**但那等于现金流取数逻辑全部自己实现，模板只负责排版。**

### 2.3 引擎的两个额外事实（一好一坏）

**好：性能形态比 zelin 好一个数量级（结构上明确，未实测耗时）**

引擎**先汇总全模板需求再批量查**：`collect_financial_data`(`:306-317`) 收集科目 → `collect_all_data`(`:377-391`)
把所有行的科目并成一个 `all_accounts` **只调一次** `fetch_account_balances` → `_get_gl_movements`(`:642-677`)
**一条 SQL 用 `Case().when(posting_date between ...)` 为每期生成一个 `Sum` 列**、`groupby(account)`。
总 SQL 约 **3~4 条，与模板行数、科目数无关**。期初还优先用 `Period Closing Voucher` + `Account Closing Balance`
快照（`:539-562`）并单独补缺口（`_get_gap_movements`,`:623-640`），避免全历史扫 GL。

对比 zelin BS 报表：**对每个科目调一次 `get_balance_on`（N 次 SQL）**（G1b §1.5 第 ③ 条）。

**坏：「科目号配错时静默出 0」这个毛病，原生引擎也有**

`financial_report_validation.py` 是**保存时（design-time）**校验，能查 14 类问题（reference_code 格式/重复、
缺 balance_type、循环依赖、引用不存在的 code、括号不配对、dummy 值试算、筛选 JSON 语法、
**筛选字段名不是 Account 合法列**、算子非法、in 值非 list、Custom API 未白名单…）。

**但查不出「筛选合法而命中零个科目」**。静默出 0 有四条路：
1. 筛选合法但零命中（如写 `1001` 而实际科目号是 `100101`）：`_parse_account_filter` 返 `[]` → `:387-388` 提前返回空 summary → `_process_account_row`(`:1168-1170`) `account_summary.get(ref_code, [0.0]*N)` ⇒ **全 0 无提示**
2. 筛选校验失败（导入固件时 `ignore_validate=True`，`financial_report_template.py:189`）：`build_condition`(`:840-846`) 只 `log_error` 后 return None ⇒ 全 0，**错误进 Error Log，界面看不到**
3. 公式求值异常：`:1350-1355` 捕获 → `log_error` → 返 0.0
4. Custom API 抛异常：`:1192-1194` 捕获 → 返全 0

⇒ **这与 zelin 的已知毛病（G1b §5-E「科目号不对齐则数字全 0 且不报错」）完全同型，原生引擎并没修好。**

唯一相关辅助是**设计期 UI 工具** `get_children_accounts(..., missed=True)`(`:1046-1116`)，
能在模板编辑界面列出**未被任何筛选覆盖的科目** —— 人工核对用，**运行时不调用**。
⇒ 无论走哪条路，「证明报表算对了」都**必须自己建验证手段**，不能靠引擎报错。

---

## 1（续）. 官方规范的事实 —— 报表格式与科目对应

### 1.4 资产负债表法定格式（**账户式左右双栏**，已核实）

表头栏目：**左栏**「资产 \| 期末余额 \| 年初余额」；**右栏**「负债和所有者权益（或股东权益） \| 期末余额 \| 年初余额」。
来源：`zkemu.com/acc1/bb/zcfzb/`（2013 小企业会计准则专题站）；格式与
`book.hjyweb.cn` 转载的附录一致。可信度：中（两个独立来源互证，非官网原文）。

| 左栏（资产） | | 右栏（负债和所有者权益） | |
|---|---|---|---|
| 货币资金 | | 短期借款 | |
| 短期投资 | | 应付票据 | |
| 应收票据 | | 应付账款 | |
| 应收账款 | | 预收账款 | |
| 预付账款 | | 应付职工薪酬 | |
| 应收股利 | | 应交税费 | |
| 应收利息 | | 应付利息 | |
| 其他应收款 | | 应付利润 | |
| 存货（下含原材料/在产品/库存商品/周转材料明细） | | 其他应付款 | |
| 其他流动资产 | | 其他流动负债 | |
| **流动资产合计** | 合计 | **流动负债合计** | 合计 |
| 长期债券投资 | | 长期借款 | |
| 长期股权投资 | | 长期应付款 | |
| 固定资产原价 | | 递延收益 | |
| 减：累计折旧 | | 其他非流动负债 | |
| 固定资产账面价值 | 小计 | **非流动负债合计** | 合计 |
| 在建工程 | | **负债合计** | 合计 |
| 工程物资 | | 实收资本（或股本） | |
| 固定资产清理 | | 资本公积 | |
| 生产性生物资产 | | 盈余公积 | |
| 无形资产 | | 未分配利润 | |
| 开发支出 | | **所有者权益（或股东权益）合计** | 合计 |
| 长期待摊费用 | | | |
| 其他非流动资产 | | | |
| **非流动资产合计** | 合计 | | |
| **资产总计** | 合计 | **负债和所有者权益（或股东权益）总计** | 合计 |

（`book.hjyweb.cn` 那份给出的部分行次号：货币资金 1、短期投资 2、应收票据 3、应收账款 4、预付账款 5、
应收股利 6、应收利息 7、其他应收款 8、存货 9、**流动资产合计 15**、长期债券投资 16、
**固定资产账面价值 20**、**非流动资产合计 29**、**资产总计 30**；
右栏 短期借款 31、应付票据 32、应付账款 33、预收账款 34、应付职工薪酬 35、应交税费 36、
应付利息 37、应付利润 38、其他应付款 39、**流动负债合计 41**、长期借款 42、
**实收资本 48**、**所有者权益合计 52**、**负债和所有者权益总计 53**。
⇒ **行次号左右连续编号（1–30 左栏、31–53 右栏），中间有跳号留给明细行。**）

### 1.5 利润表法定格式（已核实）

表头栏目：**项目 \| 行次 \| 本年累计金额 \| 本月金额**。来源 `zkemu.com/acc1/bb/lrb/`，可信度中。

| 行次 | 项目 |
|---|---|
| 1 | 一、营业收入 |
| 2 | 减：营业成本 |
| 3 | 税金及附加 |
| 4–10 | 其中：消费税／营业税等税费明细 |
| 11 | 销售费用 |
| 12–13 | 其中：商品维修费／广告费等 |
| 14 | 管理费用 |
| 15–17 | 其中：开办费／业务招待费／研究费用 |
| 18 | 财务费用 |
| 19 | 其中：利息费用 |
| 20 | 加：投资收益 |
| **21** | **二、营业利润**（合计行）|
| 22 | 加：营业外收入 |
| 23 | 其中：政府补助 |
| 24 | 减：营业外支出 |
| 25–29 | 其中：坏账损失等明细 |
| **30** | **三、利润总额**（合计行）|
| 31 | 减：所得税费用 |
| **32** | **四、净利润**（合计行）|

**注意**：利润表栏目是「**本年累计金额 / 本月金额**」，**不是**任务书假设的「本期金额/上期金额」。
这一点对 v16 引擎可行性的判断有影响（见 §2 补正）。

### 1.6 官方**有**行次与科目的对应关系（「填列说明」），已核实

《小企业会计准则》附录的报表部分带**逐行填列说明**。实例（`gaodun.com/shiwu/30789.html` 引原文）：

> **货币资金**：「反映小企业库存现金、银行存款和其他货币资金的合计数。本项目应根据'库存现金'、'银行存款'和'其他货币资金'科目的期末余额合计填列。」
>
> **存货**：「本项目应根据'材料采购'、'在途物资'、'原材料'、'材料成本差异'、'生产成本'、'库存商品'、'商品进销差价'、'委托加工物资'、'周转材料'、'消耗性生物资产'等科目的期末余额分析填列。」
>
> **生产性生物资产**：「应根据'生产性生物资产'科目的期末余额减去'生产性生物资产累计折旧'科目的期末余额后的金额填列。」

可信度：中高（头部财会培训机构引准则原文，与准则附录体例吻合）。

**⇒ 这一条对方案选择极其关键**：官方**已经给出了「一行 ← 哪些科目」的权威映射**。
也就是说「按官方规范自建」**不是从零猜**，而是**照抄一份官方已写好的映射表**。
注意「存货」用的是「**分析填列**」——含判断成分，不是纯加总；「生产性生物资产」是**减法**（原价 − 累计折旧）。

### 1.7 「2024」这个年份 —— **结论：不是准则修订年份**

| 证据 | 结论 |
|---|---|
| 财政部会计司「政策发布」栏目（`kjs.mof.gov.cn/zhengcefabu/`）列出的 2023–2026 条目中**无任何《小企业会计准则》的修订/修改/废止/新版发布**（同期发布的是注册会计师法、企业会计准则第30号、可持续披露准则等） | 准则正文未被修订 |
| 上海市财政局 2023-06-16 的答疑仍直接援引**第七十九条**原文 | 条文编号未变，仍是 2011 年版 |
| 市面「小企业会计准则 2024年版 / 2025年版」是**图书版次**（立信会计出版社等，见 UIBE 图书馆 OPAC） | 出版物年度版次，非准则修订 |

⇒ **准则正文仍是财会〔2011〕17 号，2013-01-01 施行，至今未修订。**
本项目 `小企业会计准则(2024)` 这个名字**来自 zelin 自己的科目表文件命名**
（G1a §3.14 已核实 `tax_template.json` 里并列三个准则键：`小企业会计准则`／`小企业会计准则(2024)`／`一般企业会计准则(2024)`，
且 zelin 另有 `cn_sme_coa.json` 的 `name` 就叫不带年份的 `小企业会计准则`）。

**⇒ 这是任务书「已确立的事实」里需要修正的一条**：「准则已定：小企业会计准则(2024)」
里的 `(2024)` **不对应任何官方准则版本**，它只是 zelin 那份科目表文件的标签。
真正确立的是「**执行《小企业会计准则》（财会〔2011〕17 号）**」。

### 2.4 补正：列轴问题我自己复核了一遍，结论比「做不到」更细（**两处要修正**）

我不满足于二手结论，亲自读了列定义与 `balance_type` 的两侧。核实：

- **列定义端**：`erpnext/accounts/report/financial_statements.py:663-724` `get_columns()` —— 固定产 `account`
  （+ 隐藏 `acc_name`/`acc_number`/`currency`），然后 **`for period in period_list` 每期一个 Currency 列**（`:700-711`），
  `periodicity != "Yearly"` 且 `accumulated_values` 为 0 时再加一个 `total` 列（`:712-721`）。
  **模板里确实没有任何字段能定义列**（已核 `financial_report_row.json` 全字段清单，见下）。
- **`balance_type` 是行级 Select**：`financial_report_row.json:66-71`，
  options = `Opening Balance` / `Closing Balance` / `Period Movement (Debits - Credits)`。
  `get_ordered_values(period_keys, balance_type)` **一行只用一个 balance_type、横扫所有期列**。
- **多段列标签**：`financial_report_engine.py:1713-1732`，段标签只能改 `account` 列的 label
  （`:1722-1724`）与给期列**加前缀**（`:1727-1728` `f"{segment.label} - {col['label']}"`），
  **不能把期列改名成「年初余额」**。
- 期列的 label 来自 `get_label()`（`financial_statements.py` 内），是 `YYYY` 或 `MMM YY-MMM YY` 形态，**不可配**。

#### 修正一：利润表的官方栏目不是「本期/上期」，而是「**本年累计金额 / 本月金额**」

任务书假设利润表要「本期金额 / 上期金额」两列 —— **官方格式不是这个**（§1.5 已核实）。
这使利润表的可行性判断**从「可行」下调为「半可行」**：

- 引擎的 `accumulated_values` 是**报表级过滤器**（`financial_statements.py:702-721` 与
  `financial_report_engine.py:1662`），**不是列级属性** ⇒ **同一张报表里无法一列累计、一列单月**。
- 能做到的近似：`periodicity=Monthly` + `accumulated_values=0` ⇒ 得到 12 个月列 + 1 个 `total` 列。
  这是「每月一列 + 合计」，**不是**法定的「本年累计 / 本月」两列。

#### 修正二：资产负债表「年初/期末」有一条**可绕**的路（不是绝对做不到）

上一轮结论是「做不到」。我复核后认为**更准确的说法是「数字能拿到，列头与列序不可配」**：

**可绕法**：`filter_based_on=Fiscal Year`、`from_fiscal_year=上一年`、`to_fiscal_year=本年`、`periodicity=Yearly`
⇒ 得到**两个期列**，前列是上年年末余额（**恰等于本年年初余额**）、后列是本年年末余额。
配合 Column Break 双栏 ⇒ 形状正是 `[资产项目\|上年末\|本年末][负债权益项目\|上年末\|本年末]`，
**与中国账户式资产负债表同形**。

**但三处不合规（均已核实，非推测）**：
1. **列头错**：label 是 `2025` / `2026`（`get_label()` Yearly 分支），**不是「年初余额」「期末余额」**，且不可配。
2. **列序反**：`get_period_list` 按日期**升序** append ⇒ 年初列在前、期末列在后；官方表是**期末在前、年初在后**。
3. **多带一栏项目名**：双栏模式下每段各带自己的 `account` 列（`:1722-1724`），
   ⇒ 实际是 `[项目\|年初\|期末][项目\|年初\|期末]`，官方表右栏项目名是有的，所以这条**其实合规**（撤回此条为不合规）。

⇒ **净结论**：资产负债表用原生引擎能得到**正确的数字与正确的双栏形状**，
但**列标题是年份而非「年初余额/期末余额」、且左右顺序相反**。
这属于**外观不合规，不是算不对**。若客户/税务要求表头逐字合规，就必须在引擎外再套一层
（改列头 = 写自己的 report 脚本包一层，已超出「纯配模板」的范围）。

**这比「做不到」轻，但仍是一处真实缺口。列为「未实测」——我只读了码，没跑过报表看实际列头。**

### 2.5 `Financial Report Row` 全字段清单（已核实，供判断表达力用）

`financial_report_row.json`：`reference_code`(Data) / `display_name`(Data) / `indentation_level`(Int) /
`data_source`(Select：`Account Data` `Calculated Amount` `Custom API` `Blank Line` `Column Break` `Section Break`，`:61`) /
`balance_type`(Select，`:71`) / `bold_text`(Check) / `italic_text`(Check) / `hidden_calculation`(Check) /
`hide_when_empty`(Check) / `reverse_sign`(Check) / `calculation_formula`(**Code**，label 是
「Formula or Account Filter」`:122` —— 同一字段兼作公式与科目筛选 JSON) / `include_in_charts`(Check) /
`color`(Color) / `fieldtype`(Select：Currency/Float/Int/Percent) / `advanced_filtering`(Check) + 若干 HTML/Break 排版字段。

**注意 `data_source` 有 6 个取值而非任务书说的 5 个 —— 多一个 `Custom API`**（`:61` 原文）。
这个第 6 个取值是本次调查发现的**最重要的逃生口**（见 §2.2 阻断二）。

### 2.6 老报表的让位机制（已核实，三处而非两处）

| 文件 | 原文 |
|---|---|
| `report/balance_sheet/balance_sheet.py:31-33` | `def execute(filters=None):` / `if filters and filters.report_template:` / `return FinancialReportEngine().execute(filters)` |
| `report/cash_flow/cash_flow.py:31-33` | 同形 |
| **`report/profit_and_loss_statement/profit_and_loss_statement.py:31-33`** | **同形（任务书未提这处，实际有）** |

⇒ 让位条件是**报表筛选器里选了 `report_template`**（`balance_sheet.js:12` 有该 filter，
`:24`/`:53` 用 `depends_on: "eval:doc.report_template"` / `"eval:!doc.report_template"` 切换其它筛选器显隐）。
**三张主表都能被模板完全接管**，不需要改上游代码 —— 这是「配模板」路线成立的前提，已两侧核实。

### 1.8 现金流量表：中国用**直接法**，但有「倒轧法」这条简易路（已核实，含一条对方案很关键的事实）

| 事实 | 来源 | 可信度 |
|---|---|---|
| 小企业现金流量表**主表采用直接法**，按现金流入/流出的主要类别列示（「销售商品、提供劳务收到的现金」等） | `xiexiebang.com`（《〈小企业会计准则〉施行后，小企业现金流量表编制的简易方法》）＋ `biaogedaquan.com` 模板预览互证 | 中 |
| 三大类：经营活动／投资活动／筹资活动 | 同上 | 中 |
| 另需「将净利润调节为经营活动现金流量」的**补充资料（附表，间接法口径）** | `xiexiebang.com` | **中低（单一来源，须复核）** |
| **实务上普遍用「倒轧法」**：「采用倒轧法，在其他类别、本类别其他项目填列完毕的基础上，再根据本期现金收入总额、现金付出总额，减除已填报各项目的合计数，直接倒推出本期销售、购买收付的现金」 | `xiexiebang.com` 引原文 | 中 |

**⇒ 倒轧法这条事实对方案选择很关键**：它说明直接法现金流量表**不必逐笔分析每张凭证的对方科目** ——
可以「先填能算的项目，剩下的用现金总额倒推」。这降低了自建现金流的难度，
**但它仍然需要「把现金收支按类别归集」这个动作**，而这正是 v16 原生引擎完全没有的能力（§2.2 阻断二）。

### 2.7 zelin 的 `Cash Flow` 四件套做的正是引擎做不到的那件事（已核实两侧）

对照 G1b §1.1／§2.5 的清点 + 我自查：

| 侧 | 事实 | 出处 |
|---|---|---|
| 取数端 | 从 **GL Entry** 按 `account_type in ('Cash','Bank')` 取**流水明细**（不是余额） | `cash_flow.py:101`（取现金类科目）、`:148-175`（取 GL Entry）|
| 分类端 | 每条流水带 `cash_flow_code`，由 `assign_default_cash_flow_code()` 按 Account／Customer／Supplier 上的 `cash_flow_code` 自定义字段**自动预填**，人工可改 | `cash_flow.py:192-199`／`:200-207`／`:212-223`；字段来自 `fixtures/custom_field.json` |
| 拆分端 | `Cash Flow Item.manual_split` 允许**一笔流水拆到多个编码** | `cash_flow_item.json:182-186`（但 §2.2 已核实其只读控制因 `evel:` 拼错而失效）|
| 小计端 | 按 `Cash Flow Code.cash_flow_type`（五个中文大类）与 `formula`（`type_subtotal`/`last_period_balance`/`above_subtotal`）求小计，跨月累计读上月 `yearly_amount` | `cash_flow.py:56-63`／`:73`／`:79-83` |

**⇒ 这是「凭证级分类 + 人工可调 + 按月归集」的直接法实现，v16 原生引擎在架构上就到不了这一层**
（引擎的取数对象是 Account 表与 `Sum(debit-credit)` 按科目 groupby，
`_get_gl_movements` 不 select `voucher_no`/`against`/`party`，无凭证级遍历 —— §2.2 阻断二）。

**这一条改变了「乙案只抄数据不抄逻辑」的成色**：
现金流量表这一块，**zelin 的 DocType 设计本身就是资产**，不是可以随手丢掉的胶水。
（其 230 行主逻辑的缺陷密度远低于 600 行胶水层 —— G1b 对 `cash_flow.py` 只列出 4 条「抄后改」，
且无一条是崩溃级：`:101` 大写 `"Company"` 在 MariaDB 下能跑、`FrappeTestCase` 已废弃、
`autoname` 用中文公司全名可能超长、依赖 fixtures 的三个 Custom Field。）

### 2.8 定义端（写入端）核实结果 —— **三条推翻既有假设的发现**

#### 发现一：**没有任何「科目筛选」专用字段**，筛选条件写在 `calculation_formula` 里（一字段两义）

| 侧 | 事实 |
|---|---|
| 定义端 | `financial_report_row.json:118-124`，`calculation_formula` 是 **Code** 字段，label 为 **"Formula or Account Filter"** |
| 读取端 | `financial_report_engine.py:836` `filter_formula = report_row.calculation_formula` → `:849` `ast.literal_eval` → `:858-904` 转 pypika 条件 |

⇒ `data_source="Account Data"` 时该字段是**筛选 JSON**；`data_source="Calculated Amount"` 时是**算术公式**。
**任务书说的「取数字段不限于 `account_category`」成立，但机制不是「有个筛选字段」，而是「筛选表达式写在公式字段里」。**

#### 发现二：**`advanced_filtering` 是服务端 no-op**（典型的「结构看着对、引擎不认」）

定义端 `financial_report_row.json:159-167` 有该 Check 字段；
读取端 `financial_report_validation.py:425` 把它传进 `_validate_filter_structure`、`:455` 收作形参、`:492` 递归继续传 ——
**但函数体 `:451-498` 内从未在任何条件判断里使用这个形参**。它只改客户端 UI
（`financial_report_template.js:55,65,120-123`）。

⇒ **这正是本项目七次翻车的同型陷阱，本次提前逮到了。** 配模板时不要指望这个开关有任何服务端效果。
（`filters_editor` HTML 字段同理：`:149-153` 是纯 UI 挂载点，**未找到任何 py 读取点**，不存值。）

#### 发现三：**`disable_default_financial_report_template` 不是函数，是局部布尔变量 + COA 元数据键**

任务书说它是 `financial_report_template.py:141-151` 的一个机制、「全仓零使用、未走过的路」。核实：

- 它是 `sync_financial_report_templates()` 内的**局部布尔变量**：`:141` 赋 False、`:145` 赋 True、`:150` 读取；
  同时是 **COA 字典的一个顶层键**（`:144` `coa.get("disable_default_financial_report_template", False)`）。
- 语义：若建账用的科目表 json **顶层**带 `"disable_default_financial_report_template": true`，
  则同步模板时**跳过 `erpnext` 这一个 app**（`:150-151`），让自有 app 的模板成为唯一来源。
  **它跳过的是整个 erpnext app 的模板同步**，不是逐个禁用、也不是把 `disabled` 置 1。
- **全 bench grep 只有 4 处命中，全在同一文件**（`:141`/`:144`/`:145`/`:150`）；
  再搜 `apps/` 下所有 COA json：**0 命中**。
  ⇒ 「全仓零使用」**在「没有任何 COA 设置该键、该分支永不为真」的意义上成立**，但它不是一个可调用的函数。

⚠ **陷阱**：`get_chart()` 对 `"Standard"` / `"Standard with Numbers"` 走硬编码分支
（`chart_of_accounts.py:107-118`），只有走到 `:119-127` 的文件扫描分支才会读到自定义 json ⇒
自定义 COA 必须落在 `.../chart_of_accounts/verified/` 下且名字不等于那两个保留名。

### 2.9 自带 6 份模板的实际内容（已逐行核实）

| 文件 | 行数 | `report_type` | rows | ColBreak | SecBreak |
|---|---|---|---|---|---|
| `standard_profit_and_loss_(ifrs)` | 418 | Profit and Loss Statement | 26 | 0 | 0 |
| `standard_balance_sheet_(ifrs)` | 824 | Balance Sheet | 53 | 0 | 0 |
| `standard_cash_flow_statement_(ifrs)` | 832 | Cash Flow | 48 | 0 | 0 |
| **`horizontal_balance_sheet_(columnar)`** | **993** | Balance Sheet | **64** | **3** | **3** |
| `horizontal_profit_and_loss_(columnar)` | 1008 | Profit and Loss Statement | 66 | 6 | 5 |
| `financial_ratios_analysis` | 1087 | **Custom Financial Statement** | 63 | 0 | 0 |

**⇒ 修正任务书一处**：任务书说 `Horizontal Balance Sheet (Columnar)` 有 **64 行定义** ——
准确说是 **64 个 row（子表行）**，json 文件本身是 **993 行**。64 是行数，对。
Column Break 在第 2 行（json `:32`，`display_name`=`Equity & Liabilities`）、
第 27 行（json `:418`，`display_name`=`Assets`）、第 49 行（json `:754`，无 display_name）。

**关键观察：自带 BS 模板 26 个 Account Data 行里，筛选条件几乎全是 `["account_category","=",...]`**
（如 `L_SHARE_CAPITAL` 用 `["account_category","=","Share Capital"]`），
另有少量混用 `account_name like` / `account_type` / `root_type in`。
⇒ **自带模板重度依赖 `account_category`**，但这是**它们自己的选择**，非引擎约束（§2.1 第 6 问已证）。
**直接套用自带 IFRS 模板到中国科目表上，每行都会静默出 0**（因中国表 `account_category` 全为 0 处）。

**自带模板附带 `account_categories.json`（147 行，29 个分类）**，全部英文 IFRS 口径
（Cash and Cash Equivalents / Trade Receivables / Stock Assets / Share Capital …）。

### 2.10 `Financial Report Template` 主表字段：**没有 company、没有 country、没有 is_default**

`financial_report_template.json`：`template_name`(Data, reqd+unique, `:19-24`) /
`report_type`(Select reqd，取值 `Profit and Loss Statement` / `Balance Sheet` / `Cash Flow` /
`Custom Financial Statement`，`:28-34`) / `module`(Link Module Def) / `rows`(Table) /
`disabled`(Check, default 0, `:58-64`)。

**后果（对「打开就是中国报表」这个诉求很关键）**：
- 模板全局、跨公司共享；公司来自运行时筛选器（`financial_report_engine.py:361`、`:453-454`）。
- **无 `is_default` ⇒ 没有自动顶替。** 三个 .js 里 `report_template` filter **都没有 `default` 键**
  ⇒ **用户每次跑报表都必须手动选模板**，否则看到的还是原生老报表。
  要做到「打开即中国式报表」，现成机制里**没有**办法，得另想（未找到方案）。
- `disabled` 的过滤**只在客户端下拉**（`balance_sheet.js:16` 的 `get_query`）；
  引擎 `execute` 内**未找到 disabled 校验**（⚠ 与 §2.2 引擎侧说的 `:277` 有 `template.disabled` throw 矛盾，
  **此处两个调查有分歧，列为待核**）。

### 2.11 模板装载机制：**幂等但单向，已存在的模板永不更新**

`sync_financial_report_templates()`（`financial_report_template.py:131-153`）：
遍历 `frappe.get_installed_apps()`（`:147`）→ 每 app 每 module 找
`<module_path>/financial_report_template/` 目录（`:161`）→ 先 `import_account_categories`（`:166`）
→ 再找 `<template_dir>/<template_dir>.json`（`:168-171`，**子目录名必须与 json 基名完全一致**）
→ `frappe.get_doc(...)` + `insert()`（`:186,:190`），
三旗全开 `ignore_mandatory` / `ignore_permissions` / **`ignore_validate`**（`:187-189`）。

**是否 force 覆盖：不。** `:185` `if not frappe.db.exists("Financial Report Template", template_name):` 才 insert。
⇒ **已存在的模板永不更新、永不覆盖。** 幂等，但**单向**：
升级 ERPNext 带来的模板修订不会同步到已有站点；反之**你改过的同名模板也不会被官方版本冲掉**。
⇒ **这对「升级存活性」是正面事实**：自配的中国模板不会被 bench migrate 冲掉。

⚠ **注意 `ignore_validate=True`**：模板 json 即使缺必填、筛选表达式非法也能装进去 ⇒
**固件导入路径绕过了全部 14 类校验**，错误只会在跑报表时静默出 0（§2.3）。

**自有 app 带模板的目录要求**（从路径拼法反推）：
```
erx_core/erx_core/<module>/financial_report_template/
    account_categories.json          # 可选，先于模板导入
    <template_dir>/<template_dir>.json   # 基名必须 == 父目录名
```
`<module>` 必须在 `modules.txt` 登记且 Module Def 存在（`:159`），否则整个 module 不被扫描。
命名须遵循 `frappe.scrub()` 规则（`_delete_template` 用它定位目录，`:73`）。

⚠ **两套解析器不一致**：校验用 `json.loads`（`financial_report_validation.py:421`，严格 JSON、必须双引号），
引擎执行用 `ast.literal_eval`（`financial_report_engine.py:849`，接受单引号）。
⇒ 自建模板 json **一律用双引号**，否则保存时报 `Invalid JSON format`（但走固件导入能绕过）。

### 2.12 `Company.on_update` 的同步调用点（已核实，解释了 G1a §3.8）

`erpnext/setup/doctype/company/company.py:339-350`：
```
if not frappe.db.sql("select name from tabAccount where company=%s and docstatus<2 limit 1", self.name):   # :341-345
    if not frappe.local.flags.ignore_chart_of_accounts:                                                     # :346
        frappe.flags.country_change = True                                                                  # :347
        sync_financial_report_templates(self.chart_of_accounts, self.existing_company)                      # :348
        self.create_default_accounts()                                                                      # :349
```
双重门禁：该公司下**尚无任何 Account** 且 `ignore_chart_of_accounts` 未置。
**且在 `create_default_accounts()` 之前执行** —— 顺序关键：Account Category 必须先存在，建科目时才能赋 `account_category`。

⇒ **这确证了 G1a §3.8**：zelin 置 `ignore_chart_of_accounts=True` 会把模板同步一起跳过。
**但严重度要下调**：另有一条无参调用点
`erpnext/patches/v16_0/update_account_categories_for_existing_accounts.py:19`
`sync_financial_report_templates()`（无参 ⇒ 一定会装 erpnext 自带 6 份模板），
且自有 app 的模板同步也不依赖建公司那一刻 —— 可以手工调、或走这个 patch 路径。
**「模板同步被跳过」不是不可恢复的损失。**

### 2.13 分歧裁定：`disabled` 引擎侧**确实校验**（我亲自复核，推翻 §2.10 末尾那条）

两次调查在此处给了相反结论。**我自己读了原文，裁定如下**：

`financial_report_engine.py:276-277`（`_initialize_context` 内）：
```
if template.disabled:
    frappe.throw(_("Financial Report Template {0} is disabled").format(template_name))
```
⇒ **引擎侧确有 disabled 校验并 throw**，不只是客户端下拉过滤。
§2.10 末尾「引擎 execute 内未找到 disabled 校验」**这条是错的，已在此更正**。
（成因推测：搜索者只在 `execute()` 函数体内找，而校验在它调用的 `_initialize_context` 里。）

**记一笔方法论**：两个独立调查给出相反结论时，必须回到原文自裁。本次两处分歧
（`disabled` 校验、`data_source` 取值个数）都靠读原文解决。

---

## 3. 三条路对比

### 3.0 先厘清一件事：本次调查改变了「乙案」的内容

任务书把乙案定义为「数据抄、逻辑自建（或改用 v16 原生引擎配模板）」。
调查后发现 **「自己写报表 py」与「配原生模板」是差别极大的两件事**，必须拆开：

| 记号 | 路 | 科目表 | 报表逻辑 | 现金流 |
|---|---|---|---|---|
| **甲** | 全抄 zelin | 抄 JSON | 抄 676+367+83 行 py + 600 行胶水，逐个修缺陷 | 抄四件套 DocType |
| **乙1** | 数据抄、报表**自写 py** | 抄 JSON | 按官方规范自己写 Script Report | 自写 |
| **乙2** | 数据抄、报表**配原生模板** | 抄 JSON | **零 py 代码**，配 `Financial Report Template` | **配不出来**（§2.2 阻断二）|
| **丙** | 全自建 | 按财政部规范自编 266 条 | 自写或配模板 | 自写 |

**⇒ 乙2 在现金流量表上是断头路**，这是本次调查最硬的一条发现。

### 3.1 对比表

| 维度 | 甲（全抄 zelin） | 乙1（数据抄+自写 py） | **乙2（数据抄+配模板）** | 丙（全自建） |
|---|---|---|---|---|
| **实现成本** | 中。1126 行报表 py + 600 行胶水全部读懂并逐个修（已登记 9 类缺陷 + G1b 两处疑点）。**但 `example_data.json` 的行次配置必须逐行改**（则霖客户的科目号，G1b §5-E），这块被低估 | **高**。BS 约 30 行次 + PL 32 行次 + 现金流三大类，全部自写取数与求值。等于重做 zelin 做过的事 | **最低**。BS/PL 各配一份模板（约 60/35 个 row），**零 py**。但现金流量表**必须另找路**（见下） | 最高。多出「自编 266 条科目表」一整块，且科目表是 zelin 唯一**已实测可信**的资产 |
| **正确性可验证性**（关键） | **差**。抄来的代码「算对了」无法从代码本身证明。**且已知它在科目号不对齐时静默返回 0 不报错**（G1b §5-E，`fin_balance_sheet.py:250-263`）⇒ 错得无声 | 中。自己写的逻辑自己能写测试，但**要自己搭全部验证手段** | **中偏好**。① 官方「填列说明」（§1.6）提供逐行权威映射，可当验收基准 ② 模板是**声明式 JSON**，可脚本化比对「模板引用的科目号 ∈ 科目表」③ 引擎自带设计期校验 14 类（§2.3）④ 自带模板含 `Balance Check (should be zero)` 平衡校验行（`horizontal_balance_sheet_(columnar)` 第 54 行 `L_GRAND_TOTAL - A_GRAND_TOTAL`）—— **这一行是现成的自证机制**。⚠ **但「零命中静默出 0」引擎同样有**（§2.3） | 同乙1，且科目表本身也进入待验范围 |
| **缺陷风险** | **最高**。9 类已登记缺陷 + 6 处 `log_error` 抛 TypeError + `get_chart` 返回 56761 字符原文穿过守卫 + `ignore_chart_of_accounts` 无复位点 + `install.py` 禁用 45 项外所有 UOM。**全部在胶水层，且「坑无法事先估」的质疑成立**（G1c 已核实 9 条中 1 条被推翻、2 条口径有错、1 条比登记更糟 ⇒ 登记本身就不准） | 中。新写的代码有新 bug，但**缺陷在自己手里**，不是「别人埋的、要逐个挖」 | **最低**。无自有 py 代码 ⇒ 无自有代码缺陷。风险转移到「模板配置对不对」，是**数据问题不是代码问题**，可脚本核对 | 中，同乙1 |
| **升级存活性** | **差**。1126 行 py 依赖 `get_balance_on`（BS 真调上游）/ 自己复刻的 SQL（PL 是复刻，不跟上游修 bug，G1b §3 附带发现）⇒ 两张表取数路径不一致，升级时各有各的漂移 | 中。自己写的 Script Report 与上游解耦，但仍依赖 `get_balance_on` 等上游 API | **最好**。① 模板是数据不是代码 ② `sync_financial_report_templates` 只在模板**不存在**时 insert（`:185`）⇒ **自配模板不会被 bench migrate 冲掉**（§2.11 已核实）③ 三张主表的让位点在上游代码里（`balance_sheet.py:31-33` 等三处），**上游自己维护这条路** | 同乙1 |
| **侵入度**（L0–L5） | **L1+L2+L4**：抄 JSON/fixtures(L1) + 自有 DocType/Report(L2) + `override_whitelisted_methods` 3~4 条(L4) | 同甲（科目表进下拉仍需 L4） | **L1+L2**（科目表进下拉那条 L4 仍要，与报表无关）。**报表部分降到 L1** —— 模板是 app 内数据文件，不是代码、不占覆盖位 | 同乙1 |
| **对「客户全是中国客户」定位的契合** | 契合。zelin 本身就是为中国做的 | 契合 | **部分契合**。BS/PL 能配到「数字对、双栏形状对」，但**列头是年份而非「年初余额/期末余额」、左右顺序相反**（§2.4）；现金流配不出 | 契合 |
| **可维护性**（换准则/准则修订） | **差**。两个 Settings 都是 `issingle:1` 单例、**无 company 无准则维度**（G1b §1.2/§1.3），报表侧全走 `get_single()` ⇒ 版式全局一份、绑死一套科目号。要两套准则并存须改造 +1–2 人日 | 中。取决于自己怎么设计 | **最好**。模板按 `report_type` 分，**可存任意多份**（一份小企业准则、一份一般企业准则），跑报表时下拉选。天然多套并存 | 同乙1 |

### 3.2 特别回答：「配原生模板」vs「抄 zelin 报表 py」，哪个更可能算对、哪个更好验证

**更可能算对：配原生模板（乙2）**，四条判据：

1. **代码量差 1126 : 0。** 不写代码就没有代码缺陷。zelin 那 1126 行里 G1b 已指出的疑点包括
   单栏 13 列疑取同值（`fin_balance_sheet.py:408-417`，参数与循环变量 `i` 无关）、
   PL 把 dict 当 name 传（`:43`，侥幸不报错）、两张表取数路径不一致（一个调上游一个复刻 SQL）。
2. **取数引擎是上游维护的、且被上游自己的测试覆盖。** `test_financial_report_engine.py` 有按
   `account_number` 取数的用例（`:1362`/`:1366-1369`/`:1527`）。zelin 的报表**零测试**
   （四个 `test_*.py` 全是 `pass` 空壳，G1b §1.1）。
3. **性能形态好一个数量级。** 引擎总 SQL 约 3~4 条、与行数科目数无关（§2.3）；
   zelin BS 对每个科目一次 `get_balance_on`。
4. **官方「填列说明」（§1.6）可直接翻译成模板筛选表达式**，是「照抄权威映射」而非「猜」。
   例：「货币资金 = 库存现金 + 银行存款 + 其他货币资金 的期末余额合计」⇒
   `["account_number","in",["1001","1002","1012"]]` + `balance_type=Closing Balance`。

**更好验证：也是配原生模板**，三条判据：

1. **声明式 JSON 可静态核对。** 「模板里引用的每个科目号是否都在 266 条科目表里」是一个
   纯文本比对，**不需要跑站点**就能验。抄来的 py 代码做不到这件事。
2. **自带平衡校验行是现成的自证机制**（`Balance Check (should be zero)`，
   `horizontal_balance_sheet_(columnar)` 第 54 行）。资产总计 − 负债及权益总计 ≠ 0 立刻可见。
3. **设计期校验 14 类**（§2.3）在保存模板时就 throw，而非运行时静默。

**⚠ 但两条路共有一个致命弱点，必须讲清楚**：
**「筛选合法而命中零个科目」在两条路上都是静默出 0，不报错**
（引擎侧 `:1168-1170`；zelin 侧 `fin_balance_sheet.py:250-263`）。
⇒ **无论选哪条路，「证明报表算对了」都必须自己建验证手段**，不能指望系统报错。
最低限度是：① 用官方填列说明做逐行验收清单 ② 脚本核对模板/配置引用的科目号全在科目表内
③ 跑一遍真实数据看平衡校验行是否为 0。

---

## 4. 事实性结论（只给判据，裁决权在用户）

### 4.1 项目负责人的质疑：**方向成立，但有一处要修正**

> 「我认为可以不完全照抄 zelin 的代码，只是作为一种思路参考，然后结合财政部等官方部门的规范文件、
> 或其它权威渠道，按照标准的方式去构建报表逻辑，是不是更好。」

**成立的部分（三条事实支持）**：

1. **「绕 zelin 的坑、且坑无法事先估」这个描述准确，且指的确实是代码。**
   已核实的证据：G1c 复核 9 条已登记缺陷，结果是 **1 条被推翻、2 条口径有错、1 条比登记描述更糟**
   ⇒ **连缺陷登记册本身都不准，「坑无法事先估」是有实据的判断，不是悲观情绪。**
2. **官方确实给出了权威的报表逻辑**，不只是格式：《小企业会计准则》附录带**逐行填列说明**（§1.6），
   明确「某一行由哪些科目汇总/相减」。⇒ 「按标准方式构建」**不是从零猜，是照抄官方已写好的映射**。
3. **v16 原生引擎在报表这一层确实能替掉 zelin 的 1126 行 py**，
   且按科目号取数可行、不必贴 `account_category`（§2.1 第 6 问，两侧已核实）。

**要修正的部分（一条）**：

**「不抄 zelin 代码」不能一刀切到现金流量表。**
- 小企业会计准则下**现金流量表是必编**（第七十九条，上海市财政局官网印证，§1.3）。
- 中国现金流量表**正表用直接法**（§1.8）。
- **v16 原生引擎做不了直接法**：`_get_gl_movements`(`:642-677`) 只 `select(gl_table.account)`
  + `groupby(account)`，**不 select `against`/`voucher_no`/`party`，无凭证级遍历**（§2.2 阻断二）。
  自带 IFRS 模板是**纯间接法**（从税前利润起算）。
- **zelin 的 `Cash Flow` 四件套做的正是引擎做不到的那件事** —— 我亲自读了 `cash_flow.py:147-175`：
  它 join GL Entry + Account + Payment Entry，**select 了 `gle.against`（对方科目）、`pe.party_type`、`pe.party`**，
  再按 `cash_flow_code` 归集。**这是直接法的核心机制，且缺陷密度远低于 600 行胶水层**
  （G1b 对 230 行主逻辑只列 4 条「抄后改」，无一条崩溃级）。

⇒ **净结论：质疑在「报表主体」上成立，在「现金流量表」上不成立。**

### 4.2 我认为有第四条路（直接说）

任务书问「若你认为有第四条路（如'部分抄部分配'），直接说」。**有，而且这是判据指向的那条**：

**丁案：分块取舍**

| 块 | 做法 | 理由 |
|---|---|---|
| **科目表 JSON**（266 节点）| **抄**，原样 | 唯一**已实测可信**的资产（双向集合差为空、六个 root_type 全对、树完整性零缺陷）。自编纯属重造 |
| **税模板数据**（`tax_template.json` / `tax_rule.csv` / `default_accounts.csv`）| **抄后改** | 数据层，缺陷是具体的、可穷尽的（2 处科目号笔误、6 个真空字段），**能事先估** |
| **资产负债表 + 利润表** | **配 v16 原生模板，不抄 zelin 的 1043 行 py** | §3.2 四条判据。官方填列说明（§1.6）直接翻成筛选表达式 |
| **现金流量表** | **抄 zelin 的四件套 DocType（230 行主逻辑）** | 引擎架构上做不到直接法；zelin 这块是真资产 |
| **600 行胶水层** | **不抄，重写** | 9 类缺陷全在这里。且 G1a §3.4 已发现 `get_all_nodes` 那条覆盖是**纯冗余可删**（4 条覆盖降 3 条），G1a §3.12 发现两个函数重复定义把上游修复挡在门外 ⇒ **重写比修更省** |

**丁案相对乙2 的差别只在现金流一块；相对甲案省掉 1043 行报表 py + 600 行胶水的逐个修缺陷。**

### 4.3 「2024」这个年份 —— 任务书「已确立的事实」需要更正

**准则正文仍是财会〔2011〕17 号，2013-01-01 施行，至今未修订**（§1.7 三条证据）。
`小企业会计准则(2024)` 这个名字**来自 zelin 自己的科目表文件命名**，不对应任何官方准则版本。
⇒ 建议文档口径改为「执行《小企业会计准则》（财会〔2011〕17 号），科目表用 zelin 的
`cn_smes_chart_of_accounts2024.json`」，把「准则版本」与「科目表文件版本」分开表述，
避免将来误以为存在一个 2024 版准则。

### 4.4 原生引擎的两处真实缺口（若选乙2/丁案，这两处必须接受或另解）

1. **资产负债表列头**：能拿到正确数字与正确双栏形状，但**列标题是年份（`2025`/`2026`）而非
   「年初余额/期末余额」，且左右顺序与法定表相反**（§2.4）。属**外观不合规，不是算不对**。
   要逐字合规须在引擎外套一层（写自有 report 脚本改列头），已超出「纯配模板」范围。**未实测**。
2. **利润表栏目**：官方是「本年累计金额 / 本月金额」（§1.5），
   而引擎的 `accumulated_values` 是**报表级开关**、非列级属性 ⇒ **同表内无法一列累计一列单月**。
   能做的近似是「12 个月列 + total 列」。**未实测**。
3. **附带**：模板**无 `is_default`**，三个 .js 的 `report_template` filter 都无 `default` 键
   ⇒ **用户每次跑报表要手选模板**，否则看到原生老报表。现成机制里未找到设默认值的办法。

---

## 5. 复核建议（按规范 §2.2）

### (a) 最弱环节 / 未覆盖什么

1. **全部结论都是静态读码 + 网络查证，没有一条跑过站点。** 按硬约束（不跑 bench、不建公司、
   不动站点）这是必然，但意味着**三条最关键的判断都是「未实测」**：
   - 原生引擎按 `account_number` 取中国科目表能否真取到数（引擎侧代码通用性已两侧核实，但没跑）
   - 资产负债表双栏 + 两个会计年度的**实际列头**长什么样（§2.4 的绕法只是读码推演）
   - 「筛选合法但零命中静默出 0」是否真如代码所示（§2.3）

   **这三条一次实测就能同时确证**，是最该补的验证。建议在**新建的空测试站点**上做（不碰演示站点）。
2. **官方规范的来源层级不够硬。** 我拿到的最硬来源是**上海市财政局官网**（省级政府，印证第七十九条）
   与**国家税务总局的表单 PDF**（但 PDF 是压缩流，本机无 PDF 提取库、bench venv 是 Linux 符号链接不可用
   ⇒ **未能提取表单原文**）。资产负债表/利润表的**具体行次号**来自
   `zkemu.com` 与 `book.hjyweb.cn` 两个**非官方转载站**（两者互证，但都不是财政部原文）。
   **财政部官网原文 PDF 我三次尝试均失败**（ECONNREFUSED / 自签证书 / ECONNRESET）。
   ⇒ **行次号与合计公式在正式设计前应拿财政部原文或税局表单再核一遍。**
3. **「现金流量表需编间接法附表」这条是单一来源**（`xiexiebang.com`），可信度中低，**须复核**。
   若附表也必编，工作量还要加一块（但那块**正好可以用原生 IFRS 现金流模板的 48 行**，
   §2.9 已核实它是纯间接法、结构高度对应）。
4. **没有核 zelin 报表在「配对了科目号」情况下算得对不对。** 我核的是它的代码形态与缺陷，
   **没有验证它的算法逻辑（两阶段求值、收入类 `*-1`）是否符合官方填列说明**。
   ⇒ 「甲案能不能算对」这个问题我给的是「无法从代码本身证明」，不是「它算错了」。
5. **`horizontal_profit_and_loss_(columnar)`（66 row / 6 ColBreak）未逐行解剖。**
   它可能对利润表的列问题有启示（6 个 Column Break 比 BS 的 3 个多），**未查**。
6. **丙案（全自建科目表）我基本没有实质调查。** 因为 266 节点科目表是 zelin 唯一已实测可信的资产，
   自编它的收益我看不到；但**我没有查「财政部是否公布了官方科目表电子版」** ——
   若有官方权威科目表，丙案的成色会变。**这是我主动承认的一处未覆盖。**

### (b) 你给我的「已知」里有错的 —— **有 4 处**

1. **「准则已定：小企业会计准则(2024)」——「(2024)」不对应任何官方准则版本。**
   正确：准则正文是**财会〔2011〕17 号**，2013-01-01 施行，**至今未修订**。
   出处：① 财政部会计司「政策发布」栏目 2023–2026 条目中无任何《小企业会计准则》修订/废止/新版发布
   （`kjs.mof.gov.cn/zhengcefabu/`）② 上海市财政局 2023-06-16 答疑仍直接援引**第七十九条**原文
   （`czj.sh.gov.cn/.../529d5fa528994c179cd9c6894cfbe7ce.html`）③ 市面「2024 年版/2025 年版」是**图书版次**。
   `(2024)` 来自 zelin 的科目表文件命名。

2. **「模板每行的字段：`data_source`（`Account Data`／`Calculated Amount`／`Section Break`／
   `Column Break`／`Blank Line`）」——漏了一个，实际有 6 个取值，多一个 `Custom API`。**
   出处：`financial_report_row.json:61` 原文
   `"\nAccount Data\nCalculated Amount\nCustom API\nBlank Line\nColumn Break\nSection Break"`；
   引擎分派 `financial_report_engine.py:1153-1166` 一致。
   **这个漏掉的第 6 个取值恰恰是现金流量表唯一的逃生口**（`:1178-1199`，
   `frappe.call(method, filters=..., periods=..., row=row)`，须白名单且允许 GET）。

3. **「`disable_default_financial_report_template`（`:141-151`）」——它不是函数。**
   正确：它是 `sync_financial_report_templates()` 内的**局部布尔变量**（`:141` False / `:145` True / `:150` 读）
   兼 **COA 字典的顶层元数据键**（`:144` `coa.get(...)`）。
   全 bench grep 仅 4 处命中、全在同一文件；`apps/` 下所有 COA json **0 命中**。
   ⇒ 「全仓零使用、未走过的路」**在「无任何 COA 设置该键、分支永不为真」意义上成立**，
   但它不是可调用的函数，**不能「调用它」让地区模板顶掉原生**，而要在**自有 COA json 顶层加这个键**。

4. **「`Horizontal Balance Sheet (Columnar)` 有 64 行定义」——口径要分清。**
   **64 是子表 row 数**（这个对）；**json 文件本身是 993 行**。
   另「含 `Column Break` 与右栏 `Equity & Liabilities`」需更正方位：
   `Equity & Liabilities` 是**第 2 行的 Column Break、在左**（json `:32`），
   `Assets` 是**第 27 行、在右**（json `:418`）⇒ **左栏是负债权益、右栏是资产**，与中国表（左资产、右负债权益）**左右相反**。

**你给对的（一并确认）**：
- `financial_report_validation.py:403` 是 `set(self.account_meta._valid_columns)` ⇒ Account 任何列都能当筛选条件
  —— **成立，且我把读取端也查了**（`:867-879` `getattr(table, field_name)` 动态取列，无写死分支、无列序号取值）。
- 引擎 2044 行、三个新 DocType、自带 6 份模板、`sync_financial_report_templates()` 遍历已安装 app
  ⇒ 全部核实无误。
- `balance_sheet.py:31-33` / `cash_flow.py:32-33` 已改成模板可完全接管 —— 成立，
  **且 `profit_and_loss_statement.py:31-33` 也有同样的让位点**（任务书未提，三处字节级一致）。
- zelin 四份中国科目表 `account_category` 全为 0 处、Standard 表 73 处 —— 成立。
- G1b §5-D（单栏 13 列疑取同值）、§5-E（科目号不对齐则静默 0）—— 我采信并在对比中作为关键判据使用，
  **但两条都仍是「未实测」**。

### (c) 拿不准处

1. **乙2/丁案里资产负债表列头不合规，客户/税务能不能接受。** 这是**业务判断不是技术问题**。
   若报表只用于内部管理，年份列头无妨；若要报送税务或给会计师看，
   「年初余额/期末余额」逐字合规可能是硬要求。**我不敢替你定，但它决定丁案是否成立。**
2. **利润表「本年累计/本月」两列的缺口有多要紧。** 同上，属业务口径。
   技术上的替代是「12 个月列 + total」，但那不是法定格式。
3. **现金流量表的间接法附表要不要做。** 依赖 (a)3 那条单一来源结论。若要做，
   原生 IFRS 模板的 48 行可直接改用，成本低；若不要，省一块。**须先把这条事实核准。**
4. **重写 600 行胶水层的实际成本我没估。** 我给的判据是「9 类缺陷全在这里 + 已发现两处可做减法
   （`get_all_nodes` 覆盖纯冗余、两个函数重复定义）」⇒ 重写比修更省。
   **但这是定性判断，没有量化。** 若你要人日数，需要另做一轮。
5. **MIT 许可与 GPL v3 文件头的冲突（G1c 缺陷 9）在丁案下依然存在。**
   丁案仍要抄科目表 JSON、税模板数据、现金流四件套 ⇒ 仍是 zelin 衍生物。
   且 `custom_account.py:1-2` 文件头写 GPL v3（从上游 erpnext 抄改，上游本身 GPL v3），
   与 zelin 仓库声明的 MIT 不一致。**不做法律判断，只报事实：丁案不能靠「少抄代码」规避这个问题。**
   —— 但丁案**不抄 `custom_account.py` 那 254 行**（归入「600 行胶水层重写」），
   所以 GPL 那个具体文件可以不进自有 app。**这算一个附带好处，但整体许可问题仍需法务口径。**

---

## 6. 本次产出

| 文件 | 说明 |
|---|---|
| `Spike/S4-己-自建vs抄zelin.md` | 本文件。边查边写 |

**本次未产出脚本** —— 全部调查为读码 + 网络查证，未需要可执行探针。
（曾尝试写 PDF 提取脚本读国税总局表单，因本机无 PDF 库、bench venv 是指向容器的 Linux 符号链接而放弃，
脚本已删除，未留残留。）

**约束遵守**：只读；未改 `Reference/`、`frappe-bench/` 任何文件；未跑 bench、未建公司、未动站点；
无 git 操作；未改 `docs/01-需求摸底/S04-中国财税/`；未读 `Reference/saoxia-erpnext_china`。
