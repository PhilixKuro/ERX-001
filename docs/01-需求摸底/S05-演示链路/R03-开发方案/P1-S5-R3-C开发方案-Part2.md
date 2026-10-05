# P1-S5 开发方案 · Part2：测试站接入与回归、演示站接入、归位验收

**来源需求**：[B 需求文档](../R02-需求文档/P1-S5-R2-B需求文档.md) §4.3、§4.4（需求 TS-005～007）｜**前置依赖**：Part1 全部任务｜**日期**：2026-10-05｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S5-R3-C开发方案-总纲.md](P1-S5-R3-C开发方案-总纲.md)（执行纪律见总纲 §九，本 Part 不重复）

## 接口契约

```python
# ---- frappe_china/install.py（续 Part1）——归位检查 ----
PROBE_SOURCE: Final = "Formula"
"""撞源词探针。frappe_china/translations/zh.csv 译「计算方式」，HRMS 被锁 commit 的 locale/zh.po 译「公式」
（C 讨论第 1 步②#8）。frappe_china 排在 hrms 之后时 zh 取前者，否则取后者。若日后任一方改了这条译文，
check_app_order 的 translation 项会报「探针失效」而不是静默通过。"""

WHITELIST_TARGETS: Final[tuple[str, ...]] = (            # 与 hooks.override_whitelisted_methods 的三个键相同
    "erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country",
    "erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_chart",
    "erpnext.accounts.utils.get_coa",
)

class AppOrderCheck(TypedDict):
    ok: bool
    order: list[str]                 # 当前 installed_apps
    order_ok: bool                   # frappe_china 在全部已装业务 app 之后
    overrides: dict[str, str]        # 键 → get_hooks(...)[key][-1]
    overrides_ok: bool               # 三个都以 "frappe_china." 开头
    translation: dict                # {"source", "expected", "actual", "competitors": {app: 译文}}
    translation_ok: bool             # actual == expected 且 competitors 里至少一个 != expected
    company_checks_ok: bool          # check_all_cn_companies() 全部 ok
    problems: list[str]              # 每个不过的项一句话，ok 时为空

def check_app_order() -> AppOrderCheck:
    """AC-002 的检查本体。正向验收与反证用同一个函数（需求 §4.4 第 3 条要求不调序时能失败）。
    译名取 frappe.translate.get_all_translations("zh")（合并后的结果，读取端），expected 从
    frappe_china 的 csv 文件读（写入端），competitors 从各业务 app 的 csv／mo 读。"""
```

`check_app_order` 只读，不改任何状态；供 S8G-S1 的 IM-007 将来接进 `after_migrate`（本 Stage 不接，需求 §2 边界）。

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-003** 测试站接入与 S4 回归 | 需求 TS-005；DEC-006 ①②；RS-001／002；LG-003／LG-139 | ① 测试站 `list-apps` 含 crm／hrms／insights／raven（Insights 装不上时按 SL-006 的异常路径处理，其余三个照常）。② 装 HRMS **之前**先在测试站建一家中式公司（模拟 `HDTH` 的处境）；装完 HRMS 后不做任何操作，该公司已有 5 行 `Expense Claim Account`（入口 2 生效）；随后保存一次该公司，科目数 266、无 `Expense Claims`。③ 归位后 `installed_apps` 为目标顺序。④ `frappe_china` 全量测试**全部通过**，回执写明收集条数、通过与跳过各几条；S4 原有的 160 条一条不少（只增不减）。**有任何失败即停在测试站，不进 TS-007**（RS-002）。⑤ 记下装完后 `Company` 的 `on_update` 钩子实际执行次序（LG-139 的实测答案）。⑥ 清掉测试公司后测试站无 `_FCT` 前缀的公司 |
| **SL-004** 演示站接入与归位验收 | 需求 TS-006／007；DEC-004／006 ③；AC-002／006；RS-010 | ① 动演示站前：`docker/backups/` 根目录仍有 `20261004_005331` 那 4 个文件；新备份一套并另存到 `docker/backups/保留-S5装App前/`。② `up.sh` 跑完无报错，演示站 `list-apps` 含四个 App。③ `HDTH` 有 5 行 `Expense Claim Account`、科目号与映射一致；保存一次 `HDTH` 后科目数 266、`check_all_cn_companies()` 的 `extra_accounts` 为空、无 `Expense Claims`。④ 演示站 `check_app_order()["ok"]` 为真（顺序、三个覆盖、撞源词译名、建账自检四项）。⑤ **反证**（测试站上做）：把 `frappe_china` 调到 `hrms` 之前、清缓存、重启进程后，同一函数 `translation_ok` 为假、`ok` 为假；调回后再为真。⑥ 演示站业务数据仍为空：GL、SLE、客户、供应商、物料、各类发票均 0 条（与项目概况「演示站当前状态」一致） |

**执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。**

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-006 测试站：取 App、建入口二测试公司、装、归位、全量回归 | SL-003 | 否 |
| TS-007 演示站：备份、`up.sh`、`HDTH` 保存验证 | SL-004 | 否（依赖 TS-006 全过） |
| TS-008 归位检查函数与验收（含测试站反证） | SL-004 | 否 |

---

## 任务 TS-006：测试站接入四个 App 并跑 S4 全量回归（对应 SL-003）

### 目标
在一次性环境上先验掉 RW-01、RS-002 与入口 2，再动演示站（DEC-006 ①）。

### 具体改动（操作步骤，容器内 `/workspace/frappe-bench` 下执行）

1. **取 App**（不跑 `up.sh`，总纲 §九第 4 条）。逐个执行，代理同 `setup.sh` 第 0b 段（用 `GIT_CONFIG_*` 环境变量注入 `GIT_PROXY`）：
   ```bash
   bench get-app --branch main        https://github.com/frappe/crm.git
   bench get-app --branch version-16  https://github.com/frappe/hrms.git
   bench get-app --branch main        https://github.com/The-Commit-Company/Raven.git
   bench get-app --branch v3.14.2     https://github.com/frappe/insights.git      # HT-001
   ```
   每个取完 `git -C apps/<name> reset --hard <apps.json 里的 commit>`（浅克隆缺该 commit 时先 `fetch --depth 1 upstream <sha>`，同 `setup.sh` 第 3 段的取法），并按 Part1 TS-003 第 3 条配好只读 `upstream`、`core.fileMode false`。`bench get-app` 会顺带 `pip install` 与构建前端（HT-013）；任一失败时：Insights → 转 SL-006 的异常路径（Part3 TS-011），其余三个 → 暂停反馈。
   取完核对：`sites/apps.txt` 含四个名字；`git -C apps/<name> rev-parse HEAD` 与 `apps.json` 一致。
2. **建入口二测试公司**：在测试站用 `frappe_china.tests.utils.make_cn_company("_FCT 入口二", "FCT2")` 建一家中式公司并提交（`bench --site test.localhost execute` 一个临时函数，或 `bench --site test.localhost console` 粘贴；临时脚本放 `frappe-bench/` 下、用完删）。记下科目数（应为 266）。
3. **装到测试站**，次序 `crm → hrms → raven → insights`（总纲 A11）：
   ```bash
   bench --site test.localhost install-app crm
   bench --site test.localhost install-app hrms     # 输出里应见 frappe_china after_app_install 打印的补配结果
   bench --site test.localhost install-app raven
   bench --site test.localhost install-app insights
   ```
   装完 HRMS 立即查：`_FCT 入口二` 有 5 行 `Expense Claim Account`；无 `Expense Claims` 科目（HT-002）。
4. **归位**：`bench --site test.localhost execute frappe_china.install.reorder_installed_apps`；`bench --site test.localhost clear-cache`；**重启 `bench start`**——它在容器里由 honcho 跑着：结束现有进程后用 `docker compose exec -d -w /workspace/frappe-bench frappe bash -lc "bench start > logs/bench-start.log 2>&1"` 重新拉起，回执记一笔（总纲 §九第 4 条）。
5. **保存入口二公司**：在 `zh` 下 `frappe.get_doc("Company", "_FCT 入口二").save()`，再在 `en` 下保存一次；每次后核科目数 266、无 `Expense Claims`、`check_company_chart` 的 `ok` 为真。
6. **LG-139**：`frappe.get_hooks("doc_events")["Company"]["on_update"]` 打出实际列表，写进回执（三个以上 app 时钩子按 `installed_apps` 顺序拼接的实测答案）。
7. **全量回归**：`bench --site test.localhost run-tests --app frappe_china`。全部通过才继续（HT-011）；有失败即暂停反馈，回执写失败用例与报错原文，**不进 TS-007**。
8. **清理**：删 `_FCT 入口二`（站上无交易，`frappe.delete_doc("Company", ...)` 即可；HRMS 的 `on_trash` 会顺带删其关联记录）；核测试站无 `_FCT` 前缀的公司。

### 验证方式
SL-003 ①～⑥ 逐条在回执里贴命令输出要点（数字与列表）。

## 任务 TS-007：演示站接入四个 App（对应 SL-004）

### 目标
演示站装上四个 App、`frappe_china` 归位、`HDTH` 的科目表不被改动（DEC-006 ③）。

### 具体改动（操作步骤）

1. **备份前核对**（RS-010）：`ls docker/backups/20261004_005331-*` 应列出 4 个文件。不在即停，报用户。
2. **备份**：`docker/backup.sh`；把新出的 4 个文件另存到 `docker/backups/保留-S5装App前/`（`backup.sh` 每次新增一套，但 `restore.sh` 按修改时间取最新，另存才固定得住这个点，同项目概况的既有做法）。
3. **重建脚本装 App**：`docker/up.sh`。此时四个 App 已由 TS-006 克隆好，`setup.sh` 第 3 段只做对齐、第 4 段归位 remote、第 6 段按 `apps.json` 顺序装到演示站（`crm → hrms → insights → raven`）、第 6.2 段归位。核 `up.sh` 输出：HRMS 装完时打印的补配结果含 `华东弹簧有限公司` 的 5 个类型；6.2 段打出 `changed: True` 与目标顺序。
4. **重启 `bench start`**（同 TS-006 第 4 步）。
5. **`HDTH` 验证**：查 5 行 `Expense Claim Account` 与映射一致；在 `zh` 下保存一次 `HDTH`；科目数 266；`check_all_cn_companies()` 对 `HDTH` 的 `ok` 为真、`extra_accounts` 为空；`frappe.db.exists("Account", {"account_name": "Expense Claims"})` 为假。
6. **空账核对**：GL Entry、Stock Ledger Entry、Customer、Supplier、Item、Sales Invoice、Purchase Invoice、Journal Entry 计数均为 0（SL-004 ⑥）。

### 验证方式
SL-004 ①②③⑥ 逐条在回执里贴命令输出要点。第 5 步任一不符即暂停反馈，不往下做；回退手段是 `docker/restore.sh <第 2 步的时间戳>`（恢复数据库；四个 App 的代码仍在 `apps/`，属正常）。

## 任务 TS-008：归位检查函数与验收（对应 SL-004）

### 目标
AC-002 有一个能区分「归位了」与「没归位」的检查（需求 §4.4；开发守则「判据必须能区分它要区分的两种情形」）。

### 具体改动

1. **`frappe_china/install.py`**：实现接口契约里的 `check_app_order`。

   ```text
   check_app_order():
       order = frappe.get_installed_apps()
       biz = [a for a in BUSINESS_APP_ORDER if a in order]
       order_ok = "frappe_china" in order and all(order.index(a) < order.index("frappe_china") for a in biz)

       hooks = frappe.get_hooks("override_whitelisted_methods")
       overrides = {k: (hooks.get(k) or [""])[-1] for k in WHITELIST_TARGETS}
       overrides_ok = all(v.startswith("frappe_china.") for v in overrides.values())

       expected = get_translations_from_csv("zh", "frappe_china").get(PROBE_SOURCE)
       competitors = {a: v for a in biz
                      for v in [ (get_translations_from_csv("zh", a) | get_translations_from_mo("zh", a)).get(PROBE_SOURCE) ]
                      if v}
       actual = get_all_translations("zh").get(PROBE_SOURCE)
       translation_ok = bool(expected) and actual == expected and any(v != expected for v in competitors.values())
       # expected 为空或 competitors 全等于 expected → problems 写「探针失效：须换一个撞源词」，translation_ok 为假

       company_checks_ok = all(r["ok"] for r in check_all_cn_companies())   # 无中式公司时为真（空列表），problems 注明
       problems = [每个为假的项一句话，含 order／overrides／actual 与 expected 的原值]
       return AppOrderCheck(ok=order_ok and overrides_ok and translation_ok and company_checks_ok, ...)
   ```
   - `get_translations_from_csv`／`get_all_translations` 从 `frappe.translate` 引入，`get_translations_from_mo` 从 `frappe.gettext.translate` 引入——读取端用的就是这两个函数（`translate.py:172-187`）。
   - 不 import 任何业务 app 的模块。

2. **测试** `frappe_china/tests/test_install.py` 增：
   - `check_app_order` 在当前站点上 `ok` 为真（四个 App 未装时 `biz` 为空，`translation_ok` 为假且 problems 含「探针失效」——此用例在 HRMS 未装时 `skipTest`）。
   - 用 `patch("frappe.get_installed_apps")` 返回 `frappe_china` 在 `hrms` 之前的列表：`order_ok` 为假。
   - 用 `patch("frappe.get_hooks")` 让一个覆盖的末项是别的 app：`overrides_ok` 为假。

3. **演示站验收**：`bench --site erx.localhost execute frappe_china.install.check_app_order`，`ok` 为真，回执贴全部字段。

4. **反证（测试站）**——真调序，不靠 patch（patch 测不到缓存与进程这一层，HT-004）：
   ```text
   a. bench --site test.localhost execute  frappe.core.doctype.installed_applications.installed_applications.update_installed_apps_order
         --kwargs "{'new_order': ['frappe','erpnext','crm','frappe_china','hrms','insights','raven']}"
   b. bench --site test.localhost clear-cache；重启 bench start
   c. bench --site test.localhost execute frappe_china.install.check_app_order  → 期望 translation_ok 假、order_ok 假、ok 假；actual == 「公式」
   d. bench --site test.localhost execute frappe_china.install.reorder_installed_apps；clear-cache；重启
   e. 同 c → 期望 ok 真、actual == 「计算方式」
   ```
   c 若仍为真：说明缓存或进程没刷新、或探针选错——**暂停反馈**（这正是 RS-003 要抓的情形）。

### 验证方式
上述测试全过；第 3、4 步的四次输出贴进回执。约定显式化：「装完任何新 app 后跑 `reorder_installed_apps` 并以 `check_app_order` 验」记进 D 回执「新增约定」（Stage 概况长效信息 #1 的定稿形态）。
