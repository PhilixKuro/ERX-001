# D回执（对象：代码 / 依据：P1-S4-R7-C开发方案-Part1）

**轮次**：P1-S4-R8｜**日期**：2026-09-29｜**步骤**：`plannedDev` D（build）
**依据**：[开发方案总纲](../R07-开发方案/P1-S4-R7-C开发方案-总纲.md)＋[Part1](../R07-开发方案/P1-S4-R7-C开发方案-Part1.md)
**执行纪律**：按任务顺序、测试先行；技术假设先验证再写依赖代码；本回执逐任务实时更新。

## 逐项执行结果

| 任务 | 对应切片 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-001 建测试站点 | SL-001 | `frappe-bench/sites/test.localhost/site_config.json:1` | ✅完成 | 2026-09-30 | 新建独立站点并安装 frappe／erpnext；补 v16 bare 初始化、中文环境、开发与测试开关、Commercial Rounding、2025–2027 自然年会计年度；未改默认站点 |
| TS-002 开发容器装中文字体 | SL-001 | `docker/scripts/setup.sh:243`；`docker/README.md:199` | ✅完成 | 2026-09-30 | 持久化安装 Noto CJK 与 poppler-utils；当前容器已安装；离线时只告警并继续 |
| TS-003 app 骨架与测试脚手架 | SL-001 | `frappe-bench/apps/frappe_china/frappe_china/modules.txt:1`；`frappe_china/tests/test_scaffold.py:8`；`frappe_china/workspace_sidebar/cn_tax.json:2` | ✅完成 | 2026-09-30 | app 仅装入测试站；四个中文 Script Report 桩、空侧栏、测试基类与编辑器/导航入口已落地；完整 app 测试 5/5 通过 |
| TS-004 安装期设置 | SL-002 | `frappe_china/accounting/install.py:7`；`frappe_china/install.py:1`；`frappe_china/tests/test_install.py:28` | ✅完成 | 2026-09-30 | 45 项中文 UOM 原序落地；只新增缺失项；凑整开关经 Global Defaults 保存触发 8 类单据 Property Setter；连续安装幂等且不改 System Settings |
| TS-005 科目表数据与三个覆盖 | SL-003 | `frappe_china/accounting/chart.py:17`；`frappe_china/hooks.py:192`；`frappe_china/tests/test_chart.py:34` | ✅完成 | 2026-09-30 | zelin 小企业科目表逐字节并入；三个 HTTP 方法覆盖与原生回退落地；China/US 分支、266 节点、6 根节点均由测试守住 |
| TS-006 Company 钩子与建账编排 | SL-003 | `frappe_china/accounting/company.py:1`；`frappe_china/cn_tax/data/company_defaults.json:1`；`frappe_china/tests/test_company.py:1` | ✅完成 | 2026-09-30 | 6/6 集成测试通过；Existing Company 验收按 `DEC-120` 保留原生额外 `VAT` |
| TS-007 建账结果自检函数 | SL-003 | `frappe_china/accounting/selfcheck.py:1`；`frappe_china/tests/test_selfcheck.py:1` | ✅完成 | 2026-09-30 | 6/6 自检测试通过；正常、非目标公司、缺科目、额外科目和内部异常均符合方案 |
| TS-008 税类别、税模板、税规则；端到端测试 | SL-004 | `frappe_china/accounting/taxes.py:17`；`frappe_china/cn_tax/data/tax_setup.json:1`；`frappe_china/tests/test_taxes.py:27`；`frappe_china/tests/test_e2e_minimal.py:8` | ✅完成 | 2026-09-30 | 9 个税类别、12 个模板、13 条规则与建公司自动编排落地；3/3 税设置测试、1/1 端到端测试通过；真实 Company 界面与 HTTP 科目树证据已截图 |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-001 | 两站 `list-apps`；读回测试站设置与会计年度；核 `default_site` 与演示站基线 | `bench --site {test,erx}.localhost list-apps`＋只读站点探针＋读取 `common_site_config.json` | ✅ test 仅 frappe/erpnext；China／zh／Asia/Shanghai／yyyy-mm-dd／CNY／Commercial Rounding；FY 2025–2027；默认站仍 erx；演示站 Company 1（华东弹簧）／GL 22／SLE 12／Account 95 |
| TS-002 | `fc-list`；中文 PDF 文字与嵌入字体；字体安装失败降级 | 当前容器安装字体；`get_pdf` 生成中文 PDF；`pdftotext`／`pdffonts` 核对；一次性无效 apt 代理实跑失败分支；`bash -n` | ✅ 五组 Noto Sans CJK 字体可见；文本含“资产负债表”；字体 `NotoSansCJKsc-Regular`、`emb=yes`；离线分支输出告警且最终退出码 0；shell 语法通过 |
| TS-003 | `run-tests`；四个中文名报表；空侧栏；设置前后不变；演示站基线 | 先跑 `test_smoke`／`test_scaffold`，再跑 `run-tests --app frappe_china`；前后读取测试站设置；只读探针核演示站 | ✅ smoke 3/3、scaffold 2/2、完整 app 5/5；四报表均返回 `[{"status": "ok"}]`；`CN Tax` 空侧栏已注册且 boot 结果无 `cn tax`；测试前后均为 `Asia/Shanghai`／`zh`；演示站仍 Company 1（华东弹簧）／GL 22／SLE 12／Account 95，且只装 frappe／erpnext |
| TS-004 | `test_install.py`；强制重装前后 UOM 与 System Settings 对比 | `test_install.py` 红绿测试；预建并停用“支”后连续两次 `install-app --force`；全量快照逐项比较 | ✅ 3/3 安装测试通过；UOM 240→284 后第二次仍为 284；45 项全部存在，其中预存“支”仍停用、其余 44 项启用；既有 UOM 改动 0；System Settings 前后 sha256 同为 `dad37541…7c3d`；8 类 `rounded_total.hidden=1`；`disable_in_words=0` |
| TS-005 | `test_chart.py`；三个覆盖解析；中美两国返回值；266 节点 | `frappe.override_whitelisted_method`＋直接调用本模块函数；递归计数；源/目标文件哈希 | ✅ 6/6；三条原路径均解析到本 app；China 返回本科目表＋两个 Standard，US 与原生逐项一致；266 节点、6 根节点；不存在模板返回 `None`；源/目标 SHA-256 均为 `539D12F5…867972` |
| TS-006 | `test_company.py`；建账逐节点比对；双顺序连续建公司；异常路径 | 先红测确认模块缺失；实现后跑 6 个集成测试；另在同一测试站事务内实跑源公司→Existing Company 复制差异探针并回滚 | ✅6/6；266 节点逐字段一致、22 个默认科目、仓库／物料组／现金付款方式、两个建公司顺序、残留标志、建账异常回滚、非中国拒绝均通过；Existing Company 源科目全集一致且只多原生 `('', 'VAT')`（`DEC-120`） |
| TS-007 | `test_selfcheck.py`；正常与四类异常输入均不抛异常 | 红测确认模块缺失；实现后跑 6 个集成测试 | ✅6/6；正常中国公司 `checked=True/ok=True`、Standard 公司 `checked=False/ok=True`、缺科目/默认值判失败、额外科目只报告、内部异常与批量查询异常均返回 warning 不抛出 |
| TS-008 | `test_taxes.py`、`test_e2e_minimal.py`；界面证据；演示站基线 | 红测后实现并分别运行两组定向测试；在真实 `test.localhost` Company 新建表单设置 China／Standard Template，由浏览器读取实际下拉并经 HTTP 白名单入口取科目树；全量 app 测试后只读复核演示站 | ✅ `test_taxes.py` 3/3、`test_e2e_minimal.py` 1/1；9 个税类别、5 个销项模板、7 个进项模板、13 条规则；12 个税行严格命中 `2221005`／`2221001`，Standard 缺科目明确失败且不增科目，重跑幂等；P9 进项规则命中；13% 含税销售 113→净额 100／税 13、13% 未税销售 100→税 13／合计 113、9% 含税采购 109→净额 100／税 9，GL 借贷科目与金额相符；退货税额 `-0.065→-0.07`，无凑整分录；界面下拉含本科目表与两个 Standard，HTTP 返回 6 根节点。截图：[P1-S4-R8-TS008-ui-evidence.png](../../../../Spike/P1-S4-R8-TS008-ui-evidence.png)；演示站仍 Company 1（华东弹簧）／GL 22／SLE 12／Account 95，仅 frappe／erpnext |

## 技术假设验证

| 假设 | 依赖任务 | 状态 | 实测结果 |
|---|---|---|---|
| HT-001 中文名 Script Report 可导入并执行 | TS-003 | ✅成立 | 四个中文名 Report 均由 `frappe.desk.query_report.run` 返回一行 `status=ok` |
| HT-002 上游 `create_charts(custom_chart=...)` 与目标科目树一致 | TS-006 | ✅成立 | 中国公司实建 266 条；逐节点比对（科目号、科目名、上级科目号、`is_group`、`root_type`、`account_type`）完全一致 |
| HT-003 Noto CJK 可生成中文可读且嵌字的 PDF | TS-002 | ✅成立 | `pdftotext` 取得“资产负债表”；`pdffonts` 显示 `NotoSansCJKsc-Regular` 且 `emb=yes` |
| HT-005 无公司站点可保存 Global Defaults 并生成 Property Setter | TS-004 | ✅成立 | 测试站 Company=0；强制重装后 `disable_rounded_total=1`，8 类单据的 `rounded_total.hidden` Property Setter 均为 1 |
| HT-006 空的同名 Workspace Sidebar 可压住自动侧栏 | TS-003 | ✅成立 | `Workspace Sidebar/CN Tax` 已注册、`items=[]`，`get_sidebar_items()` 结果不含 `cn tax` |
| HT-008 Company 生命周期顺序符合建账钩子需要 | TS-006 | ✅成立 | app `on_update` 入口实测已有成本中心、科目数为 0；随后自有建账成功 |
| HT-009 税模板正常 `insert()` 可通过校验 | TS-008 | ✅成立 | 12 个模板均由正常 `insert()` 创建，未置 `ignore_validate`／`ignore_links`；`test_taxes.py` 与端到端建公司均通过 |
| HT-013 测试回滚且不导入 `erpnext.tests.utils` 时站点设置不变 | TS-003 | ✅成立 | 完整 app 测试前后 `System Settings.time_zone=Asia/Shanghai`、`language=zh` 均未变化 |
| HT-014 `after_rollback` 回调可复位建账标志 | TS-006 | ✅成立 | mock `create_charts` 抛错后显式 rollback，`ignore_chart_of_accounts=False`；随后同进程建 Standard 公司成功 |

## 全量验证

| 门 | 结果 |
|---|---|
| Part1 定向测试 | ✅TS-008：`test_taxes.py` 3/3、`test_e2e_minimal.py` 1/1；此前 TS-001～007 各定向测试亦全部通过 |
| `bench --site test.localhost run-tests --app frappe_china` | ✅30/30 全部通过（约 54.5 秒） |
| 格式与静态检查 | ✅主仓与 app 仓 `git diff --check` 均通过；ruff 在当前 bench 环境仍未安装，Python 文件已由 30 个测试实际导入执行 |
| 演示站基线 | ✅Part1 收尾复核通过：Company 1（华东弹簧）／GL 22／SLE 12／Account 95，仅 frappe／erpnext |

## 偏离与暂停

- **已恢复**：TS-001 开工前 Docker 自动审批审查服务曾连续返回 `503 Service Unavailable`；2026-09-30 审批链恢复后按用户授权正常执行。故障期间未绕过审批、未改站点。
- **TS-003 安装顺序恢复**：初次安装发生在 `modules.txt` 从生成器默认模块改成 `CN Tax` 之前；`bench migrate` 不会补建后来新增的 `Module Def`。测试站执行一次 `install-app frappe_china --force` 后官方安装链补齐模块与侧栏元数据；演示站未执行该命令。
- **格式检查工具缺失**：app 的 `pyproject.toml` 声明 ruff 规则，但当前 bench 环境没有 `ruff` 可执行文件或 Python 模块；未擅自安装依赖。Python 文件均已由实际测试导入执行，最终格式门留到 Part1 全量验证再按可用工具处理。
- **TS-006 已裁决**：Part1 原要求 `Existing Company`「走原生路径，科目与源公司一致」，实测原生路径会额外新增无编号 `VAT`。用户采用推荐项（`DEC-120`）：保留原生路径，验收改为源科目全集一致且只允许额外 `VAT`；讨论见 [D讨论记录](P1-S4-R8-D讨论记录.md)。
- **TS-008 界面证据的站点路由**：项目 `serve_default_site=true` 会让常规 `bench serve` 固定服务演示站。截图时临时以 `bench --site test.localhost serve --port 8000` 锁定测试站，取证后已恢复原 `bench serve --port 8000`；演示站数据与安装 app 基线复核无变化。

## 新增约定

| 约定 | 类别（命名/位置/错误处理/依赖/跨层调用） | 在哪个任务确立 |
|---|---|---|

## 未做项

| 项 | 为什么没做 |
|---|---|

## 状态值

- **Part1 已完成（D 步进行中）**——TS-001～008 全部完成；下一续跑点为 Part2 的 TS-009。

## 复核建议

1. 优先抽查 [TS-008 界面证据](../../../../Spike/P1-S4-R8-TS008-ui-evidence.png)：确认 Company 实际下拉三项及 HTTP 返回的六个根节点均清晰可辨。
2. 抽查 `frappe_china/accounting/taxes.py` 对税科目号的严格解析与幂等分支；这里决定是否会误挂科目或静默新建科目。
3. 抽查 `test_e2e_minimal.py` 的三张单据与退货边界断言；这是 Part1 中覆盖面最广、最接近真实业务链的一组证据。
4. `DEC-120` 是 Part1 唯一经用户裁决的验收口径变更，复核 Existing Company 时应以讨论记录中的新口径为准。

> **R11 更正**：本回执有被 E 步（IT-028）指出的缺项与不符之处，更正统一记在 [Part4 回执末尾的「更正段」](P1-S4-R8-D回执-Part4.md#更正段p1-s4-r11-追加对应-e-确认报告-it-028)。上文原样保留。
