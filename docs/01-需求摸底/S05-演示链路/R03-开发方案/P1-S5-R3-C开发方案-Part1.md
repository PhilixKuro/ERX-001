# P1-S5 开发方案 · Part1：版本锁定、重建脚本、归位与报销类型科目预配

**来源需求**：[B 需求文档](../R02-需求文档/P1-S5-R2-B需求文档.md) §4.2（需求 TS-001～004）｜**前置依赖**：无｜**日期**：2026-10-05｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S5-R3-C开发方案-总纲.md](P1-S5-R3-C开发方案-总纲.md)（执行纪律见总纲 §九，本 Part 不重复）

## 接口契约

```python
# ---- frappe_china/install.py ——安装期钩子与归位 ----
BUSINESS_APP_ORDER: Final[tuple[str, ...]] = ("crm", "hrms", "insights", "raven")   # ADR-0003
TAIL_APPS: Final[tuple[str, ...]] = ("frappe_china", "frappe_debug")              # 恒在末尾，按此先后

def target_app_order(installed: list[str]) -> list[str]:
    """纯函数。frappe 居首、erpnext 次之；BUSINESS_APP_ORDER 中已装的按该序；
    其余未知 app 保持原相对顺序；最后是 TAIL_APPS 中已装的。不增不减（集合与入参相同）。"""

def reorder_installed_apps() -> dict:
    """把站点的 installed_apps 调成 target_app_order(当前)。幂等：已是目标顺序则不写、不留 Version。
    返回 {"changed": bool, "before": list[str], "after": list[str]}。供 setup.sh 经 bench execute 调用。"""

def after_app_install(app_name: str) -> None:
    """hooks.after_app_install。app_name == "hrms" 时对全部中式公司补配报销类型科目（需求 §4.2.2 入口 2）；其余 app 不动作。"""

# ---- frappe_china/accounting/hr.py（新增）——HRMS 报销类型科目预配 ----
def set_cn_expense_claim_accounts(company: str) -> list[str]:
    """为一家中式公司配 5 个报销类型的默认科目（映射见 cn_tax/data/company_defaults.json 的 expense_claim_type）。
    站点无 Expense Claim Type DocType → 返回 []、零查询之外不做任何事。
    只配缺的：该类型对该公司已有 Expense Claim Account 即跳过，不覆盖。
    映射里的科目号在该公司查不到 → 收齐后一次 throw（同 _throw_missing_accounts 口径），不写空值。
    返回本次新配的类型名列表。"""

def backfill_cn_expense_claim_accounts() -> dict[str, list[str]]:
    """对全部中式公司（chart_of_accounts == CN_CHART_NAME，与 check_all_cn_companies 同一筛法）调上者。
    返回 {公司名: 新配类型}。after_app_install 与人工修复共用。"""
```

`docker/apps.json` 条目结构（新增两个可选字段）：

```json
{ "url": "...", "branch": "version-16", "tag": "v3.14.2", "commit": "<40位>", "app_name": "insights", "official": true }
```

- `tag` 与 `branch` 二选一：有 `tag` 时按 tag 取，`branch` 不写。
- `official: true`：url 就是官方仓库、本项目不 fork（DEC-001）。缺省为假（frappe／erpnext／frappe_china 照旧是自有 fork）。

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-001** 版本锁定与重建脚本 | 需求 TS-001／002／003；DEC-001／003／015；需求 §4.2.1 五条 | ① `apps.json` 共 7 条，顺序为 `frappe, erpnext, crm, hrms, insights, raven, frappe_china`；四个新条目 `official: true`、commit 为 40 位且分别以 `6f5ac249`／`deedce73`／`5447f162`／`e890308e` 开头，Insights 用 `tag: v3.14.2`、无 `branch`。② `setup.sh` 第 3 段对 tag 条目能取到并对齐到锁定 commit；**预检对不存在的分支或 tag 报错退出**（`ls-remote --exit-code`，异常路径）。③ 第 6 段按 `apps.json` 顺序装；`apps/` 下有而 `apps.json` 没有的 app 打警告、不装（异常路径）。④ 第 6 段之后归位：`frappe_china` 已装时调 `reorder_installed_apps`，第二次跑 `changed` 为假（幂等）；`frappe_china` 未装时跳过并打一行说明（边界）。⑤ 第 4 段：官方 App 只有 `upstream`（官方地址，push 地址为 `DISABLED_use_origin_instead`），无 `origin`；frappe／erpnext／frappe_china 的 remote 不变。⑥ `lock-apps.sh` 写入后 `git diff docker/apps.json` 只可能出现 commit 变化：顺序不变、Insights 的 `tag` 保留且不出现 `"branch": "HEAD"`、官方 App 的 url 不变；`apps/` 下有而 `apps.json` 没有的 app 追加到末尾并打警告。⑦ `target_app_order` 单测覆盖：常规七个；缺某个业务 app；有未知 app；`frappe_debug` 在场；入参已是目标顺序；入参无 `frappe_china` |
| **SL-002** 报销类型科目预配 | 需求 TS-004；DEC-005；需求 §4.2.2 入口 1、2 | ① 新建中式公司后：5 个报销类型对该公司各有一行 `Expense Claim Account`，科目号与映射一致；该公司无名为 `Expense Claims` 的科目；科目数 266。② 删掉某公司的 5 行后调 `after_app_install("hrms")`：5 行补回。③ 某类型已有指向别的科目的行时再调：该行不变、返回值不含该类型（只配缺的）。④ `after_app_install("crm")`：零写入。⑤ 映射科目号查不到：报错并列出全部缺项，不写入任何一行（异常路径）。⑥ 站点无 `Expense Claim Type`：返回空、不报错（依赖不可用）。⑦ 同一公司分别在 `zh` 与 `en` 下保存一次，科目数不变、无 `Expense Claims`（LG-003）。⑧ `frappe_china` 不在模块顶层 import `hrms`、`required_apps` 不含 `hrms`（静态检查） |

**执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。**

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-001 `apps.json` 加条目、改顺序 | SL-001 | 否 |
| TS-002 归位函数 | SL-001 | 否（TS-003 调它） |
| TS-003 `setup.sh` 四处改动 | SL-001 | 与 TS-005 可并行 |
| TS-004 `lock-apps.sh` 保序保 tag | SL-001 | 与 TS-005 可并行 |
| TS-005 报销类型科目预配 | SL-002 | 与 TS-003／004 可并行（文件不相交） |

---

## 任务 TS-001：`apps.json` 加四个条目并改为装载顺序（对应 SL-001）

### 目标
`apps.json` 成为「装哪些 app、按什么顺序装、锁哪个版本」的唯一清单（总纲 A1～A3）。

### 具体改动
`docker/apps.json`：重排为下表顺序，四条新增。commit 取 2026-10-05 已核的完整 SHA。

| # | app_name | url | branch／tag | commit | official |
|---|---|---|---|---|---|
| 1 | frappe | `https://github.com/PhilixKuro/frappe.git` | branch `version-16` | 不变 | — |
| 2 | erpnext | `https://github.com/PhilixKuro/erpnext.git` | branch `version-16` | 不变 | — |
| 3 | crm | `https://github.com/frappe/crm.git` | branch `main` | `deedce73c1eb48577e7f70e95df6bac1dc55c93f` | true |
| 4 | hrms | `https://github.com/frappe/hrms.git` | branch `version-16` | `6f5ac249283f6fa1013fd5616f3d95f686ba7bb2` | true |
| 5 | insights | `https://github.com/frappe/insights.git` | **tag `v3.14.2`** | `5447f1621c0e6593994286807fe2521e03f1b0b4` | true |
| 6 | raven | `https://github.com/The-Commit-Company/Raven.git` | branch `main` | `e890308e967fdc6510d88b9f16cb1dbda321b1ea` | true |
| 7 | frappe_china | `https://github.com/PhilixKuro/FrappeChina.git` | branch `main` | 不变 | — |

`docker/README.md`「版本记录」段补两句：`apps.json` 的顺序就是装载顺序；`official`／`tag` 两个字段的含义。

### 验证方式
`python -c "import json;print([a['app_name'] for a in json.load(open('docker/apps.json',encoding='utf-8'))])"` 输出与上表顺序一致；四个新 commit 各用 `git ls-remote <url>` 核对一次与分支头或 tag 相符（锁定后上游可能已前进，此时只核 commit 存在：`git fetch <url> <sha>` 成功）。

## 任务 TS-002：归位函数（对应 SL-001）

### 目标
一个幂等、自校验的入口，把 `frappe_china` 调到全部业务 app 之后（DEC-003；总纲 A4／A5）。

### 具体改动
`frappe_china/install.py`：新增接口契约里的 `target_app_order`、`reorder_installed_apps`。

```text
target_app_order(installed):
    head = [a for a in ("frappe", "erpnext") if a in installed]
    biz  = [a for a in BUSINESS_APP_ORDER if a in installed]
    tail = [a for a in TAIL_APPS if a in installed]
    other = [a for a in installed if a not in head + biz + tail]   # 原相对顺序
    out = head + biz + other + tail
    assert sorted(out) == sorted(installed)
    return out

reorder_installed_apps():
    before = frappe.get_installed_apps()
    after  = target_app_order(before)
    if after == before: return {changed: False, before, after}
    update_installed_apps_order(after)        # 框架入口：校验不增不减、frappe 居首、写 Version、限 System Manager
    update_site_config("installed_apps", frappe.get_installed_apps())   # LG-010（A5）
    frappe.clear_cache()                      # 全局键与 client_cache；进程内缓存靠重启，见 TS-003
    return {changed: True, before, after: frappe.get_installed_apps()}
```

- `update_installed_apps_order` 从 `frappe.core.doctype.installed_applications.installed_applications` 引入；`update_site_config` 从 `frappe.installer` 引入。
- `bench execute` 以 Administrator 连接，满足 `only_for("System Manager")`；该命令结束时自动 commit。

`frappe_china/tests/test_install.py`：新增 `target_app_order` 的六个用例（SL-001 ⑦），纯函数、不碰站点；另加一个用例在当前站点上调 `reorder_installed_apps` 两次，断言第二次 `changed` 为假（站点上已有哪些 app 都成立）。

### 验证方式
`bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_install`。

## 任务 TS-003：`setup.sh` 四处改动（对应 SL-001）

### 目标
新机器按 `apps.json` 重建出与本机同版本、同顺序、`frappe_china` 已归位的站（需求 §4.2.1 第 1～4 条）。

### 具体改动
`docker/scripts/setup.sh`：

1. **第 3 段解析**：python 片段多输出两列——`ref`（有 `tag` 取 tag，否则取 `branch`，再缺省 `version-16`）与 `official`（`1`／`0`）；空字段仍写 `-`（R17 FD-049 的约束）。`app_entries` 一并保留给第 4、6 段用。
2. **第 3 段预检**：`git ls-remote --exit-code --heads --tags "$app_url" "refs/heads/$ref" "refs/tags/$ref"`；非零即报「分支或 tag `$ref` 不存在或访问不了」并退出。原注释里「`--heads`」的说法改正。`bench get-app --branch "$ref"`（HT-001）。tag 克隆出的仓库 HEAD 是游离的，后面「对齐到锁定 commit」的 `reset --hard` 照常可用；日志里「仍在 $app_branch 分支」一句在 tag 条目上改说「停在 tag $ref」。
3. **第 4 段 remote 归位**：`official=1` 的 app——`upstream` 设为 `apps.json` 里的 url、push 地址设 `DISABLED_use_origin_instead`，**删除 `origin`（若有）**，不把 `upstream` 当成 fork；其余 app 保持现逻辑。为此第 4 段改为遍历 `app_entries` 拿 url 与 `official`，`apps/` 下不在 `apps.json` 里的目录照旧只设 `core.fileMode false`。
4. **第 6 段装 app 的顺序**：改为遍历 `app_entries`（跳过 frappe），按 `apps.json` 顺序 `install-app`；之后遍历 `apps/*/`，凡不在 `apps.json` 里的打警告「未在 apps.json 声明，未安装」。
5. **新增第 6.2 段「归位」**：`frappe_china` 在 `list-apps` 里时执行 `bench --site "$SITE_NAME" execute frappe_china.install.reorder_installed_apps`，打出返回值；不在则打「frappe_china 未安装，跳过归位」。段末提示：「若 bench start 正在跑，重启它（docker/start.sh）才按新顺序取钩子」（HT-004）。

注释沿用本文件写法：每处改动注明原因与需求编号（S5 需求 §4.2.1 第 n 条）。

### 验证方式
`bash -n docker/scripts/setup.sh`；行为在 TS-007（演示站经 `up.sh` 装 App）与 TS-016（空目录重建演练）实测。预检的异常路径在 TS-016 用一个临时改坏 tag 的 `apps.json` 副本验（见 Part4）。

## 任务 TS-004：`lock-apps.sh` 保序、保 tag、认官方 App（对应 SL-001）

### 目标
跑 `lock-apps.sh` 只更新 commit，不把顺序、tag、官方 url 写坏（需求 §4.2.1 第 5 条及总纲 §六第 2 行）。

### 具体改动
`docker/lock-apps.sh` 的 python 段：

```text
entries = json.load(apps.json)                  # 原顺序
by_name = {e.app_name or basename(url): e}
dirs    = [d for d in sorted(apps/*) if (d/.git).exists()]
for e in entries (按原顺序):
    d = apps/<e.app_name>；不存在 → 原样保留该条并打警告「未克隆」
    sha = rev-parse HEAD
    if e.official:  url = e.url（不读 remote）
    else:           url = remote get-url origin，取不到再 upstream，再取不到保留 e.url
    if e.tag:       保留 tag，不写 branch
    else:
        br = git symbolic-ref -q --short HEAD
        br 为空（游离）→ 保留 e.branch，打警告「HEAD 游离，branch 沿用 apps.json」
        否则 branch = br
    e.update(url, commit=sha)
for d in dirs 不在 entries 里: 追加 {url, branch, commit, app_name}，打警告「新 app，已追加到末尾，请确认装载顺序」
写回（indent=2, ensure_ascii=False）
```

`--show` 一行多显示 `tag` 或 `branch` 与 `official` 标记。

### 验证方式
TS-016 第 3 步：主 bench 装完四个 App 后跑 `docker/lock-apps.sh --show` 与写入，`git diff docker/apps.json` 为空（commit 未变时）。另手工构造一个缺条目的 `apps.json` 副本（`cp` 到临时文件、改 `APPS_JSON` 不必，直接在 git 工作区改后验、再 `git checkout` 还原——`checkout` 只还原本任务自己改的这一个文件，属可撤销操作）验「追加到末尾并警告」。

## 任务 TS-005：HRMS 报销类型科目预配（对应 SL-002）

### 目标
保住 S4 的科目表：HRMS 在场时，中式公司的 5 个报销类型都已有默认科目，HRMS 的 `set_expense_claim_type_accounts` 因此全部跳过、不建 `Expense Claims`（DEC-005）。

### 具体改动

1. **`frappe_china/cn_tax/data/company_defaults.json`** 新增键 `expense_claim_type`：

   ```json
   "expense_claim_type": { "Calls": "5602090", "Food": "5602040", "Medical": "5602010", "Others": "5602250", "Travel": "5602130" }
   ```
   `_comment` 补一句：映射待领域专家确认（需求 §4.2.2、LG-011）。五个科目号已核为本科目表中的明细科目（`is_group=0`）。

2. **`frappe_china/accounting/hr.py`**（新增）：实现 `set_cn_expense_claim_accounts`、`backfill_cn_expense_claim_accounts`。

   ```text
   set_cn_expense_claim_accounts(company):
       if not frappe.db.exists("DocType", "Expense Claim Type"): return []
       mapping = _load_defaults()["expense_claim_type"]
       todo = [t for t in mapping if frappe.db.exists("Expense Claim Type", t)
               and not frappe.db.exists("Expense Claim Account", {"parent": t, "company": company})]
       不在站上的类型 → logger warning（用户删过），不报错
       accounts = {t: _account_name(company, mapping[t]) for t in todo}
       missing = [f"{t}={mapping[t]}" for t, a in accounts.items() if not a]
       _throw_missing_accounts(company_doc_like, missing)    # 先收齐、一次报
       for t, a in accounts.items():
           d = frappe.get_doc("Expense Claim Type", t)
           d.append("accounts", {"company": company, "default_account": a})
           d.save(ignore_permissions=True)
       return list(accounts)
   ```
   - `_load_defaults`、`_account_name`、`_throw_missing_accounts` 从 `frappe_china.accounting.company` 引入；`_throw_missing_accounts` 现收 `doc` 只用 `doc.name`，传 `frappe._dict(name=company)` 即可，不改其签名。
   - **不 import `hrms` 的任何模块**；只按 DocType 名操作。

3. **入口 1**：`frappe_china/accounting/company.py` 的 `build_cn_company` 末尾（`setup_cn_taxes` 之后）调 `set_cn_expense_claim_accounts(doc.name)`。此时 `ignore_chart_of_accounts` 仍为真，HRMS 的两个建科目钩子无论排在前后都不建科目：排在前面时被该标志挡掉；排在后面时 5 行已配好、全部跳过（HT-003）。

4. **入口 2**：`frappe_china/hooks.py` 加 `after_app_install = "frappe_china.install.after_app_install"`；`install.after_app_install(app_name)` 在 `app_name == "hrms"` 时调 `backfill_cn_expense_claim_accounts()` 并打印结果。依据 HT-002：框架先跑 HRMS 的 `after_install`（建 5 个类型），再调已装 app 的 `after_app_install`。
   - **新机器按 `apps.json` 重建时 HRMS 先于 `frappe_china` 装**，此钩子不会因 HRMS 触发——但此时还没有中式公司，之后建公司走入口 1。恢复备份的站点自带已配好的行。两条路径都不漏，故 `after_install` 不另加补配。

5. **测试** `frappe_china/tests/test_expense_claim.py`（新增，继承 `FrappeChinaTestCase`）：`setUpClass` 里若 `Expense Claim Type` DocType 不存在则 `skipTest("HRMS 未安装")`。用例对应 SL-002 ①～⑦；⑥ 用 `patch("frappe.db.exists")` 让 DocType 判为不存在；⑤ 用 `patch` 让 `_account_name` 对一个科目号返回 `None`，断言报错文本含该科目号且 5 个类型都没新增行；⑦ 显式设 `frappe.local.lang`，`zh`、`en` 各保存一次公司。⑧ 写进 `test_scaffold.py`：读 `hooks.py` 断言 `required_apps == ["erpnext"]`；`grep` 等价地扫 `frappe_china/**/*.py` 顶层无 `import hrms`／`from hrms`。

### 验证方式
HRMS 未装时（TS-006 之前）：`run-tests --module frappe_china.tests.test_expense_claim` 报「跳过」、其余全过。HRMS 装上后（TS-006）：该模块全过。约定显式化：「依赖可选 app 的功能只在该 DocType 存在时生效、模块顶层不 import 它」记进 D 回执「新增约定」。
