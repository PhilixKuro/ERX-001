# ADR-0012: `erx_core` 内部模块最少——`modules.txt` 现只列 1 个

- 状态：accepted
- 日期：2026-09-25 / 决策者：用户裁决（C 步第 15 步①），Claude 提选项
- 对应决策：DEC-063

## 上下文

Frappe 的「模块」（`modules.txt` + `Module Def`）不只是代码组织单位。C 步查出一条机制（发现十五）：

`get_module_list` → `add_module_defs` → `auto_generate_sidebar_from_module()`，**每个 `Module Def` 自动生成一个 hammer 侧栏进 boot**（`__init__.py:899`、`installer.py:749-755`、`workspace_sidebar.py:239-252`）。

⇒ **模块划分是界面决策，不只是代码决策。** 而 CR-010 的方向正是「折叠无关入口」。

## 决策

**`modules.txt` 现在只列 1 个模块：`cn_tax`**（中国财税，承载 8 个 DocType + 3 个 Report）。其余代码放**普通 python 包**，不进 `modules.txt`：

| 目录 | 内容 | 是否模块 |
|---|---|---|
| `cn_tax/` | 8 DocType + 3 Report + 科目表 JSON | ✅ `modules.txt` 列 1 项 |
| `i18n/` | 译名 csv + 自检 | 普通包 |
| `patches_mfg/` | 服务端修正的 `doc_events` handler | 普通包 |
| `demo/` | 演示操控 whitelisted 方法 + 节点 js + 数据生成器 + 数据集 json | 普通包 |
| `workspace_sidebar/` | 自有侧栏 json | app 级 json 目录（`sync.py:120`） |
| `desktop_icon/` | 入口图标 json | app 级 json 目录 |

**判据须写进 app 的 README**：需要 `Module Def` 的只有 DocType／Report／Page／Workspace，纯代码放普通包。

## 后果

**正面**
- 只多出 1 个 hammer 侧栏，而非 6 个。与 CR-010 的方向一致。
- `modules.txt` 可随时追加，现在预留无收益。

**负面**
- 「中国财税」这件事的代码分散于三处：模块 `cn_tax/`、`hooks.py`（覆盖位与 `doc_events`）、`after_install`（配置数据）。**C 步复核建议把这条界线点名为模块边界最模糊处**，并给出收拢办法（让 `after_install` 只调用 `cn_tax` 模块内的一个入口函数）。**本步裁定采纳该收拢办法**：`after_install` 不写业务逻辑，只按序调用 `cn_tax` 内的入口函数。这样「中国财税」的逻辑全在模块内，`hooks.py` 与 `after_install` 只剩接线。
- **⚠ `cn_tax` 的对外接口 16 项，命中 C 步分解检查的拆分信号「公开接口超过 10 个」。** 如实登记：若将来报表继续增加，应把「报表」独立成第二个模块。

**中性**
- 普通包与模块的区别对读代码的人不直观（目录长得一样），故判据必须写进 README，否则下一个人会把普通包当模块加进 `modules.txt`。

## 备选方案

**按域分 6 个模块** —— 代码组织最清楚，每域一个模块。**没选**：**发现十五**——`modules.txt` 每多一项，`auto_generate_sidebar_from_module()` 就自动生成一个 hammer 侧栏进 boot ⇒ 6 个模块＝自己又造 6 个噪音入口，**与 CR-010「折叠四个第三方 App 的无关入口」直接相悖**。见 NV-048。

**只 1 个模块装全部**（含将来的生产增强报表）—— 界面成本最低。**没选**：中国财税的 8 个 DocType 与将来的生产增强报表混在一个模块下，**Report 的模块归属会体现在报表列表分组里**，客户看到财税报表与产能报表同组。见 NV-049。故取「现在 1 个、演示后追加第 2 个」而非「永远 1 个」。

## 关联

- 依赖：ADR-0001（单 app 内才有「内部怎么分模块」这个问题）、ADR-0007（`cn_tax` 的 8 DocType 与覆盖位来自该决策）
- 被依赖：前瞻性设计 P-3（`modules.txt` 留出第二个模块位置 → IM-010／IM-011）
- 取代：无

## 失效条件

演示后做需求图谱 §3.2 那批时追加第 2 个模块（生产增强）；若报表继续增加应把「报表」独立成第三个。
