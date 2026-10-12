# S6 R6 方案 TS-019／TS-021 给译者的指令

本目录（批量档）与 `Spike/P1S6R6-demo/`（演示线档）的每一块都按本文件译。依据：R6 开发方案 TS-021 第 2 步、需求 §4.2.2～§4.2.4、DEC-029。

## 输入与输出

- 输入 `in-*.json`：`{"group": app, "items": [{"key", "refs", "current", "context"}]}`。`key` 是源词（有 `:` 后缀的是 `源词:context`），`refs` 是出处，`context` 是出处前后各 3 行源码，`current` 是合并字典现值（多为空或英文原样）。
- 输出同名 `part-*.csv`（把 `in-` 换成 `part-`，扩展名 `.csv`），UTF-8，无表头。每个 `key` 恰好一行：
  - 无 context：`源词,译文`
  - 有 context（`key` 里 `:` 之后是 context）：`源词,译文,context`
  - 按 CSV 规则加引号：字段含逗号、双引号、换行或首尾空格时整字段加双引号，内部双引号写两个。源词逐字照抄（含首尾空格、`\n` 字面量），不改大小写。
- 拿不准的，照样给最好的译文，另在 `doubt-*.txt` 每行写 `键<TAB>原因`。

## 译法

1. **简体中文、大陆 ERP 用词**。禁止取 `zh_TW.po` 原文或繁体字（帳、戶、資、料、單、據、發、與、價、為等），禁止台湾用词（如「帐号」写「账号」，「资料」在指数据时写「数据」，「项目」不要写成「专案」，「档案」写「文件」，「设定」写「设置」，「讯息」写「消息」，「伺服器」写「服务器」）。
2. **整句意译，不逐词对译**。读 `context` 看这条在界面哪里、什么时候出现，再定译文。不得出现「是 您 sure」「登录 带 密码」这类词对词拼接；汉字与汉字之间不留空格。
3. **不中英夹杂**。译文里不留英文单词。例外：全大写缩写（PDF、API、SQL、URL、ID、SKU、UOM、BOM、GST、VAT、CRM、AI、LLM、JSON、CSV 等）照原样；品牌与产品名（Frappe、ERPNext、Raven、Insights、OpenAI、Google、WhatsApp、Slack 等）照原样——**品牌名要保留时，只在确实是专有名词处保留**。英文代码标识符（字段名 `due_date`、函数名、`doc.status` 之类）在示例代码里照原样。
4. **占位符与 HTML 原样保留**：`{0}`、`{1}`、`{}`、`%s`、`%(name)s`、`{{ var }}`、`${type}` 等个数与写法不变（中文语序需要时可调换次序）；HTML 标签（`<b>`、`<br>`、`<a href=…>`）原样、次序不变；Markdown（`**`、`##`、列表符）保留。
5. **不加不减**：不添加原文没有的意思，不省略原文的意思；句末标点用中文标点（`。`、`，`、`？`、`：`），原文无句号的短标签不加句号。
6. **单据用「单／凭证／底稿」，「表」留给报表**（需求 §4.2.4）。例：Timesheet → 工时单，Job Card → 生产任务单，Stock Entry → 物料移动。

## 术语表（必须一致）

按以下顺序查，先查到的为准：

1. `Spike/P1S6R7/glossary.json`：本轮已定的全部词（点名用词、S3 术语标准定稿词、演示线档已定词）。键 → 定稿译文。
2. 查合并字典现译：`python -I -X utf8 Spike/P1S6R7/lookup.py "<英文词>"` 打印该词的现译与含该词的已有译文，**与官方既有用词保持一致**（如 Item → 物料、Warehouse → 仓库、Account → 科目、Customer → 客户、Supplier → 供应商、Sales Order → 销售订单、Purchase Receipt → 采购入库、Delivery Note → 销售出库、Stock Entry → 物料移动、Work Order → 生产工单、BOM → 物料清单、Payment Entry → 收付款凭证、Journal Entry → 日记账凭证、Cost Center → 成本中心、Company → 公司、Lead → 线索、Deal → 商机、Channel → 频道、Workspace → 工作区、Agent → 智能体、Bot → 机器人、Function → 函数、Insights 的 Query → 查询、Dashboard → 仪表板、Chart → 图表）。
3. 二者都没有的，自定，记进 `doubt-*.txt` 写「新词」。

## 自查（交付前）

- 行数等于 `items` 数，无空译；
- 每行跑一遍：无繁体字、无「中文：」或 `???` 占位、汉字间无空格、无非缩写英文单词；
- 占位符与 HTML 和源词逐个对上。

主 Session 合并时用 `Spike/P1S6R7/merge_check.py` 机检，任一条不过整块退回重译。
