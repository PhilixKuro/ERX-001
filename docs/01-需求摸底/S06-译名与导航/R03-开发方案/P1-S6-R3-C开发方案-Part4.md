# P1-S6 开发方案 · Part4：演示站逐屏核、新基准点、全量回归与收尾

**来源需求**：[B 需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) §4.3「何时跑」、§4.9、§七实施者第 9、10 条、§八（需求 TS-013；AC-001／002／004／015）｜**前置依赖**：Part1～3 全部任务已完成｜**日期**：2026-10-09｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S6-R3-C开发方案-总纲.md](P1-S6-R3-C开发方案-总纲.md)（执行纪律见总纲 §九，本 Part 不重复）

## 接口契约

```javascript
// ---- Spike/P1S6R4-screen-check.js ——逐屏核（宿主 node 24 直接跑，DevTools 协议，无 npm 依赖；总纲 A13） ----
// 用法：node Spike/P1S6R4-screen-check.js <site_url> <screens.json> <out_dir>
// 启动与登录照 Spike/V16-cdp-run.js：--remote-debugging-port=0，从 DevToolsActivePort 读端口；
// /api/method/login 取 sid，Network.setCookie 注入。
// screens.json：[{id, stage, route|steps, wait_for, note}]——steps 为点击序列（选择器或侧栏 label），用于「由上游单据创建」类屏。
// 每屏：等 wait_for 出现 → 截图 <out_dir>/<id>.png → 在页面里跑 extract_visible_text() → 找英文词 → 记侧栏标题。
function extract_visible_text() {}   // 取可见元素的 textContent、placeholder、title、按钮文字；排除：input/textarea 的 value、.like-disabled-input 的用户数据、链接到记录的标题（data-doctype 链接的文字）
function find_english(texts, allow) {}  // 正则 /[A-Za-z]{2,}/ 命中的词，减去 allow（编码名、单位符号、币种代码、BOM、PDF、XLSX、CRM 等白名单——白名单写在 screens.json 顶部，每项带理由）
// 输出 <out_dir>/result.json：[{id, pass, english:[…], sidebar_title, screenshot}]
```

```python
# ---- Spike/P1S6R4-sidebar-dupes.py ——AC-002 前半（bench execute 跑，只读） ----
def run(site_lang: str = "zh") -> dict[str, list[str]]:
    """对站上全部 Workspace Sidebar：按 boot.get_sidebar_items 的同一取法取 Section Break 的 label，
    以 zh 译后分组，返回 {侧栏名: [重名的中文分节]}；空字典即通过。"""
```

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-010** 逐屏核与收尾 | 需求 TS-013；DEC-010；AC-001／002／004／015；完成标志①～⑤ | ① 演示站 `migrate`、`build`、`clear-cache` 后：`translation_check.run` 返回 `[]`；`check_app_order()["ok"]` 为真；`HDTH` 科目 266。② 屏清单（需求 §4.9 表一 23 环节＋末两行、表二 `/crm`／`/raven`／`/insights`）每屏一张截图、`result.json` 每屏 `pass=true`；发现过英文词的屏，补 csv 后复核为通过（回执记补了哪些词）。③ 每屏 `sidebar_title` 为「Business Flow」，或回执写明换走的屏与原因（HT-008；`/crm`、`/raven` 屏不计）。④ `P1S6R4-sidebar-dupes.py` 在演示站返回 `{}`；`HDTH` 下科目 Link 下拉搜「应收」与 `Account.account_type` 选项列表中「应收账款」各只出现一次（截图）。⑤ SL-007 ④ 的原有入口 diff 在演示站上再做一次，为空。⑥ 新空账基准点：演示站恢复到造数前的备份后，`Translation` 0 行、`_FCT` 前缀与本轮造的演示数据查无记录、`tabCash Flow Worksheet` 存在且 0 行；备份出的 4 个文件另存 `docker/backups/保留-S6收尾/`；`20261008_211805` 仍在根目录与 `保留-S5R12后/`。⑦ `frappe_china` 全量测试通过，收集条数 ≥ 215＋本 Stage 新增；通过、跳过分开报。⑧ 异常路径：`screen-check.js` 对一个故意未译的屏（测试站上临时加一条英文 label 的自有侧栏条目、不加 csv）报 `pass=false` 并列出该词——证明判据有判别力；该条目随即删除 |

**执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。**

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-014 演示站逐屏核与新基准点 | SL-010 ①～⑥、⑧ | 否 |
| TS-015 全量回归与常驻文件 | SL-010 ⑦ | 否 |

---

## 任务 TS-014：演示站逐屏核与新基准点（对应 SL-010）

### 目标
在演示站上按演示顺序逐屏证明「无英文词、侧栏不跳」，并把演示站留成干净的新基准点（总纲 A14）。

### 具体改动（操作步骤）

1. **先在测试站把脚本跑通**：写 `screens.json`（环节、路由或点击序列、等待选择器），先在测试站 6787 端口服务上跑一遍，修脚本本身的问题；做 SL-010 ⑧ 的判别力反证。
2. **核旧基准点**：`docker/backups/` 根目录与 `保留-S5R12后/` 下 `20261008_211805` 的 4 个文件都在。
3. **演示站上线本 Stage 改动**：`bench --site erx.localhost migrate`、`bench build --app frappe_china`、`bench --site erx.localhost clear-cache`，重启 `bench start` 进程。跑 SL-010 ①。
4. **备份 A（基准点候选）**：`docker/backup.sh`。记下时间戳 `{A}`。
5. **造演示数据**：按 `最小闭环操作稿.md` 环节 1–23 的路径造（`HDTH` 下；CRM 线索、商机在 `/crm` 里建）。可写成 `bench execute` 脚本放 `Spike/P1S6R4-demo-data.py`，也可在 CDP 脚本的 `steps` 里经界面做——界面做的那几屏同时就是被核的屏。
6. **逐屏核**：`node Spike/P1S6R4-screen-check.js http://localhost:8000 screens.json Spike/P1S6R4-screens/`。不通过的屏：补 csv（测试站先验、再同步到演示站 `clear-cache`）后对该屏复跑。全部通过后跑 SL-010 ③④⑤。
7. **备份 B（测试态留档）**：`docker/backup.sh`，4 个文件另存 `docker/backups/保留-S6R4测试态/`，仅供回溯。
8. **恢复到 A**：`docker/restore.sh {A}`（显式指定），恢复后 `bench --site erx.localhost migrate`（无变化即空跑）、`clear-cache`。跑 SL-010 ⑥ 的查询。
9. **新基准点**：A 即新基准点——把 `{A}` 的 4 个文件另存 `docker/backups/保留-S6收尾/`。若第 6 步期间改过 csv 或代码，A 已过时：恢复后再 `migrate`、`clear-cache`，**另出备份 C 作基准点**，A 不另存。回执写明最终基准点是哪个时间戳。
10. **自检收尾**：演示站 `translation_check.run` 返回 `[]`（AC-008 演示站一半、AC-015）。

### 验证方式
SL-010 ①～⑥、⑧。截图与 `result.json` 放 `Spike/P1S6R4-screens/`（截图不进 git 时在主仓库 `.git/info/exclude` 加该目录，开发守则「自己要排除的文件写进 `.git/info/exclude`」）。

---

## 任务 TS-015：全量回归、开发守则、README、常驻文件回写（对应 SL-010 ⑦）

### 目标
确认无回归，把本 Stage 的工程约定与系统现状写回常驻文件。

### 具体改动（操作步骤）

1. **全量回归**：`bench --site test.localhost run-tests --app frappe_china`；回执写收集、通过、跳过各几条，与 S5 收口的 215 条对比。
2. **自查方案外改动**：`git status --short`（主仓库）与 `git -C frappe-bench/apps/frappe_china status --short` 的文件清单逐个对上本方案的任务；frappe、erpnext、四个官方 App 目录 `status` 为空。
3. **README**：「desk 前端覆盖登记」节逐行复核（Part2 TS-008 三行、Part3 TS-012 三行，及 TS-011／013 若有）；「相对 zelin 的修改」节 `:120` 一句「只维护自身新增且官方词典不存在的键，避免全站覆盖官方译名」**按现状改写**——本 Stage 起有意覆盖官方译名，依据见测试侧覆盖清单；现金流四件套一节的目录路径（Part1 TS-004 已改）复核。
4. **常驻文件回写**——**先载入 `docs/流程体系/常驻文件契约.md`**，按其判据定写哪个文件、写什么、顺带清掉哪些失效内容：
   - `docs/开发守则.md`：「何时跑译名自检」（Stage 概况长效信息 #1：改过 csv 后／在演示站界面改过配置后／涉及译名的提交前／演示前，由 AI 自动跑；命令为 `bench --site <站> execute frappe_china.translation_check.run`，测试站另随测试套件跑）；D 回执各 Part「新增约定」节的条目（至少：自检函数的形态、自有 DocType 改名补丁放 `pre_model_sync`、改 app 级 json 必调 `modified`、desk 前端覆盖必登 README）。
   - `docs/项目概况.md`（Stage 概况长效信息 #2）：「数据模型」节 `Cash Flow` → `Cash Flow Worksheet`；「UI 路由结构」节「`frappe_china` 的功能目前没有导航入口」按实况改写（业务流程图标与侧栏）；「开发环境」节演示站当前状态与备份基准点（新增 `保留-S6收尾/` 一条，并标明 `restore.sh` 不带参数取哪个）；「已知限制」里译名一大条按本 Stage 结果改写（已改造的部分、仍在演示线外未处理的撞名属 DF-002）；能力表加「译名自检」「业务流程导航」。
5. **项目概况之外的长效信息**：HT-014（侧栏 URL 项对非 Administrator 是否可见）与 HT-008 若有换走侧栏的屏，写进路线文档 §四 S7 的执行清单或交 Stage 收口时判去向——D 回执列出，**本任务不改路线文档**（属 Stage 收尾，见流程中枢第 8 步）。

### 验证方式
SL-010 ⑦；常驻文件改动在 D 回执「改动清单」里逐文件列出，每条注明依据（常驻文件契约的哪条判据）。
