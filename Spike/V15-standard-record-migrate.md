# V-15 探针记录：改 standard=1 导航记录后 `bench migrate` 是否覆盖字段值

**命题**：改 `standard=1` 的导航记录（`Workspace Sidebar` / `Workspace Sidebar Item` / `Desktop Icon`）后跑 `bench migrate`，**改动的字段值**是否被覆盖回 json 原值。
**日期**：2026-09-24｜**站点**：`erx.localhost`（已恢复 `20260922_145623` 演示数据）
**探针代码**：`Spike/V15_standard_record_migrate.py`（分步函数）、`Spike/V15-verify-clean.py`（收尾核验）
**结论**：三张表**均不被覆盖** → `go`。但有一条**前置陷阱**与一条**失效边界**，见 §3 / §5。

## 0. 安全前置

跑 `docker/backup.sh` 得 `20260924_231033`（旧的三份 + `保留-R6重装前/` 均未被覆盖，该脚本只 `cp` 不删）。

## 1. 测试目标（每张表一条，只改非命名字段）

| 表 | 记录 | 改的字段 | 原值 → 测试值 |
|---|---|---|---|
| `Workspace Sidebar` | `Stock` | `header_icon` | `stock` → `bug` |
| `Workspace Sidebar Item` | `Stock` 的第 3 行 | `label` | `Stock Entry` → `Stock Entry-V15TEST` |
| `Desktop Icon` | `Stock` | `icon` | `stock` → `bug` |

避开命名字段（`Workspace Sidebar.title` / `Desktop Icon.label` 都是 `autoname: field:*`），以免记录被重命名而触发 orphan 清理。`Workspace Sidebar Item` 是 `istable: 1` + `autoname: hash`，改 `label` 不动行名。

**基线**：三条记录的 `db_modified` 与 json 的 `modified` **逐字相等**（刚导入后的原始态）。

## 2. 命令序列

```bash
cd /d/ERX-001/docker                       # compose.yaml 在 docker/，不在项目根
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'
P=/workspace/Spike/V15_standard_record_migrate.py
R="docker compose exec -T -w /workspace/frappe-bench/sites frappe ../env/bin/python $P"

$R step_snapshot     # 基线
$R step_mutate       # 改三条记录（原值存 Spike/V15-state.json）
# —— 此处发现 §3 陷阱，先把 json 源改回原值 ——
docker compose exec -T -w /workspace/frappe-bench frappe bench --site erx.localhost migrate
$R step_check        # 判定
$R step_bump_json    # §5 边界：把 json 的 modified 调到未来
docker compose exec -T -w /workspace/frappe-bench frappe bench --site erx.localhost migrate
$R step_check_bumped
$R step_unbump_json  # 复位
```

两处跑法坑（都不是本命题结论，只是让探针能跑）：

- `bench execute Spike.xxx` 报 `NameError: name 'Spike' is not defined`——`/workspace/Spike` 不在 import 路径。改为直接 `env/bin/python` 跑脚本。
- 直接跑脚本须以 `/workspace/frappe-bench/sites` 为 **cwd**：frappe 的 logger 用相对路径 `os.path.join("..","logs",...)`（`frappe/utils/logger.py:24`），cwd 不对会 `FileNotFoundError: /workspace/logs/database.log`。

## 3. ⚠ 前置陷阱：`developer_mode=1` 下 `save()` 会把改动写回 app 的 json 源

本站点 `site_config.json` 有 `"developer_mode": 1`。`doc.save()` 之后发现 **json 源文件自己也变成了测试值**——即 DB 与 json 同时被改，此时跑 migrate 看"没被覆盖"是**假阳性**（两边一样，无从覆盖）。

导出发生在：

- `frappe/desk/doctype/workspace_sidebar/workspace_sidebar.py:48-63` —— `before_save()` → `export_sidebar()`
- `frappe/desk/doctype/desktop_icon/desktop_icon.py:58-81` —— `on_update()` → `export_desktop_icon()`

两处的门槛一致：

```python
allow_export = self.app and self.standard and not frappe.flags.in_import and frappe.conf.developer_mode
```

实测被改动的文件（只有对应那几行变，其余字节不动，故可精确改回）：

```
erpnext/erpnext/workspace_sidebar/stock.json   header_icon / 那一行 label / modified
erpnext/erpnext/desktop_icon/stock.json        icon / modified
```

**处置**：把这两个 json 精确改回原值（含 `modified`），核到 `git status --porcelain` 为空（与 HEAD 逐字节一致），才构成有效测试条件：**DB 是测试值且 `modified` 较新，json 是原值且 `modified` 较旧**。

> 对 CR-010 的含义（事实陈述，不含建议）：在 `developer_mode=1` 的机器上改 standard 导航记录，改动会同时落进 app 源码目录，成为 app 仓库的工作区改动。

## 4. 判定：三张表均不被覆盖

`bench migrate` 跑完无报错。`step_check` 实测：

| 表 | 字段 | json 原值 | 探针设的值 | migrate 后 | 被覆盖? |
|---|---|---|---|---|---|
| `Workspace Sidebar` | `header_icon` | `stock` | `bug` | **`bug`** | 否 |
| `Workspace Sidebar Item` | `label` | `Stock Entry` | `Stock Entry-V15TEST` | **`Stock Entry-V15TEST`** | 否 |
| `Desktop Icon` | `icon` | `stock` | `bug` | **`bug`** | 否 |

三条记录的 `db_modified` 在 migrate 前后**一字未变**，且子表行名仍是 `d25tkm7tnm`——说明不是"导入后又写回同值"，而是**导入整条被跳过**。

## 5. 覆盖判据（实测 + 读码）与失效边界

**判据是比对 `modified` 时间戳，不是比对 hash。** 源码 `frappe/modules/import_file.py:128-142`：

- `stored_hash` 只在 `doc["doctype"] == "DocType"` 时才读（`:130-134`），故这三张表**根本不走 hash 分支**；`migration_hash` 字段也只有 DocType 有。
- 判据落在 `:141`：`is_db_timestamp_latest and doc["doctype"] != "DocType"` → `continue`（跳过导入）。其中 `is_db_timestamp_latest` = `get_datetime(json.modified) <= get_datetime(db.modified)`（`:124-126`）。
- 任何 `doc.save()` 都把 `db.modified` 刷成 `now()`，必然新于 json 的 `modified`，于是导入被跳过——这就是改动能留住的原因。

**失效边界（已实测，非推断）**：把两个 json 的 `modified` 调到未来（`2026-12-31`，字段值仍留 json 原值）再跑一次 migrate，三张表**全部被打回 json 原值**：

| 表 | migrate 前 | json 原值 | 第二次 migrate 后 |
|---|---|---|---|
| `Workspace Sidebar` | `bug` | `stock` | **`stock`**（被覆盖）|
| `Workspace Sidebar Item` | `Stock Entry-V15TEST` | `Stock Entry` | **`Stock Entry`**（被覆盖）|
| `Desktop Icon` | `bug` | `stock` | **`stock`**（被覆盖）|

即：**改动能维持到上游升级换掉那个 json 文件为止**（升级带来的新文件 `modified` 更新，即触发覆盖）。

顺带两条同源事实：

- 覆盖时子表**整表删后重插**——`Stock Entry` 那一行的行名从 `d25tkm7tnm` 变成 `9h1c109pd0`（`import_doc` → `delete_old_doc` → `doc.insert()`，`import_file.py:229-238`）。任何按子行 name 的外部引用都会断。
- 读码（**本探针未实测**）：`:123-128` 若记录在 DB 中不存在，`db_modified_timestamp` 为 `None`，守卫整段被跳过而**无条件导入**。即"改字段值"留得住，但"整条删掉"会在下次 migrate 被重建。

## 6. 对命题前提的一处更正：`Desktop Icon` 在 migrate 路径上不是生成的

命题背景写的是 `Desktop Icon` 由 `create_desktop_icons_from_workspace()` 生成、"生成源与 json 导入源不是一回事"。实际全仓调用点只有一处：`frappe/utils/install.py:203`（`auto_generate_icons_and_sidebar`），即**装站 / 装 app 时**才跑；`frappe/migrate.py` 里没有任何调用。

`bench migrate` 走的是 `frappe/model/sync.py:120-126`：

```python
app_level_folders = ["desktop_icon", "workspace_sidebar", "sidebar_item_group"]
```

三类都按 app 级目录 `<app>/<app>/<folder>/*.json` 逐文件 `import_file_by_path`。故 `Desktop Icon` 与 `Workspace Sidebar` 在 migrate 上**走同一条 json 导入路径、同一套判据**——这与 §4 三张表行为一致的实测结果吻合。`erpnext/erpnext/desktop_icon/` 下确有 24 个 json，`frappe/frappe/desktop_icon/` 下 11 个。

`Workspace Sidebar Item` 则**没有自己的 `standard` 字段**（`istable: 1`，字段表里无 `standard`），它不被单独导入，而是随父 `Workspace Sidebar` 的 json 一起进出。三张表的 `standard` 语义因此只有两套，不是三套。

## 7. 收尾核验（`Spike/V15-verify-clean.py`）

- 字段值：`header_icon=stock` / `label=Stock Entry` / `icon=stock`，均已回原值。
- `db_modified` 已复位到与 json 相等（`step_unbump_json` 用 `frappe.db.set_value(..., update_modified=False)` 直写，不触发 `on_update`，故不会再次导出 json）。
- `-V15TEST` / `bug` 全库零残留（`Workspace Sidebar Item` / `Workspace Sidebar` / `Desktop Icon` 三表各查一遍）。
- `erpnext` app `git status --porcelain` 为空——两个 json 与 HEAD 逐字节一致。
- 记录数与基线同：`Workspace Sidebar` 32 / `Workspace Sidebar Item` 573 / `Desktop Icon` 35。
- 演示数据完好：1 公司 `华东弹簧` / 95 科目 / 6 仓库 / 财年 `2026` / 2 Item / 1 BOM / 2 销售订单。

一处**非本探针造成**的附带现象：第一次 migrate 日志有 `Deleting icon Frappe Framework`，来自 `delete_duplicate_icons()`（`sync.py:315-328`）清理重命名后的陈旧 App 图标；现存 App 类图标为 `Framework`(frappe) 与 `ERPNext`(erpnext)，总数仍 35。与本命题的三条测试记录无关。
