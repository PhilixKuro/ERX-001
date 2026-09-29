# P1-S4 开发方案·Part3：取数层、行映射、资产负债表、利润表、漏科目检查

**来源需求**：[B 需求文档](../R06-需求文档/P1-S4-R6-B需求文档.md) §4.8、§4.9、§4.11，需求 TS-003（本方案已完成核准，见下）｜**前置依赖**：Part2（TS-010 的 `ledger.py` 与结转）｜**日期**：2026-09-29｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S4-R7-C开发方案-总纲.md](P1-S4-R7-C开发方案-总纲.md)

> **格式依据**：财政部会计司《小企业会计准则》附录「会计科目、主要账务处理和财务报表」（`kjs.mof.gov.cn/zhengcefabu/201111/P020111118325852734144.pdf`）第 68–78 页，C 步已逐行取得原文；利润表第 3 行按财会〔2016〕22 号改称「税金及附加」；增值税各明细借方余额的列报按 22 号第三部分。**凡标「推定」的映射，原文写的是「分析填列」或未列明细，须送客户会计确认**（列入回执「拿不准处」）。

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-006** 资产负债表与利润表 | 需求 TS-003／012／013、§4.8／§4.9／§4.11、AC-004 ③④、AC-007 末句、AC-008 后半、AC-011、DEC-087／117 | 数据用 TS-011 的两年测试数据集（2025-01 至 2026-03，每月结转）。<br>1. **格式**：`小企业资产负债表` 返回 8 列，列头依次为 `资产｜行次｜期末余额｜年初余额｜负债和所有者权益｜行次｜期末余额｜年初余额`；32 行，行名、行次与本 Part「资产负债表行定义」逐字一致。`小企业利润表` 月报列头 `项目｜行次｜本年累计金额｜本月金额`，32 行；年报第四列列头为 `上年金额`<br>2. **勾稽**：两张表的每条合计行都等于原文勾稽式（资产负债表 10 条、利润表 9 条，含 `≥` 式）；资产负债表在 2025-06、2025-12、2026-03 三个时点两列都平衡（行 30 ＝ 行 53）<br>3. **与总账独立核对**：`货币资金`、`应交税费`、`未分配利润`、`营业收入`、`税金及附加`、`净利润` 六行的数值，用**不经 `ledger.py`** 的 SQL 按科目号直接汇总，逐位相同<br>4. **跨年**（AC-004 ④）：2026-03 利润表的「本年累计金额」＝ 2026-01 至 03 的合计，不含 2025 年任何发生额；2026-03 资产负债表的「年初余额」＝ 2025-12 资产负债表的「期末余额」，逐行相同<br>5. **结转不影响报表**：对 2026-03 取消结转前、取消后、重新结转后各出一次利润表与资产负债表，三次逐位相同（AC-007 末句、AC-008 后半）<br>6. **往来与税费重分类**：造一个预收款客户（`1122` 贷方余额）与一个预付款供应商（`2202` 借方余额）→ 分别出现在 `预收账款`（行 34）与 `预付账款`（行 5），不冲减 `应收账款`／`应付账款`；留抵月 `应交增值税` 的借方余额出现在 `其他流动资产`（行 14），`应交税费`（行 36）不含它<br>7. **年报**：2025 年度利润表（12 月、年报）的「上年金额」列：2024 年无会计年度记录 → 全为 0 且说明行写「上年无数据」；2026 年报的「上年金额」＝ 2025 年报的「本年累计金额」逐行相同（2026 年 4–12 月没有结转，说明行会列出这几个月未结转，数字照出）<br>8. **不静默出 0**：把某条映射的科目号改成科目表里没有的号（测试里 patch 映射常量）→ 报表执行报错并列出缺的科目号，**不返回数据**；`营业税`（行 5）与 `开办费`（行 15）按「法定行、科目表无对应科目」显示 0.00，说明行列出这两行及原因<br>9. **结转状态提示**：未结转的月份出表 → 说明行有「2026 年 3 月尚未结转」；结转后又提交一张该月单据 → 说明行有「结转后该月又有凭证变动」；两种情况报表数字照常输出<br>10. **平衡校验**（BR-006）：测试里 patch 一条映射使资产少计 → 说明行以醒目样式写出「资产总计与负债和所有者权益总计不等，差额 X」，并在 `report_summary` 标红<br>11. **漏科目检查**（AC-011）：在测试公司上结果为空；新建一个挂在 `9999` 之外、任何行都没覆盖的明细科目（如在 `3` 权益类根下新建 `3990 测试科目`）并对它记账后，检查列出它；把 `1012` 的 `account_type` 清空后，检查列出「货币资金下的科目未设为 Cash／Bank，现金流量表会漏取」<br>12. **报表设置**：四个 Report 在库里 `add_total_row = 0`、`prepared_report = 0`、`disable_prepared_report_automation = 1`（LG-136） |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-011 行映射引擎与两年测试数据集 | SL-006 | 否 |
| TS-012 资产负债表 | SL-006 | 否 |
| TS-013 利润表（含年报、税金及附加明细） | SL-006 | 否 |
| TS-014 漏科目检查 | SL-006 | 否 |

---

## 任务 11：行映射引擎与两年测试数据集（对应切片 SL-006）

### 目标
一套可复用的「行 ← 科目」映射与计算引擎（需求 §4.11 第 4、5、7 条：映射放**代码常量**），以及 SL-006／007／008 共用的测试数据。

### 具体改动

**`frappe_china/accounting/statements/mapping.py`**

```python
@dataclass(frozen=True)
class Src:
    numbers: tuple[str, ...]                          # 科目号；每个展开为该科目本身（明细）或其全部下级明细
    sign: Literal["dr", "cr"]                          # dr = 借 − 贷；cr = 贷 − 借
    split: Literal["all", "pos", "neg"] = "all"        # pos：只取为正的部分；neg：只取为负的部分并取绝对值
    per: Literal["account", "party", "unit"] = "account"   # 按正负拆分时的粒度：逐科目／逐往来单位／整组合并

@dataclass(frozen=True)
class Line:
    no: int | None                 # 行次；分类标题为 None
    label: str                     # 法定行名，逐字
    src: tuple[Src, ...] = ()
    formula: str | None = None     # 仅加减与行号，如 "18-19"；由 _eval 解析，不用 eval()
    empty_reason: str | None = None   # 法定行、科目表无对应科目：显示 0.00 并在说明里列出
    indent: int = 0
    bold: bool = False

BS_LEFT:  tuple[Line, ...]   # 32 项（含分类标题），见下表
BS_RIGHT: tuple[Line, ...]   # 32 项（含分类标题与空位），与 BS_LEFT 逐位配对，照原文版式
PL_LINES: tuple[Line, ...]   # 32 项
BS_CHECKS: tuple[str, ...]   # 原文勾稽式 10 条，如 "15=1+2+3+4+5+6+7+8+9+14"、"9>=10+11+12+13"、"53=47+52"、"53=30"
PL_CHECKS: tuple[str, ...]   # 9 条
```

**`frappe_china/accounting/statements/engine.py`**

```python
def resolve(company: str, lines: Iterable[Line]) -> dict[str, list[str]]:
    """全部科目号 → 明细 Account.name。任何科目号在该公司不存在：收集全部缺号后一次抛错（验收第 8 条）。"""

def evaluate(company: str, lines, *, snapshot: "Snapshot") -> dict[int, float]:
    """按 Line 定义算出每个行次的值。snapshot 是一次取出的 GL 汇总（见下），同一张表的各行共用，不逐行查库。
    1. 取数行：Σ over src of value(src)；value 的算法：
         取 src 覆盖的明细科目在 snapshot 里的 (debit, credit)；per = "party" 时按 (科目, 往来类型, 往来单位) 分组。
         per = "unit" 时整组先求和再判正负；"account"／"party" 时逐组判正负后再求和；split = "all" 不判。
         sign 决定取 借−贷 还是 贷−借。
    2. empty_reason 行：值 0.0。
    3. 公式行：按行号依赖顺序求值（有环即抛错——这是映射常量的缺陷）。
    全部结果 flt(, 2)。"""

def check(values: dict[int, float], checks: tuple[str, ...]) -> list[str]:
    """逐条勾稽，返回不成立的说明；"=" 允许 0.005 以内误差，">=" 同。"""

@dataclass
class Snapshot:        # 由 ledger.gl_sums 构造；by_party=True 时键为 (account, party_type, party)
    ...
def snapshot_balance(company, to_date, *, fy_opening_of=None) -> Snapshot: ...
def snapshot_movement(company, from_date, to_date) -> Snapshot: ...        # 恒 exclude_pl_closing=True
```

- `ledger.gl_sums` 增加一个参数 `by_party: bool = False`，按 `(account, party_type, party)` 分组。签名其余不变（Part2 定义）。
- `fy_opening_of` 的口径见 Part2 `gl_sums` 注释：上年末余额，加本年的期初凭证。

**`frappe_china/accounting/statements/labels.py`**：`LEGAL_LABELS: frozenset[str]` 汇集三张表的全部列头、行名，以及打印模板里的标题与表号。`tests/test_legal_labels.py`（总纲 A6）：
- `zh` 下对每项断言 `_(x) == x`；
- 断言 `LEGAL_LABELS` 覆盖 `BS_LEFT`／`BS_RIGHT`／`PL_LINES` 的全部 `label`。

**资产负债表行定义**（左右两栏按原文版式逐行配对；「—」为空位；`dr`／`cr` 为取数符号）

| 位 | 左：行名 | 行次 | 取数 | 右：行名 | 行次 | 取数 |
|---|---|---|---|---|---|---|
| 1 | 流动资产： | — | 标题 | 流动负债： | — | 标题 |
| 2 | 货币资金 | 1 | dr 1000 | 短期借款 | 31 | cr 2001 |
| 3 | 短期投资 | 2 | dr 1101 | 应付票据 | 32 | cr 2201 |
| 4 | 应收票据 | 3 | dr 1121 | 应付账款 | 33 | cr 2202 逐往来 pos；dr 1123 逐往来 neg；cr 220202、220203、220204、220205 |
| 5 | 应收账款 | 4 | dr 1122 逐往来 pos；cr 2203 逐往来 neg | 预收账款 | 34 | cr 2203 逐往来 pos；dr 1122 逐往来 neg |
| 6 | 预付账款 | 5 | dr 1123 逐往来 pos；cr 2202 逐往来 neg | 应付职工薪酬 | 35 | cr 2211 |
| 7 | 应收股利 | 6 | dr 1131 | 应交税费 | 36 | cr 2221000 整组 pos；cr 2221011、2221012、2221013、2221015、2221020 逐科目 pos；cr 2221 其余明细（2221016…2221019、2221030…2221160，split=all） |
| 8 | 应收利息 | 7 | dr 1132 | 应付利息 | 37 | cr 2231 |
| 9 | 其他应收款 | 8 | dr 1221 | 应付利润 | 38 | cr 2232 |
| 10 | 存货 | 9 | dr 1400；dr 4001、400101、400102、400103、400199；dr 4101、410103、410199；dr 4401、4403 | 其他应付款 | 39 | cr 2241 |
| 11 | 其中：原材料 | 10 | dr 1401、1402、1403、1404（**推定**） | 其他流动负债 | 40 | cr 2290；cr 2221014 |
| 12 | 在产品 | 11 | dr 1409、4001、400101、400102、400199（**推定**） | 流动负债合计 | 41 | 31+…+40 |
| 13 | 库存商品 | 12 | dr 1405、1407（**推定**） | 非流动负债： | — | 标题 |
| 14 | 周转材料 | 13 | dr 1411（**推定**） | 长期借款 | 42 | cr 2501 |
| 15 | 其他流动资产 | 14 | dr 1490；dr 2221000 整组 pos；dr 2221011、2221012、2221013、2221015、2221020 逐科目 pos | 长期应付款 | 43 | cr 2701 |
| 16 | 流动资产合计 | 15 | 1+…+9+14 | 递延收益 | 44 | cr 2801 |
| 17 | 非流动资产： | — | 标题 | 其他非流动负债 | 45 | cr 2900 |
| 18 | 长期债券投资 | 16 | dr 1501 | 非流动负债合计 | 46 | 42+…+45 |
| 19 | 长期股权投资 | 17 | dr 1511 | 负债合计 | 47 | 41+46 |
| 20 | 固定资产原价 | 18 | dr 1601 | — | | |
| 21 | 减：累计折旧 | 19 | cr 1602 | — | | |
| 22 | 固定资产账面价值 | 20 | 18−19 | — | | |
| 23 | 在建工程 | 21 | dr 1604 | — | | |
| 24 | 工程物资 | 22 | dr 1605 | — | | |
| 25 | 固定资产清理 | 23 | dr 1606 | — | | |
| 26 | 生产性生物资产 | 24 | dr 1620（组内 1621 − 1622） | 所有者权益（或股东权益）： | — | 标题 |
| 27 | 无形资产 | 25 | dr 1700（组内 1701 − 1702） | 实收资本（或股本） | 48 | cr 3001 |
| 28 | 开发支出 | 26 | dr 1710、4301 | 资本公积 | 49 | cr 3002 |
| 29 | 长期待摊费用 | 27 | dr 1801 | 盈余公积 | 50 | cr 3101 |
| 30 | 其他非流动资产 | 28 | dr 1900 | 未分配利润 | 51 | cr 3102（含 3103 本年利润、3104 利润分配）；加「未结转损益」（见注） |
| 31 | 非流动资产合计 | 29 | 16+17+20+21+…+28 | 所有者权益（或股东权益）合计 | 52 | 48+…+51 |
| 32 | 资产总计 | 30 | 15+29 | 负债和所有者权益（或股东权益）总计 | 53 | 47+52 |

**注**：
- **应交税费（行 36）与其他流动资产（行 14）的分割**（财会〔2016〕22 号第三部分）：
  - `2221000 应交增值税` 按**整组**（十个专栏合计）判正负：借方余额计入行 14，贷方余额计入行 36；
  - `2221011／012／013／015／020` 逐科目判正负：借方计入行 14，贷方计入行 36；
  - `2221014 待转销项税额` 整科目计入行 40（22 号：贷方余额列「其他流动负债」）；
  - 应交税费下其余明细按原文（28）：取贷方余额，借方余额以负数计入行 36。
- **往来重分类**：`1122`／`2203`／`1123`／`2202` 按「科目＋往来单位」逐一判正负后分到两行，对应原文（4）（5）（25）（26）的「分析填列」。
  - `220202…220205`（暂估应付）无往来单位，整科目按贷方余额计入行 33（**推定**）。
  - 原文另规定「超过 1 年的预付／预收账款」列其他非流动资产／负债，**本 Stage 不做账龄拆分**，列为已知限制写进 README。
- **未分配利润（行 51）**（总纲 §五 第 6 条）：`3102` 组的贷方余额，加「未结转损益」。
  - 未结转损益 ＝ −Σ(借 − 贷)，范围是全部 `root_type ∈ {Income, Expense}` 的明细科目，取截至该时点的累计余额。
  - 每月都已结转时它为 0，结果与需求原式相同。
  - 年初余额同样按 `fy_opening_of` 口径计算。
- **`9999 临时开账科目`** 不映射。它不为 0 时，漏科目检查会列出它，平衡校验也会报差额。这是期望行为：开账临时科目本应结平。
- **存货（行 9）** 含成本类的 `4001` 组、`4101` 组、`4401`／`4403`（原文列举的科目之外、按「等科目……分析填列」**推定**）。`400103 生产成本-库存调整` 是 zelin 表的默认库存调整科目，余额性质存疑，列入回执「拿不准处」。

**利润表行定义**（「本月」＝报告月发生额，「本年累计」＝本会计年度 1 月至报告月；**两列都排除损益结转与本年利润结转**，`ledger.gl_sums(..., exclude_pl_closing=True)`）

| 行次 | 行名（逐字） | 取数 |
|---|---|---|
| 1 | 一、营业收入 | cr 5001、5051 |
| 2 | 减：营业成本 | dr 5401、5402 |
| 3 | 税金及附加 | dr 5403 |
| 4 | 其中：消费税 | 分摊（见注），来源 2221030 |
| 5 | 营业税 | `empty_reason = "营业税已于 2016 年 5 月 1 日全面改征增值税，科目表无对应科目"` |
| 6 | 城市维护建设税 | 分摊，2221040 |
| 7 | 资源税 | 分摊，2221060 |
| 8 | 土地增值税 | 分摊，2221070 |
| 9 | 城镇土地使用税、房产税、车船税、印花税 | 分摊，2221080、2221090、2221100、2221160 |
| 10 | 教育费附加、矿产资源补偿费、排污费 | 分摊，2221110、2221120、2221130、2221150（地方教育附加并入本行，**推定**） |
| 11 | 销售费用 | dr 5601 |
| 12 | 其中：商品维修费 | dr 5601160（**推定**：科目表无「商品维修费」，取「销售费用_修理费」） |
| 13 | 广告费和业务宣传费 | dr 5601050 |
| 14 | 管理费用 | dr 5602 |
| 15 | 其中：开办费 | `empty_reason = "科目表无开办费明细科目"` |
| 16 | 业务招待费 | dr 5602040 |
| 17 | 研究费用 | dr 5602190 |
| 18 | 财务费用 | dr 5603 |
| 19 | 其中：利息费用（收入以"-"号填列） | dr 5603210 |
| 20 | 加：投资收益（损失以"-"号填列） | cr 5111 |
| 21 | 二、营业利润（亏损以"-"号填列） | 1−2−3−11−14−18+20 |
| 22 | 加：营业外收入 | cr 5301 |
| 23 | 其中：政府补助 | cr 5301040 |
| 24 | 减：营业外支出 | dr 5711 |
| 25 | 其中：坏账损失 | dr 5711080 |
| 26 | 无法收回的长期债券投资损失 | dr 5711091 |
| 27 | 无法收回的长期股权投资损失 | dr 5711092 |
| 28 | 自然灾害等不可抗力因素造成的损失 | dr 5711101 |
| 29 | 税收滞纳金 | dr 5711071 |
| 30 | 三、利润总额（亏损总额以"-"号填列） | 21+22−24 |
| 31 | 减：所得税费用 | dr 5801 |
| 32 | 四、净利润（净亏损以"-"号填列） | 30−31 |

- **行名里的引号是原文的中文引号（`"-"` 在原文为 `“-”`）**。`labels.py` 按原文码点录入，D 步从附录 PDF 用 `pdftotext` 取文本比对。
- **税金及附加明细（行 4–10）的分摊**：`5403` 在本科目表是单一明细科目，无法按科目直接分出。算法如下：
  1. 取本期借记 `5403` 的每张凭证（排除损益结转）；
  2. 在同一凭证里找贷记上述应交税费科目的金额 cᵢ；
  3. 该凭证的 `5403` 借方净额 D 按 cᵢ／Σc 分到各行，舍入尾差归最后一项；
  4. Σc = 0 的凭证（例如直接从银行存款付印花税）不分摊，金额计入「未能归入明细」，在说明行写出合计与凭证号。
  - 原文勾稽是 `行 3 ≥ 行 4+…+行 10`，未归入的部分不破坏勾稽。
  - 本 Stage 自己生成的附加税计提凭证天然可分摊。
- **单位**：金额保留两位小数，负数带「-」号。

### 两年测试数据集

**`frappe_china/tests/dataset.py`**：`build_two_year_dataset(abbr) -> Dataset`。
- 在测试站建一家本表公司，造 2025-01 至 2026-03 共 15 个月的业务，每月末调用 `generate_month_end_closing`。
- 业务全部用正常单据提交：

| 业务 | 发生时间与频次 | 单据与分录 |
|---|---|---|
| 实收资本注入 | 2025-01 | JE：借 1002，贷 3001 |
| 采购原材料 | 每月 | PI，`P13专票含税` |
| 采购运费 | 隔月 | PI，`P9专票含税` |
| 销售 | 每月 | SI，`P13专票含税` |
| 收款、付款 | 每月 | PE，带 `reference_no` |
| 管理费用 | 每月 | JE：借 5602090，贷 1002 |
| 折旧 | 每月 | JE：Depreciation Entry，借 5602070，贷 1602020 |
| 缴上月增值税 | 次月 | JE：借 2221020，贷 1002 |
| 留抵 | 2025-03 | 进项大于销项 |
| 多交 | 2025-07 | 预缴 JE：借 2221002 |
| 预收 | 2025-10 | 一笔预收款：PE 收款、无发票 |
| 预付 | 2025-11 | 一笔预付款 |
| 提现 | 2026-02 | JE：借 1001，贷 1002，现金内部转账，供 SL-007 使用 |

- 每月再建一张现金流量底稿（Part4 TS-015 完成后才能加这一步，此前数据集先不建底稿）。
- `Dataset` 记录每月各关键科目的**独立期望值**，由造数时的金额直接累加，不查库，供验收第 3 条比对。
- 该数据集在测试类的 `setUpClass` 里造一次，类结束回滚（HT-013）；耗时写进 D 回执。

### 验证方式
`tests/test_mapping.py`：
- `BS_LEFT`／`BS_RIGHT` 各 32 项且行次 1–53 恰好各出现一次；`PL_LINES` 行次 1–32 各一次。
- 公式无环。
- 同一张表里，除「其中」子行、以及 pos／neg 成对拆分外，没有科目被两个取数行重复覆盖。
- 本表 266 个科目里，全部 `root_type ∈ {Asset, Liability, Equity}` 的明细（除 `9999`）至少被资产负债表覆盖一次；全部 Income／Expense 明细至少被利润表覆盖一次。
- `resolve` 对缺号抛错。

---

## 任务 12：资产负债表（对应切片 SL-006）

### 目标
账户式左右双栏的法定资产负债表，自写（DEC-087），屏幕、XLSX、打印同一套数据。

### 具体改动

**Report `小企业资产负债表`**（`cn_tax/report/小企业资产负债表/`；HT-001 不成立时按总纲 §七 改名）

| 字段 | 值 |
|---|---|
| `report_type` | `Script Report` |
| `ref_doctype` | `GL Entry` |
| `is_standard` | `Yes` |
| `module` | `CN Tax` |
| `add_total_row` | 0 |
| `prepared_report` | 0 |
| `disable_prepared_report_automation` | 1 |
| 角色 | `Accounts Manager`、`Accounts User` |

- `.js` 定义筛选：`company`（Link，必填，默认 `frappe.defaults.get_user_default("Company")`）、`fiscal_year`（Link，必填）、`month`（Select 1–12，必填，默认当月）。筛选的 label 用英文源词经 `__()`（总纲 A9）。另写一个 `formatter`：`bold` 行加粗，分类标题行不显示金额。
- `.py` 只有一行转发：`def execute(filters=None): return balance_sheet.execute(filters)`。

**`frappe_china/accounting/statements/balance_sheet.py`**

```python
COLUMNS = [  # fieldname 各不相同；label 为法定列头，逐字
  {"fieldname": "a_label", "label": "资产", "fieldtype": "Data", "width": 220},
  {"fieldname": "a_no", "label": "行次", "fieldtype": "Int", "width": 50},
  {"fieldname": "a_close", "label": "期末余额", "fieldtype": "Currency", "width": 130},
  {"fieldname": "a_open", "label": "年初余额", "fieldtype": "Currency", "width": 130},
  {"fieldname": "l_label", "label": "负债和所有者权益", "fieldtype": "Data", "width": 240},
  {"fieldname": "l_no", "label": "行次", "fieldtype": "Int", "width": 50},
  {"fieldname": "l_close", "label": "期末余额", "fieldtype": "Currency", "width": 130},
  {"fieldname": "l_open", "label": "年初余额", "fieldtype": "Currency", "width": 130},
]   # Currency 列统一 options = "currency"，每行带 currency = 公司币种

def execute(filters) -> tuple:
    f = _validate_filters(filters)                 # 公司存在且用本表；会计年度为自然年；月份 1–12；否则 frappe.throw
    end = 该月最后一天；fy_start = 会计年度起始日
    close = evaluate(company, BS_LEFT + BS_RIGHT, snapshot=snapshot_balance(company, end))
    open_ = evaluate(company, BS_LEFT + BS_RIGHT, snapshot=snapshot_balance(company, fy_start - 1 天, fy_opening_of=f.fiscal_year))
    notes = check(close, BS_CHECKS) + check(open_, BS_CHECKS)        # 平衡与勾稽
    notes += closing_notes(company, f.fiscal_year, 1..month)         # month_closing_state 的 issues，逐月
    notes += empty_reason 行说明（本表无）
    data = [32 行 dict，左右配对；标题行金额为 None（不是 0）]
    message = _render_notes_html(notes)            # 有平衡差额时用红色醒目块
    summary = [{"label": "资产总计", "value": close[30]}, {"label": "负债和所有者权益总计", "value": close[53]},
               {"label": "差额", "value": close[30] - close[53], "indicator": "Red" if 不等 else "Green"}]
    return COLUMNS, data, message, None, summary, True     # 第 6 项 skip_total_row=True
```

- `report_summary` 的前两项 label 取法定行名（`资产总计`、`负债和所有者权益（或股东权益）总计`，已在 `LEGAL_LABELS` 里）；第三项按总纲 A9 用英文源词 `_("Difference")`。

### 验证方式
`tests/test_balance_sheet.py`，对应 SL-006 验收第 1–6、8–10、12 条中属资产负债表的部分：
- 调用方式：`frappe.desk.query_report.run("小企业资产负债表", filters=...)`，走框架入口，不直接调 `execute`；
- 测试里 `frappe.local.lang = "zh"`；
- 数据用 TS-011 数据集。

---

## 任务 13：利润表（含年报、税金及附加明细）（对应切片 SL-006）

### 目标
法定利润表，月报与年报两种口径（DEC-117），本年累计只算本会计年度（V-27），排除结转凭证（需求 §4.7.4）。

### 具体改动

**Report `小企业利润表`**：Report 各字段同 TS-012。筛选在 TS-012 基础上加一项 `period_type`（Select：`Monthly`／`Annual`，默认 `Monthly`；label 与选项用英文源词经 `__()`，需要新词条时进 csv，总纲 A9）。选 `Annual` 时 `month` 固定为 12，并在界面上隐藏。

**`frappe_china/accounting/statements/profit_and_loss.py`**

```python
def execute(filters) -> tuple:
    f = _validate_filters(filters)
    fy = 本会计年度；start_m, end_m = 报告月月初, 月末
    ytd = evaluate(company, PL_LINES, snapshot=snapshot_movement(company, fy.start, end_m))
    if f.period_type == "Annual":
        prev = 上一个自然年的 Fiscal Year（按起止日期查，不按名字）
        second = evaluate(... snapshot_movement(company, prev.start, prev.end)) if prev else 全 0
        second_label = "上年金额"；若 prev 不存在或该年无任何 GL → notes += ["上年无数据"]
    else:
        second = evaluate(... snapshot_movement(company, start_m, end_m)); second_label = "本月金额"
    notes = check(ytd, PL_CHECKS) + check(second, PL_CHECKS)
    notes += surtax_unallocated_notes(...)       # 税金及附加分摊的「未能归入明细」
    notes += [f"第 {l.no} 行「{l.label}」：{l.empty_reason}" for l in PL_LINES if l.empty_reason]
    notes += closing_notes(company, fy, 1..month)
    columns = [项目, 行次, 本年累计金额, second_label]
    return columns, data, message, None, None, True
```

- 税金及附加分摊由 `engine.py` 提供函数 `allocate_surtax(company, from_date, to_date) -> tuple[dict[int, float], list[str]]`，返回行 4–10 的值与说明。`evaluate` 在遇到带标记 `alloc` 的 `Src` 时调用它。实现时给 `Src` 增加 `alloc: bool = False` 字段。

### 验证方式
`tests/test_profit_and_loss.py`，对应 SL-006 验收第 1–5、7–9 条中属利润表的部分：
- 分摊：数据集里附加税计提凭证的 `5403` 借方，应全部分到行 6 与行 10；
- 再造一笔「借 5403 贷 1002」的印花税，它应出现在「未能归入明细」说明里，行 3 包含它，行 9 不含。

---

## 任务 14：漏科目检查（对应切片 SL-006）

### 目标
列出有余额或有发生额、却不被任何报表行覆盖的明细科目（需求 §4.11 第 5 条），覆盖三张报表的映射。

### 具体改动

**Report `漏科目检查`**：Report 各字段同 TS-012；筛选为 `company`／`fiscal_year`／`month`。列头用英文源词经 `_()`：`Account`、`Account Number`、`Balance or Movement`、`Issue`。这张不是法定报表，不受逐字合规约束。

```python
def execute(filters):
    covered = 资产负债表与利润表映射 resolve 后的全部明细科目
    bs_accounts = 本公司 root_type ∈ {Asset, Liability, Equity} 的明细；pl_accounts = Income／Expense 明细
    rows  = [bs 明细 ∉ covered 且 报告月末余额 ≠ 0]
    rows += [pl 明细 ∉ covered 且 本年发生额（不排除结转） ≠ 0]
    rows += [「1000 货币资金」下的明细科目 account_type ∉ {Cash, Bank} → Issue：「现金流量表会漏取」]
    rows += [account_type ∈ {Cash, Bank} 却不在「1000」组下的明细 → Issue：「不属货币资金，却会被现金流量表取数」]
    return columns, rows, (空结果时 message = "未发现漏映射的科目")
```

### 验证方式
`tests/test_unmapped.py`，对应 SL-006 验收第 11 条：
- 在测试数据集上结果为空；
- 在 `3` 权益类根节点下新建 `3990 测试科目` 并记一笔账 → 列出它；
- 清空 `1012` 的 `account_type` → 列出它。
