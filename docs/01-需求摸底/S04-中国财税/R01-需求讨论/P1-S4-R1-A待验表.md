# P1-S4-R1-A待验表

**发起步骤**：P1-S4-R1 A 步（`plannedDev` shape · 需求讨论）
**发起日期**：2026-09-26
**唤起的可选步骤**：**SA**（`SA-probe-plannedDev-spike.md`，`附属=新Session做`、`可并行至阻塞项`、`结果去向=回原步骤`）
**格式**：[交接契约](../../../流程体系/交接契约.md)「待验表」。**前三列由 shape 写，后三列由 spike 填回**；判定只填 `待验`／`go`／`no-go`／`无法判定` 之一。

**四条命题全部 `不阻塞`** ⇒ 按交接纪律 1，A 步不停下，继续推进 CR-014 并入清单与 CR-005 科目表方案（判断型议题，探针答不了）。按纪律 7，**不阻塞项须在 A 步收尾前处理完**——要么已填回，要么转为遗留问题登记。

**探针留档去向**：`Spike/V21-*`～`Spike/V24-*`（沿用本项目既有命名，最大已用号为 V20）。各条另出 `Spike/V{n}-回报.md`。

**派出记录**（2026-09-26）：四条已按 SA 步 `附属=新Session做` 分四个独立 Session 派出，各验一条命题（bricks/spike 纪律 3「一个探针一个命题」）。

**⚠ 一处与 Spec 的偏离，明记**：按 SA 步本应由探针自己把后三列填回本表。本次改为**探针交回事实、由 A 步逐条填入**——理由是四条并行，三个以上 Session 同时改同一份表有互相覆盖之虞。**事实来源不变**（只取探针实跑所得，不加工、不代填），但「填表的手」是 A 步而非探针。故若某条判定与探针留档 `Spike/V{n}-回报.md` 有出入，**以留档为准**。

**⚠ V-22 是四条里唯一写站点的**，已给它三条额外约束：不动 `华东弹簧` 任何既有单据（要核销就自建一张一次性 Payment Entry）、建专用测试 `Bank`／`Bank Account`、跑完清理并回报残留。另明禁 `bench reinstall`／`migrate`／`build`／`seed-demo.sh`／`backup.sh`／`restore.sh`（`backup.sh` 每类只留最新一份，跑它会挤掉现有基准点）与「建第二家公司」（RW-07 那个崩溃前提）。

---

| 编号 | 待验命题 | 阻塞否 | 判定 | 实际观察 | 探针代码 |
|------|---------|--------|------|---------|---------|
| **V-21** | 本机站点 `erx.localhost` 上，`erpnext.setup.doctype.company.company.get_region()`（或其实际定义位置）对本项目公司返回的字符串**是否逐字等于 `China`** | 不阻塞 | **`go`** | **定义只一处**：`erpnext/__init__.py:120`（运行时 `get_region.__code__.co_filename/co_firstlineno` 自证与静态搜索一致；`apps/frappe` 内搜 `get_region` **零命中**；`party.py:309 get_regional_address_details` 与 `taxes_and_totals.py:1281 get_regional_round_off_accounts` 是同前缀的**不同函数**，非本命题对象）。**取值来源三级回退**（`:120-132`）：入参 `company` 空 → 回落 `frappe.local.flags.company`；有公司则 `frappe.get_cached_value("Company", company, "country")`，即**直接读 `Company.country`**（`fieldtype=Link, options=Country`）；都无则 `frappe.flags.country or System Settings.country`。**三条调用路径全部返回 repr `'China'`**，len 5，码点 `43 68 69 6e 61`，UTF-8 `4368696e61`，`is_ascii=True`、无前后空白：`get_region("华东弹簧")`／`get_region()`（flags 未设）／`get_region()`（按 docstring 设 `frappe.local.flags.company` 后，已在 `finally` 复位）。**公司 `country` 原值**：`frappe.db.get_value` 与 `get_cached_value` 均为 `'China'` 且逐字节相同（无缓存偏差）；公司行 `{'name':'华东弹簧','abbr':'HDS','country':'China','default_currency':'CNY'}`（全站仅此一家）；`System Settings.country`=`'China'`；`Country` 里 `code=cn` 的记录名是英文 `'China'`。**⚠ 另有一项超出本命题的事实见下方「V-21 的附带发现」** | `Spike/V21-get-region-exact.py`／`Spike/V21-out/get-region-exact.json`（原始输出）／`Spike/V21-回报.md` |
| **V-22** | 一份**中文列名的 xlsx 或 csv 银行流水**（非 MT940），经 `Bank Statement Import` ＋ `Bank Transaction Mapping` 配列映射后，**能否全部导入成 `Bank Transaction` 记录**；随后 `auto_reconcile_vouchers()` **能否把其中至少一笔与既有单据自动核销上**（`Bank Transaction.status` 变为已核销且 `clearance_date` 落值） | 不阻塞 | **`go`**（两半均成立，但**通过路径不是命题设想的那条**，且附带两个硬前置） | **(a) 成立**：中文表头 8 列（交易日期／摘要／借方发生额／贷方发生额／余额／对方户名／交易流水号／币种）＋1 列字面量 `Bank Account`；映射 8 字段（**`余额` 必须留空**——Bank Transaction 无余额字段，映到 Link 字段会触发静默失败）。xlsx `status=Success`、导入 2 行（`ACC-BTN-2026-00007/00008`），中文「货款收入」「手续费」「江南机械」**落库无乱码**，Data Import Log 2 条 `success=1`／`exception=None`；utf-8 csv 同样 Success；峰值共导 12 行。**(b) 成立**：`auto_reconcile_vouchers()` 返回「1笔交易已对账」，`ACC-BTN-2026-00007` → `status=Reconciled`、`allocated 8888.0`／`unallocated 0.0`，挂到 `ACC-PAY-2026-00009` 且该凭证得 **`clearance_date=2026-09-28`**。**⚠ 但 `Bank Transaction Mapping` 子表全程未被读取一次，填中文 `file_field` 完全无效** —— 四处实测缺陷与两个硬前置见下方「V-22 的四处缺陷」。**路径是同步非队列**（容器无 queue worker、`is_scheduler_inactive()=True`，但 `developer_mode=1` 使 `run_now` 真、`enqueue(now=True)` 同进程执行），**调的是出厂 `start_import()` 本身、非手工替代流程**。**`Error Log` delta = 0**。**清理已验**：10 个 DocType 计数逐一回到基线（Bank Transaction 0→12→0／Payment Entry 2→5→2／Bank Account 0→1→0／Bank 0→1→0／Error Log 1→1→1／BSI 0→7→0／Data Import Log 0→12→0／File 2→9→2／GL Entry 22→28→22／Account 95→96→95），演示数据完好（`ACC-PAY-2026-00006/00007` 的 `clearance_date` 仍 `None`、`docstatus=1`；95 科目／12 SLE／2 销售订单／1 BOM／6 仓库／1 公司均与基线一致） | `Spike/V22-seg0-baseline.py`…`V22-seg17-*.py`（18 段，核心证据是 **`V22-seg3-diagnose.py`** 键不匹配对照实验与 **`V22-seg10-clean-shipped.py`** 未改源码跑通）／样本 `V22-sample-statement{.xlsx,.csv,-gbk.csv,-clean.xlsx}`／输出 `V22-out/seg0..seg17-*.json`／留档 `V22-回报.md` |
| **V-23** | `Reference/saoxia-erpnext_china` 内**是否存在月末结转（增值税期末结转：进项税额转出／转出未交增值税／未交增值税）的实现**；若有，它是 Journal Entry 模板、自有 DocType，还是脚本 | 不阻塞 | **`no-go`**（确认缺失） | **saoxia 完全不触会计域**，三种形态（JE 模板／自有 DocType／脚本）全无。**52 个同义词扫 242 文件 / 1.54 MB**：`转出未交增值税`／`未交增值税`／`进项税额转出`／`应交增值税`／`2221003`／`2221007`／`2221020`／`journal_entry`／`make_gl_entries`／`gl_entry`／`period_closing_voucher`／`carry_forward`／`period_end`／`month_end` **全部零命中**；宽口补扫 `grep -rn 增值税` = **0 行**，`grep -rnwi vat` 全词 = **0 行**（散见 vat 全是 `private`／`activate` 子串），`grep -rn 2221` 命中全落在 `china_city_code.json` 行政区划码（如 `142221` 山西省忻县）。**有命中的词 100% 落在 `translations/zh.csv`**（9221 行两列翻译）：`:7547 Period Closing Settings,期末结账设置`、16 处 `结转` 全是 `Carry Forward` **休假**结转。唯一非 csv 的 `Journal Entry` 命中是 `sales_order_dashboard.py:9,30`（全文 32 行，仅仪表盘关联单据配置，不建凭证不算金额）。**三条绝对断言判据齐**（开发守则）：① 52 同义词多轮 grep；② **目录清单**——`modules.txt` 仅 `ERPNext China`／`HRMS China`，**无 Accounts 模块**，`erpnext_china/doctype/` 17 个全 CRM／企微、`hrms_china/doctype/` 13 个全 HR、58 个 json **无 CoA／税率表／JE 模板**、`patches.txt` **空**、`after_install` 唯一数据文件是 `territory.csv`；③ **三种藏法逐一排除**——报表仅 2 张且 `query`／`javascript` 长度 **0**、`.py` **全 0 字节**；6 个 Custom Field 逐个看过无一指向税额；全 app 仅 2 个 Check 字段均追到引用点。**git 全历史**：`--grep` 搜 `结转`／`增值税`／`journal`／`税` = **0 条提交**——该仓库历史上从未有过会计文件 | `Spike/V23-vat-period-end-scan.py`／`Spike/V23-vat-period-end-scan.out.json`／`Spike/V23-回报.md` |
| **V-24** | zelin `小企业会计准则(2024)` 科目表 JSON 里，**同名父子（父科目与其某个子科目名称完全相同）具体是哪 2 对**，各自的 `account_number` 是什么、哪一个是 `is_group` | 不阻塞 | **`go`**（确是 2 对） | **JSON**：`Reference/zelin-tech-erpnext_china/erpnext_china/chart_of_accounts/custom_accounts/chart_of_accounts/cn_smes_chart_of_accounts2024.json`（内 `name`=`小企业会计准则(2024)`、`country_code`=`cn`）。**总节点 266（分组 41／叶子 225）**，与 V-19 实测 266 条吻合。同目录 `cn_sme_coa.json` 是另一张表（`小企业会计准则`，无年份，190 节点，同名父子 **0** 对），非本命题对象。**两对形态完全一致（父整百编号作壳、子 +1 可记账）**：① `资产类 > 非流动资产 > 生产性生物资产`——父 **1620／is_group=1**（account_type 空）、子 **1621／is_group=0**（`Fixed Asset`），父的另一子是 `生产性生物资产累计折旧`(1622)；② `资产类 > 非流动资产 > 无形资产`——父 **1700／is_group=1**、子 **1701／is_group=0**（`Fixed Asset`），父的另一子是 `累计摊销`(1702)。已用 grep 原文（JSON 行 304-314／322-332）不依赖自写解析器独立复核。**先前代码读结论核对**：一般企业2024 确为 **13** 处、`应收账款` 确为 **11220(is_group=1)／11221(is_group=0, Receivable)**；民间非营利(2025) **4** 处。**⚠ 但「父必为壳、子必为叶」只在小企业(2024) 这 2 对上成立**——一般企业表里 `固定资产 16000/16010` 子也是分组，`长期股权投资 15100/15110` 与 `其他应付款 22300/22410` **父反而 is_group=0**，不能套用。**⚠ 演示路径结论见下方「V-24 的附带发现」（比命题本身要紧）** | `Spike/V24-samename-parent-child.py`／`Spike/V24-out/V24-hits.json`／`Spike/V24-回报.md` |

---

---

## V-22 的四处缺陷与两个硬前置（判定 `go` 的附带条件）

> **本节全部由 A 步逐条独立复核过源码**，不只取探针回报——四处缺陷与那条核销前置都自行读过对应行。**复核结论：探针所述与源码一致，无一处夸大。**

**⚠ 先说最要紧的一句**：判定是 `go`，但 **`Bank Transaction Mapping` 这个机制是坏的**。中文流水能进去，靠的是「让文件列序与目标字段顺序对齐」，**不是**靠那张映射表。故 DEC-082 当初的判据「`Bank Transaction Mapping` 可映射任意列布局」**不成立**。

### 四处缺陷（均已核源码）

| # | 缺陷 | A 步的复核落点 | 后果 |
|---|---|---|---|
| **1** | **键不匹配（致命）** | **已核实**：写入端 `bank_statement_import.py:68-70` 以 `i.file_field`（即**中文表头**）为键构造 `column_to_field_map`；读取端 `frappe/core/doctype/data_import/importer.py:879` 是 `column_to_field_map.get(str(j))`，**`j` 是 `enumerate(row)` 的列序号**。故中文表头键**永不可能命中**。探针对照实验：同一份数据按表头映射 **0/7** 成功、按列序号 **7/7** 成功 | 填中文列名的映射表**完全无效**；能跑通是因为列序恰好对齐 |
| **2** | **门禁倒置** | **已核实**：`:84-85` 要求 `if "Bank Account" not in json.dumps(preview["columns"]): frappe.throw`，而补该列的 `add_bank_account()` 在 **`:327`**、由 `start_import()` 在 `:283` 之后才调 ⇒ 门禁先跑、补列后跑 | 不手工预置 `Bank Account` 列即抛 `ValidationError: Please add the Bank Account column` |
| **3** | **挪用真实列凑门禁会静默毒化** | 探针实测：Link 校验拿余额数字去对 Bank Account 名，`importer.py:85-92` 对 `type != "info"` 的告警**直接 `return`**，`status` 停在 `Pending`、**不抛异常不写日志** | **静默失败**——报 Success 却不建单，或干脆卡在 Pending |
| **4** | **映射表每次导入被删光重建，且有粘性** | **已核实**：`update_mapping_db():315-324` 先 `for d in bank.bank_transaction_mapping: d.delete()`，再按 `template_options` 重建；而它由 `start_import():286` **每次导入都调** | 中文映射被冲成 `0/1/2/3/5/6/7`；下次 `validate()` 又从被污染的表重建，**把陈旧键塞回来** |

### 一处最危险的发现：GBK csv 静默乱码

**`status=Success`、`success=1`、单也建了，但中文全乱码**（`»őżîĘŐČë` 应为「货款收入」）。**成因已核实**：`start_import():291` 另建了一个 **不带 `template_options`** 的 `ImportFile`，故**预览阶段的阻塞告警与 `import_data()` 实际检查的不是同一个对象**，告警拦不住导入。

**⚠ 这条对本项目权重最高**：中国网银导出 **GBK/GB18030 极常见**，而本项目此前已多次踩中文编码坑（项目概况「已知限制」与记忆里的 heredoc/GBK 两条）。**探针未验 `use_csv_sniffer` 开关能否补救**（`Bank Statement Import` 有该字段），若可用则此条可降级。

### 自动核销的硬前置（业务约束，非缺陷）

**已核实**：`bank_reconciliation_tool.py:1340` 定义 `ref_condition = pe.reference_no == transaction.reference_number`，而 **`:1381-1382`**：

```python
if frappe.flags.auto_reconcile_vouchers is True:
    query = query.where(ref_condition)
```

即**自动模式下把它升为硬 WHERE 条件**（手工模式下它只是 rank 四因子之一）。**故凭证的 `reference_no` 必须与流水的 `reference_number` 完全相等才可能自动匹配上**——金额、日期、往来单位全对也不行。6 笔只核销 1 笔正是此因。`get_je_matching_query` 同样强制 `cheque_no` 相等（探针只读码未实跑）。

**⇒ 这是一条要落到业务流程上的约束**：本项目的收付款凭证**必须回填 `reference_no`**（银行流水号），否则自动对账形同不存在、只能手工点。

---

## 三条填回后的附带发现（超出命题、但直接影响本 Stage）

> 按交接纪律 5「不在表里写建议」，本节只记**事实**；去向与处置由 A 步讨论定。三条均已由 A 步独立复核（不只取探针回报）。

### ⭐ V-24 的附带发现：演示公司用的是 `Standard` 表，不是 zelin 的中国科目表，且已开始记账

**探针原话**：「这两个科目不会出现，原因比『碰巧没选到』更彻底——**演示根本没用 zelin 的科目表**。」`最小闭环操作稿.md` 环节 1 明写 `Create Chart Of Accounts Based On = Standard Template`、`Chart of Accounts = Standard`，生成 ERPNext 原生 95 条；全文 grep `zelin`／`小企业`／`一般企业`／`erpnext_china` 及 `生产性生物资产`／`无形资产`／`累计摊销`／`1620`／`1621`／`1700`／`1701` **全部零命中**（已用 grep `步` 得 78 命中做阳性对照，确认检索有效）。

**A 步在实站独立复核，确认并补出探针未查的一半**（`docker exec` 读 `erx.localhost`）：

| 项 | 实测值 |
|---|---|
| `Account` 条数（`华东弹簧`） | **95** —— 与 `Standard` 表吻合，**不是** zelin 的 266 |
| 五个根科目名 | `收入`／`权益`／`费用`／**`资金(资产)使用`**／**`资金来源（负债）`** —— 是 `Standard` 英文表的中文译名，**不是**中国准则的 `1 资产类`／`2 负债类`… 六根 |
| 公司数 | 1（`华东弹簧`） |
| **`GL Entry`** | **22** |
| **`Stock Ledger Entry`** | **12** |
| 已提交销售发票 | 1 |

**⚠ 本条的分量须按图谱原文收窄，A 步初判写宽了**：初判写成「这与 CR-005 硬约束直接相撞、是此前未被任何产物点明的前提问题」，**该表述不准**——[需求图谱](../../0-P1文档/需求图谱.md) `:205-208` **已显式点明这一处**，且已给出判据：

> `CR-005 中国科目表 ⊥ 〔沿用现有 95 科目标准表建公司〕`……**约束的重量取决于它挂在谁身上**：「开始记账后不可换」挂客户正式库是硬约束，挂脚本生成的演示库近乎零成本（**删库重建即可**）。

**故准确的形态是**：`华东弹簧` 确实已用掉它那一次建账机会（22 GL／12 SLE 已落，不可换表），但它是 **S1 的学习与实操公司**，不是演示公司。路线文档 §四 S7 的前置依赖写的是「S4（**科目表 → 建公司**，硬次序③）」，即**演示公司本就是 S4 之后新建的一家**，S4 完成标志⑥「同进程连续建两家公司不崩」也正预设了多公司。**图谱那条互斥已消解、不是开放问题。**

**剩下的真实待定点比初判小得多，但确实存在**（交 A 步讨论，见讨论记录第 2 步）：`华东弹簧` 里那套**完整闭环样本**（主数据＋采购链＋生产链＋销售链，22 GL／12 SLE／1 BOM／2 工单，另是 `docker/backups/20260922_145623` 的内容与项目概况点名的站点现状）建在 `Standard` 95 条表上，**故它不能直接充当中式科目表下的演示数据** —— S7 的 CR-011／CR-012 须在新公司里重建。这不改变任何既定次序，但影响「S7 要不要复用现有样本」这个预期。

### V-21 的附带发现：`regional_overrides` 当前无 `China` 键

**探针原话**：`frappe.get_hooks("regional_overrides")` 实测键为 `['France','United Arab Emirates','Saudi Arabia','Italy']`，`"China" in hooks` → `False`。

**A 步独立复核**（不取探针结论，自行解析 `hooks.py` 与读 `__init__.py`）：

- `hooks.py` 里 `regional_overrides` 块 **14 行、顶层键恰好四个**：`France`／`United Arab Emirates`／`Saudi Arabia`／`Italy`，块内 `China` 不出现。**与探针一致。**
- **派发点的容错行为已读码确认**（`erpnext/__init__.py:145`）：`overrides = frappe.get_hooks("regional_overrides", {}).get(get_region())`，随后 `:148` `if not overrides or function_path not in overrides: return fn(*args, **kwargs)`。**故缺 `China` 键不报错**，只是所有 `@allow_regional` 点走原函数。`:152` 的 `overrides[function_path][-1]` 即「末位装的 app 胜出」那处。

**两条事实由此确立**：

1. **这是自建 app 装载前的基线**，不是缺陷——`China` 键本就该由 `erx_core` 注册。
2. **⚠ 但 IM-007 的断言按字面写会 `KeyError`**：图谱 IM-007 原文是「断言 `get_hooks("regional_overrides")["China"]` 每条 list 的 `[-1]` 落在自有模块前缀上」，而 `["China"]` 是下标取值、不是 `.get()`。在 `erx_core` 未注册任何 `regional_overrides`（或注册失败）时，这条自检**本身抛异常而非给出告警**——那正是它要检测的故障场景。**已登记为 LG-125**，去向由 A 步定（S8G-S1 才实现 IM-007，但本 Stage 是 `cn_tax` 覆盖位的产出方）。

### V-23 的附带发现：两份参考料在月末结转上同样缺失，另有两条留档

1. **月末结转两份参考料均无实现可借，须自建**——zelin 有科目无凭证逻辑（全仓零 `Journal Entry`），saoxia 连科目都没有。**这使路线文档「月末结转 2–4 人日」的估算前提（『zelin 也没做，但科目已备好』）保持成立，且排除了「翻 saoxia 能省一点」这个可能。LG-098 至此闭合。**
2. **一条不确定线索**（探针如实标注）：`zh.csv:7838-7841` 出现 `22210101 进项税额`／`22210102 销项税额` 是**八位**科目号，与 zelin 的**七位**（`2221001`）编码位数不同——说明 saoxia 作者见过某份八位编码的中国科目表，但**仓库内确实没有该表**。不构成实现。
3. **两条 `Reference/` 的风险事实已坐实**（供 NV-016 与许可证判断留档，**本 Stage 不消费、只记**）：① `erpnext_china/utils/old_system_data.py`（558,760 字节）含 **34,305 处**手机号样式串（此前记载为 33727，探针只计数未回显）；② **许可证矛盾有了确切落点**——`license.txt` 是 MIT 且 copyright 仍为占位符 `[year] [fullname]`、`hooks.py:6` 写 `mit`，而 `install_fixtures.py:1-2` 文件头声明 **GPL v3**；③ 另记 `install_fixtures.py:41-73` **上跳六级直接改写 frappe/erpnext 源码树**的 17 个 workspace json（含 `erpnext/accounts/workspace/accounting/accounting.json`）做字符串替换汉化——**这是本项目开发守则明禁的形态**（不改上游源码），再次印证 NV-016「只可读不可并入」。

---

## 各条命题的背景与判定要求（供探针建立上下文，不属表格列）

### V-21 — `get_region()` 返回值（源自 LG-084）

**为什么要验**：需求图谱 LG-084 称其为「A 步判定的最要紧未查实项」，理由是 CR-005～007 走 `regional_overrides` 的覆盖判断全建在这个字符串上，region key 须逐字匹配。

**⚠ 但本 Stage 的 A 步已判定这条分量按现状偏高**（见讨论记录第 1 步议题 ④）：ADR-0007 的 **NV-038 已否决 `regional_overrides` 路线**——上游 18 个 `@allow_regional` 挂点**全部是交易时点**，无一在建账路径上；A 案走的是 4 个 whitelisted 覆盖 ＋ Company 三钩子。**故它对 CR-005 建账不再是前置**，仍牵动两处：① CR-006 若要用 `regional_overrides` 挂计税覆盖；② **S8G-S1 的 IM-007 自检**（断言 `get_hooks("regional_overrides")["China"]` 每条 list 的 `[-1]` 落在自有模块前缀上）。

**判定要求**：

- `go` = 返回值逐字等于 `China`；`no-go` = 返回其它字符串（**须写出实际返回的确切字符串**）。
- 顺手记下 **`get_region()` 的定义位置与取值来源**（读的是 `Company.country`、`System Settings`、还是别处），以及**公司 `country` 字段的实际值**。
- 若同一函数在 frappe 与 erpnext 各有一份，**两处都记**。

### V-22 — 中文银行流水导入与自动对账（源自本步议题 ②，用户已裁甲案）

**为什么要验**：A 步读码判定**银行对账原生已完整**（`bank_reconciliation_tool.py` 1531 行、rank 四因子匹配、`auto_reconcile_vouchers` `:964` 非悬空、`Bank Statement Import` 支持 CSV＋MT940、`Bank Transaction Mapping` 可映射任意列布局、`Bank Transaction Rule` 做自动归类），用户据此**裁定甲案：直接把该项由 3–5 人日缩为 0.5–1 人日，不自研匹配逻辑**。

**⚠ 故本条的性质与其余三条不同**：它**不再是"定范围的依据"**（范围已定），而是**提前暴露甲案自陈的那处风险**——「若中文格式导入有坑，要在 S4 内临时补，而此刻没有预留量」。早验掉就早消掉。这一条同时是 **LG-122** 的闭合动作。

**判定要求**：

- **列名用中文**（如「交易日期」「摘要」「借方发生额」「贷方发生额」「余额」「对方户名」），这正是与 MT940 路径的差别所在，不要图省事直接用英文列。
- `go` = 导入成功且**至少一笔自动核销上**；`no-go` = 任一环节失败（**须写出确切报错与失败在哪一环**：读文件／列映射／建 `Bank Transaction`／`auto_reconcile_vouchers`）。
- **⚠ 按开发守则「静默失败自成一类排查对象」**：`Bank Statement Import` 继承 `DataImport`、走后台队列，**"没报错"不等于成功**。须给正向证据——`Bank Transaction` 的实际条数、核销后的 `status` 与 `clearance_date` 取值，不能以"没报错"代替。
- 记下**配一次列映射的实际耗时量级**（分钟级还是小时级），这是甲案那 0.5–1 人日估算的唯一实测依据。
- **不必**测 MT940 路径（`mt940` 包已确认装在 bench env，且国内银行不导该格式）。
- **不要动演示公司的既有数据**：用一次性测试公司或测试银行账户，跑完清理（同 V-18／V-19 的做法）。

### V-23 — saoxia 的月末结转实现（源自 LG-098，动机已缩一半）

**为什么要验**：LG-098 原动机是「zelin 缺月末结转与银行对账两块，saoxia 可能有」。**本步议题 ② 已查明银行对账原生就完整、谁都不用抄**，故只剩月末结转那半值得翻。zelin 侧已确认**全仓零 `Journal Entry`**，但科目已备好（`2221007` 进项税额转出／`2221003` 转出未交增值税／`2221020` 未交增值税）。

**⚠ 硬约束（NV-016）**：`Reference/saoxia-erpnext_china` **只可读、不可并入**——它含 **33727 个真实手机号**，另无财税本地化、只适配 v15、许可证矛盾。**本条只做阅读调研，不抄任何源码进本项目。**

**判定要求**：

- `go` = 找到月末结转的实现（**须写出文件路径与实现形态**：Journal Entry 模板／自有 DocType／脚本，以及它结转哪几个科目、按什么口径算）；`no-go` = 确认没有（**须说明查了哪些路径与关键词**，按开发守则「断言原生没有 X 须满足三条」：多同义词 grep ＋ 看过目录清单 ＋ 说明为何不可能在别处）。
- 顺手记它**是否只适配 v15 的写法**（若有实现但依赖 v15 API，对本项目的参考价值要打折）。

### V-24 — 同名父子科目具体是哪 2 对（源自 LG-080，为判断型议题备事实）

**为什么要验**：LG-080 是**判断型**遗留问题（处置办法要讨论定，如给 group 层加「（汇总）」后缀），本轮不派探针解决它——但它有一个前置事实可顺手确认：那 2 处同名父子**具体是哪两对**。没有这个事实，CR-005 讨论处置办法时只能泛泛而谈。

**已知**：zelin 4 张表里 3 张有同名父子，一般企业2024 有 **13 处**（含 `应收账款 > 应收账款` 11220/11221）；小企业(2024) 有 **2 处**。症状不是官方那种"子科目被追加数字 1"（去重键含科目号），而是**"只差科目号前缀"**——下拉里 group 与能记账的明细只差编号，`11220` 是 group、`11221` 才能记账。**改译名解决不了它。**

**判定要求**：

- `go` = 列出那 2 对的完整信息（父与子各自的 `account_name`／`account_number`／`is_group`／`root_type`／`account_type`）；`no-go` = 实际不是 2 对（**则写出真实对数与全部明细**——此前那个「2 处」的数也是读码得出的）。
- **读 JSON 源即可**（`Reference/zelin-tech-erpnext_china/` 下小企业准则那份科目表），**不必建公司**——V-19 已实测建出来的 266 条与 JSON 源逐项一致（双向集合差两边都空），故 JSON 上的结论对建账结果成立。
- 顺手记**这 2 对在演示线上会不会被用到**（即最小闭环操作稿 23 环节里是否要选到这些科目）——若都用不到，处置优先级可降。
