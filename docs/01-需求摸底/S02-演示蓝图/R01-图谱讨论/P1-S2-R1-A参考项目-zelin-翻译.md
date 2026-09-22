# P1-S2-R1-A 参考项目 zelin-tech/erpnext_china — 翻译部分调研

> 调研对象：`D:\ERX-001\Reference\zelin-tech-erpnext_china\`
> 调研范围：仅翻译部分（财税能力 / 接入机制 / 代码质量由另两个 Agent 负责）
> 只交事实，不给本项目的做法建议。

## 一、四条已知缺陷它怎么译的

结论先行：**四条里只解决了第 4 条（未译），前三条一条没解决**，其中缺陷 3 是逐字照抄了官方的误译。

### 缺陷 1：Setup / Settings 都译「设置」 → 未解决

`erpnext_china/translations/zh.csv` 原文两行 `Settings,设置` 与 `Setup,设置`：两条独立存在、译文完全相同、均不带 context。撞名情形与官方一致，同一侧栏两个分节仍会同名。它还多加了一条 `ERPNext Settings,设置`（官方译「ERPNext设置」），把二重撞名变成三重。

### 缺陷 2：Accounts Receivable / Debtors 都译「应收账款」 → 未解决

原文 `Accounts Receivable,应收账款` 与 `Debtors,应收账款`，父子科目同名问题原样保留。且它的撞名范围比官方更宽——「应收账款」还被 `Receivables`、`Receivable`、`Receivable Account` 三个源词占用。

同时 `Debtors` 词族内部语义不统一：

```
Debtors,应收账款                       Debtor Turnover Ratio,应收账款周转率
Debtor/Creditor,债务人/债权人           Debtor/Creditor Advance,债务人/债权人预付款
```

即作为科目名走"应收"路线，作为通用词走"债务人"路线，两种语义混用。

### 缺陷 3：`Opening & Closing` 误译「POS机交接班」 → 未解决，误译照抄

原文 `Opening & Closing,POS机交接班`，与官方 v16 完全相同的误译。值得注意的是它**同时**收了正确的近义条目，说明作者见过这个词但没意识到带 `&` 那条是错的：

```
Opening and Closing,开账与关账              Show Opening and Closing Balance,显示期初与期末余额
Show net values in opening and closing columns,期初/末栏显示净值
```

### 缺陷 4：Item / Accounts Setup / Sales Taxes 未译 → 已解决

三条都有条目、都译了：`Item,物料`、`Accounts Setup,会计设置`、`Sales Taxes,销售税费`。

`Item` 译「物料」而非「项目/物品」，是制造业语境下的合理取法（与 BOM=物料清单、Work Order=生产工单 一致）。相关联条目也齐：`Sales Taxes and Charges,销售税费`、`Sales Taxes and Charges Template,销售税费模板`、`Setup Sales Taxes,设置销售税`（官方源串大小写不一致产生的 `Setup Sales taxes` 重复项它也照收了，译文一致，无害）。

### 汇总表

| # | 缺陷 | 它的译文 | 是否解决 |
|---|---|---|---|
| 1 | Setup / Settings 同名 | 都是「设置」 | 否 |
| 2 | Accounts Receivable / Debtors 同名 | 都是「应收账款」 | 否 |
| 3 | Opening & Closing 误译 | 「POS机交接班」（照抄误译） | 否 |
| 4 | Item / Accounts Setup / Sales Taxes 未译 | 物料 / 会计设置 / 销售税费 | 是 |

## 二、有没有用 context 参数

**用了，但只用了 32 条（占 0.17%），且没有一条用在缺陷 1、2 上。**

### 列结构

`zh.csv` 是**变长列**：Frappe 的 csv 格式允许每行 2 列或 3 列。实测（Python csv 解析，非按逗号裸切）：有效数据行 18332（`wc -l` 报 19350 是因部分译文内含换行）、唯一 source 18297、2 列行 18300、3 列行 32（第 3 列非空的正好 32）。

第 3 列即 context。Frappe 的加载逻辑（`D:\ERX-001\frappe-bench\apps\frappe\frappe\translate.py` 第 196-217 行 `get_translation_dict_from_file`）确认了这一约定：

```python
if len(item) == 3 and item[2]:
    key = item[0] + ":" + item[2]
    translation_map[key] = strip(item[1])
elif len(item) in [2, 3]:
    translation_map[item[0]] = strip(item[1])
```

即 3 列行以 `source:context` 为 key，2 列行以 `source` 为 key。同一 source 可以既有平条目又有多条 context 条目，互不覆盖。

### 32 条 context 样例（全部集中在"同一短词在不同 DocType 下语义不同"）

```
Rate,税率,Sales Taxes and Charges          # 税表里是税率不是单价，共 4 条（销/采 × 明细/模板）
Make,品牌,Vehicle                          # 车辆里是品牌不是"制造"，共 2 条
Left,已离职,Employee                        # 员工里是"已离职"不是"左"
Issue,资产发出,Asset Movement               # 资产收发，共 3 条（Issue/Receipt/Transfer）
In Process,制程检验,Quality Inspection
Off,停机,Workstation
Base,基本工资,Salary Structure Assignment
Is Subcontracted,受托加工,Sales Order
```

其余：`Payslip`/`Debit Note`×2/`Credit Note`/`State`×2/`Weight`/`Period`/`Accounts`/`Account Name`/`Account Type`/`Payments`/`Advance Payments`/`Advance Paid`/`Open Documents`/`Outward`/`Inward`/`Subcontracted Quantity`。选点都对。

### 判读

作者**懂这套机制**（会正确写 3 列、context 填的是 DocType 名、选点也对），但**用得极少**，只在被"同一源词多义"咬到时才补一条。

缺陷 1、2 的形态是反方向的——**多个源词撞到同一目标词**（Setup 与 Settings 都→设置；Accounts Receivable 与 Debtors 都→应收账款）。这类冲突 context 机制本身也解不了（context 是按 source+场景拆分译文，不是去重目标词），要解得改其中一方的译文用词。这个仓库两边都没动。

顺带查到的同类撞名（同一目标词被 ≥2 个源词占用）共 **914 组**，会计与制造区的样例：

```
设置    <= ERPNext Settings / Setting / Settings / Setup
应收账款 <= Accounts Receivable / Debtors / Receivables / Receivable / Receivable Account
应付账款 <= Accounts Payable / Creditors / Payable / Payables
工序    <= Operations / Operation / Item operation / For Operation
仓库    <= Warehouse / Warehouses / For Warehouse / Accepted Warehouse / Stores / Requesting Site / Request for
状态    <= States / State / Status          已提交 <= Committed / Submitted / submitted
```

`仓库` 组里 `Request for` 与 `Requesting Site` 明显是误归，`已提交` 组里 `Committed` 是误归（见第四节）。

## 三、翻译的形态与生效机制

### 路径与格式

| 文件 | 行数 / 条数 | 格式 |
|---|---|---|
| `erpnext_china/translations/zh.csv` | 19350 物理行 / 18332 数据行 / 18297 唯一 source | Frappe 旧式 CSV，2 或 3 列无表头 |
| `erpnext_china/locale/zh.po` | 4922 字节 / 56 条 msgid / 0 条 msgctxt | 标准 gettext PO |

两套并存。`locale/zh.po` 里的 56 条带 `#:` 注释，指向 `erpnext/` 与 `hrms/`（各 3 条与 2 条有源文件注释），内容是长句设置项说明，明显是给别的 app 的串补译——但放在 `erpnext_china` 自己的 locale 下。

### 生效机制：Frappe 原生加载，不走 fixtures

`translate.py` 第 172-187 行 `get_translations_from_apps`：

```python
for app in apps or frappe.get_installed_apps(_ensure_on_bench=True):
    translations.update(get_translations_from_csv(lang, app) or {})
    translations.update(get_translations_from_mo(lang, app) or {})
```

按已安装 app 顺序遍历，**后装的 app 覆盖先装的**。`erpnext_china` 装在 frappe/erpnext 之后，所以它的 18297 条直接盖掉官方同 source 的译文。这是纯声明式生效，装上 app 即生效，不需要导入动作。

核对过没有 fixtures 路线：`erpnext_china/fixtures/` 只有 `cash_flow_code.json`、`custom_field.json`、`property_setter.json` 三个，无 `translation.json`；`hooks.py` 里搜不到 `translation` / `fixtures` 相关键；`setup/*.py` 与 `patches.txt` 里也搜不到 `translat`。即**不经 `Translation` DocType**。

值得注意的是加载顺序里的一个落差：同一 app 内 `csv` 先加载、`mo`（由 `locale/*.po` 编译）后加载并覆盖。所以 `erpnext_china` 自己那 56 条 po 会盖掉它自己 csv 里的同名条目。但 **`erpnext_china` 的 csv 与官方 `erpnext` 的 po 属于不同 app**，app 间按安装顺序决定，csv 在后所以仍然赢。

### 这 18297 条怎么来的

git 历史（`git log -- erpnext_china/translations/zh.csv`，21 个提交）：`f38cb78 initial`（2026-01-07，余则霖）+11856 行一次性导入 → 中间约 19 个小改（`少量汉化`、`科目表Dr词条翻译修正`、`Payment在采购订单，销售订单与销售发票中汉化调整` 等，单次几行到几十行）→ `4d9c1c5 update translation for v16`（**2026-08-08，作者 Fisher Yu / szufisher，与前期作者不同人**）+12930 / −5776 一次大换血。即"一次性大批导入 + 长期零散修补 + 最后一次大规模重刷"。

与官方 v16 的关系（用 `frappe`/`erpnext`/`hrms` 三个 app 的 `locale/zh.po` 合并成 14330 条基线比对，脚本实测）：与官方译文**完全一致 13503 条**；source 相同但**译文不同（覆盖官方）748 条**；source **不在官方 po 里 4046 条**。

即**它不是在官方基础上做小增量，而是一份自带的全量表**：13503 条（74%）与官方逐字相同，说明基础是从官方那份继承来的；真正的自主改动是那 748 条覆盖。

覆盖的样例（官方 → 本仓）：`Master` 主表→主数据、`Primary Contact` 主要联系人→首选联系人、`Production Capacity` 生产能力→产能、`Accounting Dimensions` 核算维度→辅助核算、`Payment Details` 支付详情→付款信息、`Dear` 尊敬的→亲爱的。

改动方向偏"中国会计/制造从业者的习惯说法"（辅助核算、产能、主数据），不是修错。也有改坏的：`ERPNext Settings` 从「ERPNext设置」改成「设置」，**反而新增了一条与 Setup/Settings 的三重撞名**。

那 4046 条官方 po 里没有的 source，抽查看主要是 HRMS 领域（`Shift Start`、`Half Day Date`、`Last Sync of Checkin` 等）——本 bench 的 `hrms/locale/zh.po` 解析出 0 条，说明 hrms 官方没有中文 po，这批是它自己补的。

### 覆盖 v15 还是 v16

**确实按 v16 对齐过，但不彻底。** 依据：

v16 时代的界面词大批命中：`Workspace,工作区`、`Sidebar,侧边栏`、`Number Card,数字卡`、`Card Break,卡片分隔`、`Form Tour,表单向导`、`Workspace Shortcut,工作区捷径`、`Prepared Report,后台运行报表`、`Submission Queue,提交队列`、`Route History,网址路径浏览历史`、`View Switcher,视图切换`、`Reports & Masters,报表与主数据`、`Your Shortcuts,快速访问`、`Search for anything,搜索任何内容`。

同时有明确缺口（v16 界面上会露英文）：`Setup Wizard`、`Automatic Dark Mode`、`Recent Activity`、`My Profile`、`Spotlight`、`Advance Tax`、`Perpetual Inventory`、`Backflush`、`Overproduction`、`Reposting`、`Provisional Accounting`、`Closing Stock Balance`、`Sub Assembly`、`Multi-level BOM`、`Scrap Items`、`Amortization`。

后半批是会计与制造的 v15/v16 都有的词（`Perpetual Inventory` 永续盘存、`Backflush` 倒冲、`Reposting` 重过账），这些缺失不是 v16 新增导致，而是本来没译。

另一条独立证据：官方 v16 的 `erpnext/locale/zh.po`（8412 条、含 14 条 `msgctxt`）里，缺陷 2、3 的译文与本仓 csv 逐字相同——`:33973 "Opening & Closing"→"POS机交接班"`、`:15827 "Debtors"→"应收账款"`、`:2244 "Accounts Receivable"→"应收账款"`。即这两条是从官方 v16 继承下来、未被这次 v16 重刷触及。

## 四、质量抽查

抽查方式：会计与制造核心 DocType 名与字段名定向抽约 130 条，外加全表机械扫描（纯 ASCII 译文 / 占位符丢失）。

### 总体印象

主干术语译得相当准，用词是懂 ERP 的人选的，不是机翻。几条体现专业度的：`Job Card,生产任务单`、`Routing,工艺路线`、`Workstation,工站`、`Subcontracting Order,委外订单`、`Process Loss,制程损耗`、`Operating Cost,工费成本`、`Cost of Goods Sold,主营业务成本`（按中国会计科目习惯，非直译"已售商品成本"）、`Stock Received But Not Billed,暂估库存(已收货，未开票)`、`Expenses Included In Valuation,结转库存的费用`、`Capital Work in Progress,在建工程`、`Invoice Discounting,应收账款融资(发票贴现)`、`Round Off,小数精度尾差`、`Transfer Material Against,工单发料方式`、`Exchange Rate Revaluation,汇率重估`。

占位符完整性：source 含 `{0}` 而译文丢掉的 **0 条**。这类最容易出运行期问题的错误没有。

### 确定译错

| source | 译文 | 问题 |
|---|---|---|
| `May` | `04` | **明确 bug**。月份缩写整组译成数字（Jan→01…Dec→12），但 5 月写成 `04`，与 `Apr`→`04` 重复。凡走这组缩写的地方（图表轴、报表月份列）5 月会显示 4 月 |
| `Request for` | `仓库` | 源串是"…的请求"类片段（Material Request 里的 `Request for` 指请求类型），译成「仓库」是张冠李戴 |
| `Requesting Site` | `仓库` | 应是"请求方地点/需求站点"，与 Warehouse 混为一谈 |
| `Work In Progress` | `进行中` | 制造语境下 WIP 是**在制品**（对应科目"生产成本/在制品"）。译「进行中」是当成任务状态了。ERPNext 里 Work Order 的 `Work In Progress` 既是状态值也是仓库类型名（WIP Warehouse），至少仓库那一路会错 |
| `Committed` | `已提交` | 库存语境下 Committed Qty 是**已承诺/已占用数量**（被订单占住的库存），与单据的 Submitted（已提交）是两回事，却共用「已提交」 |
| `Ledger` | `会计凭证` | Ledger 是**账簿/明细账**，Voucher 才是凭证。本仓另有 `Voucher,凭证`，两者语义被拉平 |
| `Amortization` | 缺失 | 摊销，会计常用词，无条目 |

### 可疑 / 需业务确认

| source | 译文 | 疑点 |
|---|---|---|
| `Rejected` | `拒绝` | 采购入库里 `Rejected Qty` 指**拒收**数量，「拒绝」偏审批语义。本仓在 `Set Valuation Rate for Rejected Materials` 一句里译对了（"拒收物料"），单词条没跟上 |
| `Write Off` | `内部销账` | 通常是"核销/坏账核销"，「内部销账」不是标准会计说法 |
| `Is Opening` | `开账凭证？` | 译文带问号，界面上会出现「开账凭证？」 |
| `Provisional Profit / Loss (Credit)` | `利润/(亏损）（贷方）` | 全角/半角括号混用，且丢了 Provisional（暂计） |
| `Tax Assets` | `所得税资产` | 源串无"所得税"限定，收窄了语义 |
| `Stock Entry` | `物料移动` | 直译是"库存凭证"。贴近 SAP 习惯，但丢了"这是一张单据"的意味 |
| `Bin` | `实时库存` | 意译合理（Bin 确是仓库-物料实时数量表），但 Bin 作"货位"讲的地方会不对 |
| `Server Script` | `Python脚本` | 意译准确但脱离原文，与 `Client Script,客户端脚本` 不对称 |
| `Dear` | `亲爱的` | 覆盖官方的「尊敬的」。商务邮件模板里「亲爱的客户」不合中文商务习惯，属改坏 |
| `Costing Amount`/`Cost` → `成本`；`In Value`/`Amt`/`Amount` → `金额` | | 多源一译，撞名 |

### 机械扫描结果

纯 ASCII 译文 128 条，逐条看基本都是合理的不译项（`API`、`POS`、`XLSX`、`Webhook URL`、`Verdana`、`SparkPost` 等技术名词与字体名）。混在里面的几条是无意义的大小写变换或完全等值行，无害但也无用：`Idx,IDX`、`Rgt,RGT`、`Mx,MX`、`Javascript,Javascript`、`Lft,Lft`。

## 复核建议

### 拿不准的结论

1. **官方基线的取法**。第三节"官方 14330 条"是我用本 bench 的 `frappe`/`erpnext`/`hrms` 三个 app 的 `locale/zh.po` 合并算的，`hrms/locale/zh.po` 解析出 **0 条**（文件存在但我的解析器没取到条目）。若 hrms 实际有中文条目，则"4046 条官方没有"会显著缩小。**13503 / 748 / 4046 这组数字应视为量级参考，不是精确值。** po 解析器是自写的（逐行 msgid/msgstr，遇 `msgctxt` 丢弃该条），带 msgctxt 的条目被跳过，多行拼接与转义未严格测试。
2. **"是否解决缺陷"的判定只看了译文字面**，没有在跑起来的 v16 实例里验证侧栏是否真的还同名、科目下拉是否还追加 `1`。缺陷 1、2 的现场表现还依赖 workspace 定义与科目表数据，本仓另有 `erpnext_china/erpnext_china/workspace/` 与自定义科目表（不在我的范围内），**有可能它是靠改 workspace 标签或科目名绕开了撞名，而不是靠翻译**。需要看过 workspace/科目表的 Agent 交叉确认。
3. **`locale/zh.po` 那 56 条与 csv 的覆盖关系**。我依据 `translate.py` 第 180-181 行推断"同 app 内 mo 覆盖 csv"，但没读 `get_translations_from_mo` 的实现（`frappe.gettext.translate`），也没确认 `.po` 是否被编译成 `.mo`（仓库里只见 `.po`，无 `.mo`；若构建期不编译则这 56 条根本不生效）。
4. **译错判定里的业务判断**。`Stock Entry,物料移动`、`Bin,实时库存`、`Write Off,内部销账` 我标为"可疑"而非"错"，因为可能是作者刻意的本地化取法。需要熟悉中国制造业账务习惯的人拍板。

### 没看完的

- **18297 条只抽了约 130 条**定向 + 两轮机械扫描。会计与制造以外的领域（CRM、项目、资产、HR、支持、网站/电商）基本没抽。
- **748 条覆盖官方的条目只看了前 25 条样例**，没有逐条评估改好还是改坏。这批是它相对官方的全部自主价值所在，值得完整过一遍。
- **914 组撞名只列了 7 组**。哪些撞名会像缺陷 1、2 那样造成实际操作错误（取决于是否出现在同一下拉/同一侧栏），没有逐组判断。
- **术语内部一致性未系统核查**。已知 `Debtors` 族与 `Rejected` 族自相矛盾，同类问题在其它词族可能还有。
- `erpnext_china/locale/zh.po` 那 56 条只读了前 40 行，未逐条看。
- 未与 saoxia 那份 9221 行做逐条 diff（任务未要求，待验表另有 Agent 负责）。
