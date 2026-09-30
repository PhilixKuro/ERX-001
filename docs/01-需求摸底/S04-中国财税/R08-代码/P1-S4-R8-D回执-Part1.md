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
| TS-006 Company 钩子与建账编排 | SL-003 | — | ⬜未开始 | — | — |
| TS-007 建账结果自检函数 | SL-003 | — | ⬜未开始 | — | — |
| TS-008 税类别、税模板、税规则；端到端测试 | SL-004 | — | ⬜未开始 | — | — |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-001 | 两站 `list-apps`；读回测试站设置与会计年度；核 `default_site` 与演示站基线 | `bench --site {test,erx}.localhost list-apps`＋只读站点探针＋读取 `common_site_config.json` | ✅ test 仅 frappe/erpnext；China／zh／Asia/Shanghai／yyyy-mm-dd／CNY／Commercial Rounding；FY 2025–2027；默认站仍 erx；演示站 Company 1（华东弹簧）／GL 22／SLE 12／Account 95 |
| TS-002 | `fc-list`；中文 PDF 文字与嵌入字体；字体安装失败降级 | 当前容器安装字体；`get_pdf` 生成中文 PDF；`pdftotext`／`pdffonts` 核对；一次性无效 apt 代理实跑失败分支；`bash -n` | ✅ 五组 Noto Sans CJK 字体可见；文本含“资产负债表”；字体 `NotoSansCJKsc-Regular`、`emb=yes`；离线分支输出告警且最终退出码 0；shell 语法通过 |
| TS-003 | `run-tests`；四个中文名报表；空侧栏；设置前后不变；演示站基线 | 先跑 `test_smoke`／`test_scaffold`，再跑 `run-tests --app frappe_china`；前后读取测试站设置；只读探针核演示站 | ✅ smoke 3/3、scaffold 2/2、完整 app 5/5；四报表均返回 `[{"status": "ok"}]`；`CN Tax` 空侧栏已注册且 boot 结果无 `cn tax`；测试前后均为 `Asia/Shanghai`／`zh`；演示站仍 Company 1（华东弹簧）／GL 22／SLE 12／Account 95，且只装 frappe／erpnext |
| TS-004 | `test_install.py`；强制重装前后 UOM 与 System Settings 对比 | `test_install.py` 红绿测试；预建并停用“支”后连续两次 `install-app --force`；全量快照逐项比较 | ✅ 3/3 安装测试通过；UOM 240→284 后第二次仍为 284；45 项全部存在，其中预存“支”仍停用、其余 44 项启用；既有 UOM 改动 0；System Settings 前后 sha256 同为 `dad37541…7c3d`；8 类 `rounded_total.hidden=1`；`disable_in_words=0` |
| TS-005 | `test_chart.py`；三个覆盖解析；中美两国返回值；266 节点 | `frappe.override_whitelisted_method`＋直接调用本模块函数；递归计数；源/目标文件哈希 | ✅ 6/6；三条原路径均解析到本 app；China 返回本科目表＋两个 Standard，US 与原生逐项一致；266 节点、6 根节点；不存在模板返回 `None`；源/目标 SHA-256 均为 `539D12F5…867972` |
| TS-006 | `test_company.py`；建账逐节点比对；双顺序连续建公司；异常路径 | — | ⬜未运行 |
| TS-007 | `test_selfcheck.py`；正常与四类异常输入均不抛异常 | — | ⬜未运行 |
| TS-008 | `test_taxes.py`、`test_e2e_minimal.py`；界面证据；演示站基线 | — | ⬜未运行 |

## 技术假设验证

| 假设 | 依赖任务 | 状态 | 实测结果 |
|---|---|---|---|
| HT-001 中文名 Script Report 可导入并执行 | TS-003 | ✅成立 | 四个中文名 Report 均由 `frappe.desk.query_report.run` 返回一行 `status=ok` |
| HT-002 上游 `create_charts(custom_chart=...)` 与目标科目树一致 | TS-006 | ⬜待验证 | — |
| HT-003 Noto CJK 可生成中文可读且嵌字的 PDF | TS-002 | ✅成立 | `pdftotext` 取得“资产负债表”；`pdffonts` 显示 `NotoSansCJKsc-Regular` 且 `emb=yes` |
| HT-005 无公司站点可保存 Global Defaults 并生成 Property Setter | TS-004 | ✅成立 | 测试站 Company=0；强制重装后 `disable_rounded_total=1`，8 类单据的 `rounded_total.hidden` Property Setter 均为 1 |
| HT-006 空的同名 Workspace Sidebar 可压住自动侧栏 | TS-003 | ✅成立 | `Workspace Sidebar/CN Tax` 已注册、`items=[]`，`get_sidebar_items()` 结果不含 `cn tax` |
| HT-008 Company 生命周期顺序符合建账钩子需要 | TS-006 | ⬜待验证 | — |
| HT-009 税模板正常 `insert()` 可通过校验 | TS-008 | ⬜待验证 | — |
| HT-013 测试回滚且不导入 `erpnext.tests.utils` 时站点设置不变 | TS-003 | ✅成立 | 完整 app 测试前后 `System Settings.time_zone=Asia/Shanghai`、`language=zh` 均未变化 |
| HT-014 `after_rollback` 回调可复位建账标志 | TS-006 | ⬜待验证 | — |

## 全量验证

| 门 | 结果 |
|---|---|
| Part1 定向测试 | ⬜未运行 |
| `bench --site test.localhost run-tests --app frappe_china` | ✅当前 14 个测试全部通过；Part1 后续任务增加测试后再全量重跑 |
| 格式与静态检查 | ⬜未运行 |
| 演示站基线 | ✅当前核对通过：Company 1（华东弹簧）／GL 22／SLE 12／Account 95，仅 frappe／erpnext |

## 偏离与暂停

- **已恢复**：TS-001 开工前 Docker 自动审批审查服务曾连续返回 `503 Service Unavailable`；2026-09-30 审批链恢复后按用户授权正常执行。故障期间未绕过审批、未改站点。
- **TS-003 安装顺序恢复**：初次安装发生在 `modules.txt` 从生成器默认模块改成 `CN Tax` 之前；`bench migrate` 不会补建后来新增的 `Module Def`。测试站执行一次 `install-app frappe_china --force` 后官方安装链补齐模块与侧栏元数据；演示站未执行该命令。
- **格式检查工具缺失**：app 的 `pyproject.toml` 声明 ruff 规则，但当前 bench 环境没有 `ruff` 可执行文件或 Python 模块；未擅自安装依赖。Python 文件均已由实际测试导入执行，最终格式门留到 Part1 全量验证再按可用工具处理。

## 新增约定

| 约定 | 类别（命名/位置/错误处理/依赖/跨层调用） | 在哪个任务确立 |
|---|---|---|

## 未做项

| 项 | 为什么没做 |
|---|---|

## 状态值

- **进行中**——TS-001～005 已完成，首个未完成任务为 TS-006。

## 复核建议

待 Part1 完成时填写。
