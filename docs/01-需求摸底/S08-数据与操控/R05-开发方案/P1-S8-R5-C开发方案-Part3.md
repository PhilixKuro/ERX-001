# P1-S8 数据与操控 —— 开发方案·Part3：演示框架、快照与换库、彩排、九幕与收尾

**来源需求**：[R4 B 需求文档](../R04-需求文档/P1-S8-R4-B需求文档.md) §4.2～4.4、§4.15｜**前置依赖**：Part1 TS-001；Part2 全部（TS-023 起）｜**日期**：2026-10-20｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S8-R5-C开发方案-总纲](P1-S8-R5-C开发方案-总纲.md)——A4～A10，偏离 1／2／9～11／14～19，HT-011／012／015～018 在那里。

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-012** 演示框架核心 | 需求 TS-013、CR-008、`PH-P1003`、DEC-006／009、R2 DEC-014；A8／A9／A10 | ① 配置校验（单测＋浏览器）：未知动作、未知命名函数、引用未定义的 `save_as`、缺必填键、引用不存在的场景日期，各一例，开播前报错并指出「第 N 幕第 M 步」，不执行任何一步；② 十三个通用动作在 s8dev 上各有一步跑通（一份测试配置，彩排模式，截图或日志）；③ 现场新建的销售订单、采购入库、付款单三类单据业务日期 ＝ 本幕场景日期、`set_posting_time`＝1，保存时不出 OB-075 确认框；④ 由映射生成的新表单（采购订单→采购入库）同样带场景日期；服务端代建的单据（生产计划建工单、工单提交建工序卡、物料需求→采购订单）业务日期 ＝ 场景日期（A8，查库）；生成器内不改（显式日期不被冲掉）；⑤ `save_as` 记下的单号在刷新页面、换库（SL-014 后）、跨 desk／`/crm` 跳转后，后续步骤引用仍取到；⑥ 推进键「→」进下一步，输入框获焦时不触发；`pause: presenter` 的步停下等键，未标的连续跑；浮窗显示当前幕与讲解词，`alt+h` 一键隐藏／显示；快捷键自查不撞键（HT-017）；⑦ 演示进度记录的幕、步与页面实际所在一致（每步后读回） |
| **SL-013** `/crm` 驱动 | 需求 TS-014、DEC-034；HT-012 | ① s8dev 上第 1 幕线索转商机连续 10 次彩排，10 次都完成转换（界面或兜底），每次记走的是哪条路；② 单测：读回值不符时重填一次、再不符调 `convert_to_deal`（以 mock 的页面函数验分支）；③ 中文与英文会话下 `/crm` 页面源码都含运行器脚本，`frappe_china` 的译名注入仍在（中文会话）；`git -C frappe_china diff --stat` 无本任务改动 |
| **SL-014** 快照与换库 | 需求 TS-015、DEC-005／007／031～033、CR-011（DEC-022）；A4～A6，偏离 1／10／15 | ① 快进：从按键到目标幕起始页就绪 ≤10 秒，换库后首个请求的用户即 Administrator、不经登录页；第 5→6 与第 7→8 幕各连续 5 次，共 10 次全成功（计时表）；② 进度记录与换库后的幕一致；③ 换库函数对 `_o` 结尾的库名、不在登记表内的库名一律拒绝；非 Administrator 调用被拒；④ 本幕重来：回到幕首后，该幕关注的单据类型条数与原始快照一致（逐类型比对）；连续重来同一幕两次都干净（第二次等后台补完，记等待秒数）；⑤ 跳到未演过的幕 → 该幕主用库；跳回已演过的 → 干净那份；⑥ 「回到演示前」把 `db_name` 指回预跑前的工作库；「清理快照库」删掉全部快照库、登记表清空，且当前连接库不在被删之列（当前是快照库时拒绝并提示先回到演示前）；⑦ D 待验表 HT-015 已由 SA 填回 go（或按其结论处理） |
| **SL-015** 彩排与整场预跑 | 需求 TS-016、DEC-008、需求 §4.4.9 | ① s8dev 上从清洁工作库起，打开彩排页点开始后无人干预跑完：三段生成、九幕彩排、每幕首存三份库、最后停在第 1 幕主用库；登记表 27 个库全部「就绪」；② 人为在第 4 幕某步把字段名改错（临时配置）：彩排停下，页面与日志报「第 4 幕第 N 步：原因」，已存的快照不受影响；修好后能从第 4 幕重跑；③ 记录总耗时与分项（三段生成、九幕彩排、克隆），写 D 回执 |
| **SL-016** 九幕配置与客户说明 | 需求 TS-017／018、DEC-004／025、IM-004、需求 LG-009；偏离 14／16／17／19 | ① 九幕配置按需求 §4.2 清单逐幕跑通（彩排日志＋每幕结尾截图）；第 1 幕报价单在同一标签页打开、侧栏为业务流程；第 4 幕弹换 BOM 确认框并确认；第 6 幕计件取上月；第 7 幕结转 D2 上月、三张报表出数；第 8 幕策略对比三段；第 9 幕出经济订货量建议并采纳；② 讲解词全文 grep 无「今天」「今日」；所有 `say` 用最终译名（对照 `zh.csv` 抽 10 处）；③ 九幕全程只经业务流程侧栏、不用顶部搜索（配置里无 `awesomebar` 类动作，人工过一遍）；④ 九页客户说明 PDF：每页含幕名、现在的难处、系统怎么做、好处、一两张截图，中文无乱码 |
| **SL-017** 收尾 | 需求 TS-019 | ① `frappe_china` 与 `frappe_debug` 两套 Python 测试、Node 测试全量与 TS-001 基线比只增不减、全过；两 app `ruff check`／`format --check` 0 告警；`test_translation_quality` 过；两站 `translation_check.run` 通过；② 演示站：备份另存 `保留-S8上线前/`；装 `frappe_debug`、migrate、`check_app_order` 为真；`configure_apps` 两次（第二次无改动）；`Translation` 为 0；新清洁基准备份一份并在 S8 概况与项目概况记下其时间戳；③ 演示站整场预跑一次（同 SL-015 ①），记总耗时；④ 用户以现场模式含讲解完整演一遍，用时 20～30 分钟（用户口头确认＋记录起止时刻）；⑤ LG-001：一年数据结转后资产负债表是否出 `PH-P1039` 提示，截图记 D 回执；出现则按需求修或避开 |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-018 演示配置格式、校验与演示进度 | SL-012 | 否 |
| TS-019 desk 运行器：动作、场景日期、快捷键与浮窗 | SL-012 | 否 |
| TS-020 `/crm` 驱动与注入 | SL-013 | 否 |
| TS-021 快照与换库服务端（**开写前 HT-015 须由 SA 验掉**） | SL-014 | 否 |
| TS-022 换库前端：遮罩、中转页、重来与跳幕 | SL-014 | 否 |
| TS-023 彩排模式与整场预跑编排 | SL-015 | 否 |
| TS-024 九幕演示配置与命名函数 | SL-016 | 否 |
| TS-025 按幕客户说明 PDF | SL-016 | 否 |
| TS-026 收尾：回归、演示站部署、预跑验收、LG-001 | SL-017 | 否 |

---

## 任务 TS-018：演示配置格式、校验与演示进度（对应切片 SL-012 ①⑤⑦）

### 目标

配置写错在开播前就报（需求 §4.4.2）；进度存在每份快照库里（DEC-006）。

### 具体改动

1. **`frappe_debug/data/demo.yaml`**：需求 §4.4.2 的形态，顶层另加 `scene_date_fields`（单据类型 → 业务日期字段列表，A8 前端层用）与 `start_route`（演示起始页，业务流程侧栏页）。每幕键：`id`（`act1`…`act9`）、`title`、`date`（`D1`／`D2`／`E` 或 `D2-1`，偏离 19）、`snapshot: true`、`route`（幕起始路由）、`steps`。每步键：`action`（总纲 §5.3 `ACTIONS`）＋该动作的必填键（见 TS-019 表）＋可选 `say`、`pause`、`save_as`、`on_dialog`、`timeout`。
2. **`frappe_debug/demo/config.py`**：总纲 §5.3 的 `get_demo_config`／`validate_config`。日期引用支持 `D2-1` 形式（相对场景日期加减天数）。
3. **DocType `Demo Progress`**（Single，模块 Frappe Debug）：`act`（Int）、`step`（Int）、`refs`（JSON）、`scene_date`（Date）、`active`（Check）、`base_db`（Data，预跑前的工作库名，「回到演示前」用）。权限只给 System Manager；Administrator 读写。
4. **`demo/progress.py`**：`save_progress`、`get_progress`；`hooks.py` `extend_bootinfo = "frappe_debug.demo.progress.extend_bootinfo"` 把 `get_progress()` 放进 `bootinfo.frappe_debug_demo`（运行器页面加载即可读，不多一次请求）。**不用 `boot_session`**：`get_bootinfo` 的结果按用户缓存在 redis（`sessions.py:139-147`），进度每步都变，缓存里的会过期；`extend_bootinfo` 在读缓存之后、每次都跑（`sessions.py:169-170`）。

### 验证方式

`tests/test_demo_config.py`：SL-012 ① 五例（服务端那四类）；合法配置的 `dates` 与 Part2 `dates()` 一致。`test_progress.py`：写、读、boot 字段。

---

## 任务 TS-019：desk 运行器（对应切片 SL-012 ②～⑦）

### 目标

浏览器内按配置一步步驱动 desk（需求 §4.4.3～4.4.6），不模拟 DOM 点击（路线文档 §四 S8 第 10 条）。

### 具体改动

1. **`frappe_debug/public/js/demo/runner.js`**（`hooks.py` `app_include_js`，追加型，不占覆盖位；子 Agent 读 `frappe/desk/desk.py:38`）。只在 `frappe.boot.frappe_debug_demo.active` 或 `sessionStorage.frappe_debug_mode` 有值时启动，否则只注册「开始演示」入口（彩排页里）。
2. **动作实现**（每个返回 Promise，失败 reject 带原因）：

| 动作 | 必填键 | 做法 |
|---|---|---|
| `open_new` | `doctype` | `frappe.new_doc(doctype, values)` → 等 `cur_frm.doctype === doctype && cur_frm.is_new()` |
| `open_doc` | `doctype`、`name`（可 `${ref.x}`） | `frappe.set_route("Form", doctype, name)` → 等 `cur_frm.docname === name` |
| `open_list` | `doctype`，可选 `filters` | `frappe.route_options = filters; frappe.set_route("List", doctype)` → 等列表渲染（`cur_list?.doctype`） |
| `open_report` | `report`，可选 `filters` | `frappe.set_route("query-report", report)`，`frappe.query_report.set_filter_value(filters)` → 等 `frappe.query_report.data` 非空或「无结果」已显示 |
| `open_page` | `route` | `frappe.set_route(route)` |
| `set` | `field`、`value`；子表行另给 `table`、`row` | `cur_frm.set_value` 或 `frappe.model.set_value(cdt, cdn, …)`，await 后读回比对，不等即 reject |
| `add_row` | `table`、`values` | `cur_frm.add_child` ＋ 逐字段 `frappe.model.set_value`，`refresh_field` |
| `click` | `button`（按钮源词）、可选 `group` | 在 `cur_frm.page` 的内部按钮与菜单中按 `__()` 后的文字找，`.trigger("click")`；找不到 reject（列出现有按钮） |
| `save` / `submit` | 可选 `on_dialog` | `cur_frm.save()`／`cur_frm.save("Submit")`（后者不弹确认框，子 Agent 读 `form.js:803-818`）；并发监视 `cur_dialog`：`on_dialog` 给了按钮文字时点它；`confirm_dialog` 时点主按钮（`ui/keyboard.js:248-252` 同理）；保存后等 `!cur_frm.is_dirty()` 且 `docstatus` 符合 |
| `wait` | `until`（JS 表达式）或 `job` | 轮询，`timeout` 缺省 60 秒 |
| `highlight` | `field` 或 `selector` | 给元素加 `frappe-debug-highlight` 类（CSS 外框），下一步开始时移除 |
| `call` | `fn`、可选 `args` | `frappe_debug.demo.functions[fn](ctx, args)`，返回值 `save_as` |

   **步骤执行器**：`async run_step(act, i)`：展开模板 → 显示 `say` → 执行动作 → 有 `save_as` 存进 `refs` → `save_progress(act, i+1, refs)` → 彩排模式不停；现场模式且 `pause: presenter` 时等推进键。异常：彩排模式停下并上报（TS-023）；现场模式浮窗显红色「第 N 幕第 M 步：原因」，等演示者按重来或推进键（推进键重试本步）。
3. **场景日期前端层**（A8 ①）：`frappe.ui.form.on("*", "onload_post_render")`——不支持通配时，在 `runner.js` 里对 `scene_date_fields` 的每个 doctype 注册 `onload_post_render`：`frm.is_new()` 且运行器激活时，`set_posting_time` 字段存在则置 1，再把列出的日期字段设为 `scene_date`（交货日、计划日等「晚于业务日」的字段，配置里写成 `{field: delivery_date, offset_days: 14}`）。
4. **场景日期服务端层**（A8 ②），`frappe_debug/demo/scene_date.py`：

```python
def apply_scene_date(doc, method=None) -> None:
    """doc_events {"*": {"before_insert": …}}。frappe.flags.in_scenario_generator 或 in_test 时返回；
    演示进度 active 且有 scene_date 时：doc.doctype 在 SCENE_DATE_DOCTYPES 内（与 demo.yaml scene_date_fields 同表，
    由 config.py 读出并缓存）→ 其中等于 frappe.utils.today() 的字段改为 scene_date；有 set_posting_time 的置 1。"""
```

   `Demo Progress` 读取用 `frappe.db.get_single_value`（每次插入一次查询，演示时单据量小）。客户库不装 `frappe_debug`，此钩子不存在。
5. **快捷键**（HT-017）：`frappe.ui.keys.add_shortcut({shortcut: "right", action: next, description: "演示：下一步", ignore_inputs: true})`；`alt+r` 本幕重来、`alt+1`～`alt+9` 跳幕（TS-022 实现动作）、`alt+h` 浮窗显隐。注册前查 `frappe.ui.keys` 内部表是否已有同键，有则 `console.error` 并不启动。
6. **浮窗**：右下角固定定位的 `div`（不挡 desk 主按钮区，宽 360px），显示「第 N 幕 · 标题」、当前 `say`、下一步提示；样式 `public/css/demo.css`（`app_include_css`）。文字中文字面量（A10）。

### 验证方式

s8dev（单进程 6787）：一份测试配置 `data/demo_selftest.yaml` 覆盖十三个动作，彩排模式跑一遍（SL-012 ②，日志贴 D 回执）；③④ 查库；⑤ 刷新后续跑；⑥⑦ 现场模式手按一遍（录屏或截图）。CDP 脚本 `Spike/P1S8R6-D/runner-selftest.cjs`，写之前断言 `frappe.boot.sitename === "s8dev.localhost"`。`apply_scene_date` 单测（`test_scene_date.py`）。

---

## 任务 TS-020：`/crm` 驱动与注入（对应切片 SL-013）

### 目标

第 1 幕线索转商机在 `/crm` 弹窗里完成，失败由接口兜底（需求 §4.4.7、DEC-034），注入不改 `frappe_china`（需求 LG-005，HT-012）。

### 具体改动

1. **注入通道**：`frappe_debug/hooks.py` `update_website_context = "frappe_debug.demo.crm_inject.update_website_context"`：

```python
def update_website_context(context):
    """在 frappe_china 之后执行（装序，base_template_page.py:69-75）。
    context.template 是 "www/crm.html"（非中文会话）或 frappe_china 的包装模板（中文会话）时：
    context.frappe_debug_inner = 原 context.template；context.template = "frappe_debug/templates/crm_demo.html"。"""
```

   `templates/crm_demo.html`：`{% set inner %}{% include frappe_debug_inner %}{% endset %}{{ inner|replace('</body>', '<script src="/assets/frappe_debug/js/demo/crm_driver.js"></script></body>')|safe }}`。不认识的模板一律不动。
2. **`public/js/demo/crm_driver.js`**（`/crm` 页内，无 `frappe` 全局，csrf 在 `window.csrf_token`，V-06）：只在 `sessionStorage.frappe_debug_mode` 有值时动作。读 `sessionStorage.frappe_debug_pending`（desk 运行器跳来前写入的待执行步：线索名、预期价值、关闭日期、`save_as`），执行：
   1. 点「转换为商机」（按按钮文字找）；
   2. 按占位文字找到两个输入框，原生 setter ＋ `input`／`change`／`Enter`／`blur` 填值（V-06 做法）；
   3. **读回**两个输入框的显示值，不符重填一次，再不符 → 关弹窗，`fetch("/api/method/crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal", {headers: {"X-Frappe-CSRF-Token": window.csrf_token}, …})`；
   4. 弹窗路径点「转换」后等路由变为 `/crm/deals/<name>`；接口路径用返回的商机名经页面自身路由跳过去（V-06：`router.push`，取不到 router 时 `location.assign`）；
   5. 把商机名写回 `sessionStorage.frappe_debug_result`，并 `POST frappe_debug.demo.progress.save_progress` 记 `save_as`；
   6. 记走的是哪条路（`via: "ui" | "ui_retry" | "api"`）进结果，供 SL-013 ① 统计。
3. desk 运行器对第 1 幕这一步用命名函数 `crm_convert_lead`（TS-024）：写 pending → `location.assign("/crm/leads/<lead>")` → 回到 desk 后（下一步 `open_doc`）从 `sessionStorage` 取结果。页面跳转后运行器从演示进度续（SL-012 ⑤）。

### 验证方式

SL-013 ①：s8dev 上只彩排第 1 幕 10 次（每次前切回第 1 幕主用库，TS-021 后）；在 TS-021 之前做时，每次用新线索。② `crm_driver.js` 把三步拆成可注入页面函数，Node 测试（同 `frappe_china` 的 `.cjs` 测试风格）走三分支。③ 两种会话 `curl` 页面源码 grep。

---

## 任务 TS-021：快照与换库服务端（对应切片 SL-014 ③⑥⑦，及 ①②④⑤ 的服务端部分）

### 开写前

**HT-015（需求 LG-002）进 D 待验表**：命题「换库后 60 秒内，RQ worker 与 scheduler 的任务读写哪个库；不删 redis 目标库前缀键时是否读到旧缓存」，阻塞本任务。D 步写 `P1-S8-R6-D待验表.md`，报 `需要事实验证`，由新 Session 跑 SA；TS-018～TS-020 可先做。SA 填回 no-go 时按 DEC-031 失效条件暂停反馈用户。

### 目标

每幕三份库；快进、重来、跳幕都是换库（需求 §4.4.8、A4～A6）。

### 具体改动

1. **`frappe_debug/demo/dbops.py`**（只在本模块里调 shell 与 root）：

```python
def root_password() -> str:      # frappe.conf.root_password；无则 throw「站点配置缺 root_password」
def clone_cmd(src: str, dst: str) -> str:
    """mariadb -h {db_host} -uroot -p… -e 'CREATE DATABASE `dst`' &&
       mariadb-dump -h … --single-transaction --quick --routines src | mariadb -h … dst &&
       mariadb -h … -e "GRANT ALL PRIVILEGES ON `dst`.* TO '{db_user}'@'%'"（host 照 frappe db_manager.py:33-44 的取法）
    库名只允许 [A-Za-z0-9_]，否则 throw（防注入）；口令经环境变量 MYSQL_PWD 传，不出现在命令行。"""
def clone_sync(src, dst) -> float          # subprocess.run，返回秒数；失败 throw 带 stderr 末 20 行
def clone_detached(src, dst, marker: str)  # A6：Popen(["sh","-c", f"{clone_cmd} && touch {marker}.ok || touch {marker}.fail"], start_new_session=True)
def drop_db(name)                          # 名字须在登记表内、不等于当前 db_name
```

2. **登记表** `demo/registry.py`（A5）：`snapshots.json` 结构 `{"base_db": …, "acts": {"1": {"o": {"db", "state"}, "m": {...}, "b": {...}}, ...}}`，`state ∈ {"cloning", "ready", "used", "failed"}`；`refresh()` 读标记文件把 `cloning` 转为 `ready`／`failed`。全部读写包在 `filelock("frappe_debug_snapshots")`。
3. **`demo/snapshot.py`**：总纲 §5.3 `take_snapshot`（`frappe.db.commit()` → `clone_sync(当前库, _o)` → 两次 `clone_detached` → 登记）、`snapshot_status`、`drop_snapshots`；`replenish(act)`：该幕 `m`／`b` 中 `used` 的那份 `drop_db` 后从 `_o` 重新 `clone_detached`。
4. **`demo/switch.py`**：

```python
def _switch(db_name: str) -> None:
    """V-01② 做法：先在当前库读出本会话行（tabSessions 六列，DEC-033）；
    用站点用户连目标库（HT-016）delete 同 sid 再 insert；
    update_site_config("db_name", db_name); clear_site_config_cache();
    删 redis 中以 f"{db_name}|" 为前缀的键（redis_wrapper.py:62）。
    不 commit 当前库以外的东西；本请求随后不再读库（返回值只含常量与入参）。"""

def switch_to_act(act, purpose):
    """何时换库（需求 §4.4.8 表）：
    forward / jump 到未演过的幕 → acts[act].m（state ready）；
    restart / jump 到已演过的幕 → m、b 中 state==ready 的那份；都不是 ready → 返回 {"status": "waiting"}；
    选中的那份置 used，另一份若 used 则 replenish(act)。
    目标库内的 Demo Progress 已是该幕第 1 步（快照时写的），不另写。"""
```

   权限：三个换库方法 `frappe.only_for("System Manager")` 且 `frappe.session.user == "Administrator"`（需求 §4.4.8 末）。
5. **中转页依赖的接口**：`switch_status()` 允许 Guest 调用（中转页刚换库时会话可能未就绪），只返回 `{"db": frappe.conf.db_name}` 与 `frappe.session.user`，不返回其它信息。

### 验证方式

`tests/test_registry.py`：状态机与「何时换库」表（纯函数，不连库）；`test_dbops.py`：库名校验、命令不含口令；SL-014 ③⑥ 在 s8dev 上实跑（贴命令与结果）。

---

## 任务 TS-022：换库前端（对应切片 SL-014 ①②④⑤）

### 目标

按键后数秒落在目标幕，会话不掉（需求 §4.4.8 换库四步、DEC-033、RS-012）。

### 具体改动

1. **中转页** `frappe_debug/public/demo/transit.html`（`/assets/frappe_debug/demo/transit.html`，HT-018）：纯 HTML＋内联脚本，不引 frappe 资源；全屏「切换中」遮罩。从 URL 参数取 `act`、`purpose`、`csrf`，按 `sessionStorage` 里的 csrf 发 `POST /api/method/frappe_debug.demo.switch.switch_to_act`；`waiting` 时每 2 秒重试、遮罩显示「正在准备干净的数据，约 30～70 秒」；`switched` 后每 200 毫秒轮询 `switch_status` 直到 `db` 为目标且 `user` 为 Administrator（上限 20 秒），再 `location.replace(route)`。失败显示原因与「回到演示起始页」链接。
2. **运行器侧**：快进（某幕最后一步之后、下一幕 `date` 不同即视为快进；或演示者按 `→` 越过幕尾）、`alt+r`、`alt+数字`：先盖遮罩 → 把 csrf 写进 `sessionStorage` → `location.assign(transit.html?…)`（需求 §4.4.8 第 1 步：先离开 desk）。顺着往下演、下一幕 `date` 与本幕相同（第 1→5 幕、第 6→7、第 8→9）不换库（需求 §4.4.8 表第一行）。
3. **演示结束两步**：彩排页上两个按钮「回到演示前」（`switch_to_db(base_db)`，经中转页）与「清理快照库」（`drop_snapshots`，当前是快照库时提示先回到演示前）。

### 验证方式

s8dev：SL-014 ① 计时脚本 `Spike/P1S8R6-D/switch-timing.cjs`（照 V01b 写法，断言站点名；10 次）；②④⑤ 同脚本加断言；结果表贴 D 回执。**SL-012 ⑤ 的「换库后 `save_as` 仍可用」一项在本任务补测**（TS-019 时尚无换库）。

---

## 任务 TS-023：彩排模式与整场预跑编排（对应切片 SL-015）

### 目标

一个按钮从清洁库跑到九幕快照就绪，出错即停、报出幕与步（需求 §4.4.9、DEC-008）。

### 具体改动

1. **Page `demo-rehearsal`**（`frappe_debug/frappe_debug/page/demo_rehearsal/`，仅 System Manager）：显示场景日期、三段、九幕、登记表状态与进度日志；按钮「开始预跑」「从第 N 幕继续」「回到演示前」「清理快照库」。
2. **预跑编排**（前端，`public/js/demo/rehearsal.js`，`sessionStorage.frappe_debug_mode = "rehearsal"`）：

```
0. 记 base_db = 当前 db_name（save_progress 里的 base_db）；登记表清空（旧快照库先 drop）
1. 克隆 base_db → {base}_work，switch_to_db(_work)（经中转页）          # 需求 §4.4.9 第 1 步：不动清洁基准
2. start_generate(S, D1−1) → 轮询 generate_status 至 done
3. 第 1～5 幕：每幕首 take_snapshot(act) → 依次 run_step（彩排不停）
4. start_generate(D1+1, D2−1) → 轮询
5. 第 6、7 幕（同 3）
6. start_generate(D2+1, E−1) → 轮询
7. 第 8、9 幕（同 3）
8. 轮询 snapshot_status 至 27 个库全部 ready（failed 任一即停并报）
9. switch_to_act(1, "jump") → 置 sessionStorage 模式为 "live"、Demo Progress active=1
```

   步骤间跨换库与页面跳转，编排状态（当前在第几步）存 `sessionStorage.frappe_debug_rehearsal`，页面加载后续跑。
   任一步失败：日志与页面显示「第 N 幕第 M 步：原因」（或「生成第 k 段：失败日与 traceback 首行」），停下；「从第 N 幕继续」从该幕原始快照（已存）换库重来（SL-015 ②）。
3. **场景日期**：每幕开始前 `save_progress(act, 0, refs, scene_date=该幕日期)`。
4. **耗时记录**：每步起止写进页面日志，结束时汇总打印（SL-015 ③）。

### 验证方式

s8dev：SL-015 ①②③，贴页面日志全文（存 `Spike/P1S8R6-D/rehearsal-*.log`，定长副本）。

---

## 任务 TS-024：九幕演示配置与命名函数（对应切片 SL-016 ①～③）

### 目标

按需求 §4.2 清单写成九幕配置与讲解词（DEC-004、IM-004 讲解词部分）。

### 具体改动

1. **`data/demo.yaml`** 九幕。每幕的单据从哪来：

| 幕 | 场景日期 | 起始 | 要点（配置写法） |
|---|---|---|---|
| 1 接单 | D1 | 业务流程侧栏页 | `open_list` 线索 → `call: crm_convert_lead`（TS-020）→ `call: open_quotation_from_deal`（同标签页，偏离 14，带 `sidebar=Business Flow`）→ `set` 物料与数量 5000、税模板 `13% 专票 含税价` → `submit` → `click` 创建销售订单 → `submit`（客户自动建档、税模板沿用，SL-004）`save_as: so1` |
| 2 备料 ★ | D1 | 补货建议列表 | `call: run_daily_for_scene`（以场景日期调 `run_now`，弹窗看结果）→ `open_list` 建议单（过滤：来源订单 `${ref.so1}`）→ `open_doc` → `set` 建议量为整卷 → `click` 采纳 → `open_doc` 物料需求 → `click` 建采购订单 → `submit` `save_as: po1` |
| 3 采购到付款 | D1 | `${ref.po1}` | 连续跑：建采购入库 → 提交 → 建采购发票 → 提交 → 付款（`Wire Transfer`，自动带 `1002`）→ 提交 → `open_report` 库存与账面对比（停在「无差异」） |
| 4 生产 ★ | D1 | 生产计划新建 | `set` 公司 → `click` 取销售订单（过滤 `${ref.so1}`）→ `save` `on_dialog: 换用推荐`（SL-006）→ `highlight` 计划数量（5264 或按 BOM）→ `submit` → `click` 建工单 → 打开工单 → `submit` → `open_list` 工序卡（过滤该工单）→ 首道卡报工（命名函数 `report_job_card`：一次报完、损耗 n）→ 后道卡 `highlight` 数量已减 |
| 5 完工 | D1 | 工单 | 连续跑：余下工序卡报工 → 完工入库（费用科目自动带出）→ `submit` → `open_doc` 停在成本构成 |
| ⏩ | | | 第 5 幕尾按 `→` 即快进（下一幕 `date` 不同） |
| 6 看车间 | D2 | 负荷报表 | `open_report` 产能负荷（D2 起 6 周、按周）→ `highlight` 超 100% 那格 → `open_page` SPC 控制图 → `call: piece_rate_for_scene`（以 D2 前一天调 `make_for_period`，偏离 19，看三段弹窗） |
| 7 交付与结账 | D2 | 第 7 幕订单（生成器造的 `act7_order`，命名函数按交货日＝D2 查出，偏离 16） | 连续跑：发货 → 销售发票 → 收款 → 月末结转（D2 上月）→ 提交 → 现金流量底稿（D2 上月，取明细、提交；现金流量表要用）→ `open_report` 三张法定报表各一 |
| ⏩ | | | 同上 |
| 8 策略对比 ★ | E | 策略对比报表 | `open_report` 筛选三段（`${date.S}`…）→ `highlight` 图表 |
| 9 预警与选供应商 ★ | E | 补货建议列表 | `call: run_daily_for_scene`（E）→ `open_doc` 经济订货量建议（看依据子表）→ `open_list` 物料价格（过滤该线材、采购价、按 `valid_from` 降序）→ `open_list` 供应商评分 → 回到建议 → `click` 采纳 |

2. **命名函数** `public/js/demo/functions.js`：`crm_convert_lead`、`open_quotation_from_deal`、`run_daily_for_scene`、`piece_rate_for_scene`、`report_job_card`、`find_act7_order` 等，每个登记到 `frappe_debug.demo.functions`；服务端需要的查询放 `demo/functions.py`（whitelisted，仅 Administrator）。
3. **讲解词**：每步 `say` 一两句，用最终译名，不写「今天」「今日」，日期讲「这一天」「月初」（DEC-038）。
4. **约**：九幕各幕步骤数与讲解长度按需求 §4.2「约 N 分」配；用户在 TS-026 ④ 现场演时再调。

### 验证方式

SL-016 ①：s8dev 彩排全程日志＋每幕结尾截图（`Spike/P1S8R6-D/acts/`）；② `grep -n "今天\|今日" data/demo.yaml` 无输出；抽 10 处对照 `zh.csv`；③ 配置中无顶部搜索相关动作，人工过一遍记回执。

---

## 任务 TS-025：按幕客户说明 PDF（对应切片 SL-016 ④）

### 目标

会后给老板一份九页说明，与讲解词同源（需求 §4.15、DEC-025）。

### 具体改动

1. **内容源**：`data/demo.yaml` 每幕加 `brochure: {pain: …, how: …, benefit: …, images: [文件名]}`，与 `say` 同处维护（写一次）。
2. **生成**：`frappe_debug/demo/brochure.py` `build_brochure() -> bytes`：Jinja 模板 `templates/brochure.html`（每幕一页，`page-break-after`），图片从 `frappe_debug/data/brochure_images/` 以 data URI 内嵌，`frappe.utils.pdf.get_pdf`（HT-021）。whitelisted 下载方法照开发守则「带中文文件名的下载接口自建响应」写 `Content-Disposition`。
3. **截图**：彩排跑通后手动截（需求 §4.15），放 `data/brochure_images/`；PDF 另存一份到 `docs/01-需求摸底/S08-数据与操控/0-P1-S8文档/客户说明.pdf`。

### 验证方式

SL-016 ④：打开 PDF 逐页核四项与中文，截一页贴回执。

---

## 任务 TS-026：收尾（对应切片 SL-017）

### 目标

全量回归、上演示站、整场预跑验收、用户实演、LG-001（需求 TS-019）。

### 具体改动

1. **README**：`frappe_debug/README.md` 写模块边界（A1）、两份数据文件、预跑与现场操作步骤（需求 §七）、约束（单进程 `bench serve`、scheduler 关、预跑后不改代码、客户库不从演示站来）、`root_password` 的设法；`frappe_china/README.md` 已在各任务追加的登记逐条核一遍。
2. **全量回归**（SL-017 ①）：两 app Python、Node、ruff、译名三件套；与 TS-001 基线比，写进 D 回执。
3. **演示站部署**（SL-017 ②）：
   1. 核演示站现状（清洁基准、GL 0 条、`Translation` 0）；
   2. `docker/backup.sh`，另存 `docker/backups/保留-S8上线前/`；
   3. `frappe_debug` 装上（`apps.txt`、`install-app`、`reorder_installed_apps`、`check_app_order`）、`bench --site erx.localhost migrate`；
   4. `docker/configure-apps.sh --site erx.localhost` 两次；
   5. `bench build --app frappe_china --app frappe_debug`，重启 `bench start`；
   6. `bench --site erx.localhost set-config root_password …`（不进 git）；
   7. 复核：`check_app_order`、两站 `translation_check.run`、业务数据计数、`Translation` 为 0；
   8. 备份一份作**新清洁基准**，时间戳记入 S8 概况与项目概况「演示站当前状态」（后者按常驻文件契约写，由 Workflow 收尾步骤做，本任务只在回执给出候选）。
4. **整场预跑**（SL-017 ③）：演示站上按 TS-023 跑一次，记耗时。8000 端口的 web 为单进程 `bench serve`（需求 §4.4.8 约束 2，现 Procfile 即是）；scheduler 关。
5. **用户实演**（SL-017 ④）：停下来请用户现场模式含讲解演一遍，记起止时刻与用户意见；讲解词的调整在本任务内改配置后**须重新预跑**（需求 RS-006）。
6. **LG-001**（SL-017 ⑤）：第 7 幕快照库（D2 上月已结）与第 8 幕快照库各开一次小企业资产负债表，看有无 `PH-P1039` 提示，截图；出现则按需求 §4.16 修或避开，修法进 `SH-P1S8005`。
7. **常驻文件候选**：D 回执「新增约定」中确属长效的（总纲纪律 11 列的三条及执行中新增的），列为候选，由 Workflow 收尾按常驻文件契约移交 `开发守则.md`；S8 长效信息 #2（客户正式库从空站新建）在本任务写进 `开发守则.md`（S8 概况长效信息表指定 D 步建 `frappe_debug` 时写）——写前载入常驻文件契约。

### 验证方式

SL-017 ①～⑤ 逐项证据贴 D 回执（命令与输出、截图路径、计时表、用户确认的原话）。
