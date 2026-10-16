# P1-S7-R5 D回执·Part3

**日期**：2026-10-16｜**执行者**：Codex｜**打tag**：否
**依据**：R04 开发方案总纲及 Part3；Spec：`D-code-plannedDev-build.md`。
**续跑裁决**：用户暂跳 TS-012，允许继续 TS-013～017；TS-012 未完成，不据此宣称 D 全部落地。

## 逐项执行结果

| 任务 | 对应切片 | 落地位置 | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-014 产能负荷报表 | SL-010 | `production_plus/report/capacity_load/`、`tests/test_capacity_load.py`／`.cjs` | ✅完成 | 2026-10-16 | Python 2/2、Node 1/1；已纳入最终全量 |
| TS-015 SPC 计算与报表 | SL-011 | `production/spc.py`、`production_plus/report/spc_control_chart/`、`tests/test_spc.py`、`tests/spc_data.py` | ✅完成 | 2026-10-16 | 数学 3/3、真实站点取数 1/1；已纳入最终全量 |
| TS-016 控制图页面 | SL-011 | `production_plus/page/spc_chart/`、`public/js/vendor/`、`tests/test_spc_chart.cjs` | ✅完成 | 2026-10-16 | 28 子组、两种颜色、规则 1／2、报表带筛选跳转与 tooltip 已取证 |
| TS-017 收尾、全量回归与演示站落地 | SL-012 | README；`Spike/P1S7R5-D/ts017-*` | ✅完成（保留 TS-012 缺口） | 2026-10-16 | Python 342/342、Node 89/89；365 天回放完成并回滚；演示站已迁移、配置、构建、重启和取证。首次迁移漏模块／新增日志及修正如实记录，不声称 D 全部通过。 |

## 全量验证

历史基线 TS-001 为 Python 283、Node 86；TS-012 前基线为 Python 328、Node 87。最终 Python **342/342**：334 integration（1954.625s）＋5 old category（0.268s）＋3 math unspecified（0.006s），均 OK、退出 0。日志 `frappe-bench/logs/s7-r5-ts017-full.log`。按类名＋用例名与 TS-001 283 项、Part2 328 项逐项比对，缺失均 0，分别新增 59／14；证据 `Spike/P1S7R5-D/ts017-baseline-comparison.json`。

Node **89/89**（基线86，Part2 为87），日志 `frappe-bench/logs/s7-r5-part3-node.log`。全量内译名质量 **13/13**、翻译 **20/20** 均通过；测试站 `translation_check.run` 通过。最终 Ruff check 通过、format --check **160 文件**通过；根与 app diff --check 通过。全量包含 TS-012 的 4 条原生事实断言，测试通过不等于该切片联合验收通过。

## 方案要求的验证

| 任务 | 验证方式 | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-014 | SL-010 ①～⑦，Python execute 与 Node formatter | 测试站真实工作中心、时段、假日及任务单；Node 直接调用 formatter | Python 2/2（4.081s），需求 14h、产能 64h、负荷 21.875%；未排期 1h；无产能、零数量、完成／取消排除及日周月边界通过。日志 `s7-r5-ts014-green.log`；Node 1/1。 |
| TS-015 | SL-011 ①～⑤，compute／Nelson／真实检验单 | 28 组常量手算；8 规则各命中／临界不命中；测试站真实已提交 Quality Inspection，存储读数含 abc／空值 | 数学 3/3（0.006s）、站点 1/1（6.121s），日志 `s7-r5-ts015-green.log`。X̿=10、R̄=3、σ组内=1.450512682、σ总体=1.218898800、Cpk=1.149019024、Ppk=1.367354424，106 读数；剔除 1；单读数组只进总体；限值及报表／接口一致性通过。 |
| TS-016 | 判异点与 tooltip 截图、接口与报表一致性 | 专用 `test.localhost:6787` 服务，报表点击「打开控制图」；CDP 检查 ECharts 实例和每点配置 | 版本 5.6.0、28 点，正常蓝 `#0289f7`、判异红 `#e03636`，规则 1／2；`Spike/P1S7R5-D/ts016-ui-result.json`、`ts015-spc-report.png`、`ts016-spc-overall.png`、`ts016-spc-signal-tooltip.png`。临时检验单／物料／参数／入库草稿均按普通删除清理，未忽略链接。 |
| TS-017 | SL-012 ①～⑤，全量／365 天回放／演示站 | `ts017-full-check.sh`、`ts017-replay.py`、演示站前后快照与备份 | README 齐备；Python 342/342、Node 89/89、两站译名自检通过；演示站业务计数 0。365 日计算总计 **118.678602s**、单日最大 **0.501814s**，未达 10s 输入阈值。30 物料／60 仓库行／三规则全勾、60 初始入库＋365 逐日出库＝425 SLE；回滚后物料0、台账与公司设置恢复，无新增计算错误。结果 `ts017-replay-result.json`，日志 `s7-r5-ts017-replay.log`。 |

## 演示站落地证据

- 备份：`docker/backup.sh` 成功，`20261016_162704` 的 database／files／private-files／site-config 四件套已另存 `docker/backups/保留-S7上线前/`；该备份包含尚未清理的 TS-010 残留，恢复后须再次按确切测试记录清理。
- 首次 migrate 退出 0，但因模块映射旧缓存只扫描 CN Tax，新 DocType／Page 未注册；清缓存后第二次完整 migrate 正确注册 5 个新 DocType、两个报表及页面。日志 `s7-r5-ts017-demo-migrate.log`、`s7-r5-ts017-demo-remigrate.log`。第二份日志曾因误启动重叠 migrate 被截断并产生零字节空洞，保留现状；重叠调用被迁移锁拒绝，未执行第二份迁移。
- `docker/configure-apps.sh --site erx.localhost` 连续两次均输出「无改动」（LiteLLM 仍按既有延期跳过）；第二次输出 `s7-r5-ts017-configure-second.log`。`bench build --app frappe_china` 退出 0；停止原 honcho 后重起 `bench start`，日志仍为 `frappe-bench/logs/bench-start.log`。
- 两站译名自检均通过；演示站装序 `check_app_order()["ok"]=true`、`auto_indent=0`、计件工资组件存在、Stock Plus／Production Plus 侧栏均 0 项。演示站仅华东弹簧有限公司、266 科目；GL／SLE／客户／供应商／物料／所有列出的业务单据／Translation 均 0。最终快照 `Spike/P1S7R5-D/s7-erx.localhost-after.json`。
- 页面：`ts017-demo-ui-result.json`、`ts017-demo-work-order.png`、`ts017-demo-spc-empty.png`；工单为 `__islocal=true`，不保存；空控制图提示「请选择物料和检验参数」，ECharts 5.6.0 资源实际 HTTP 200。
- ECharts 与许可证均与 Insights 包字节一致：JS SHA256 `bf4a223524e40b77c304bec67e1222cf551f14880cf42c69dc046558e11c07b1`，LICENSE `634293835b43a6dd2094fa39182a3d9a6b9ca43b7fdb9ac354e8037af2a3093a`。
- 首次迁移将 45 条历史浏览器失败从 deferred queue 刷入 Error Log（集中创建于 16:29:36～37）；本次页面未注册探针再产生 1 条，误启动重叠迁移被锁拒绝产生 1 条。来源与 trace 哈希清单保存 `ts017-deferred-errors.json`，只按这 47 个确切身份及哈希清理，未删除原有错误日志；最终与首次快照比对新错误为 0。不把首次迁移发生过错误的事实改写为「从未新增」。

## 偏离与暂停

- 用户允许暂跳 TS-012，未改变该项验收结论；保留其生产代码与原生失败事实。
- TS-013、TS-015 数学与两项 Node 测试有缺模块／缺文件的红态；TS-014 Python 红态在迁移期间中止，TS-015 站点集成断言在实现后补入，不能声称全部严格先红后绿。切片完成时未逐一重跑全量，本次 TS-017 补跑覆盖当前代码；保留此流程偏离。
- 取证首次使用 8000 端口，站点断言发现实际为演示站即中止；没有执行造数或页面业务操作。改为 6787 专用测试站。首版 28 点全判异，不满足两色取证，已修测试数据并重拍。
- 翻译守卫排除原样 vendor JS，只扫描 app 自有源词；否则 minified ECharts 内部 `__` 片段被误当源词。CSV 初次按大小写排序导致排序测试失败，已改用守卫相同的 casefold 排序，最终全量 20/20 通过。
- 演示站基线存在早前 TS-010 取证残留 `_FCT_TS010_UI_1792088513074` 及其两个批次（无 SLE）。备份 `20261016_162704` 已完整另存 `docker/backups/保留-S7上线前/`，再用正常链接检查删除上述确切测试记录；未宽泛删除数据。原基线见 `s7-erx.localhost-before.json`，清理日志 `s7-r5-ts017-demo-clean.log`。
- 回放探针保留在 `Spike/P1S7R5-D/ts017-replay.py` 便于复核，未采用方案的用后删 `frappe-bench/tmp/replay_probe.py` 路径；业务数据仍必须事务回滚。

## 新增约定

无新增工程约定。模块、普通计算包、可选 HRMS 分支、CSS 颜色变量及 vendor 位置均沿用方案；README 已补模块边界、按某日计算入口／四条约定、已知限制及 ECharts Apache-2.0 来源。

## 未做项

TS-013～017 无剩余开发任务。TS-012 联合验收仍按用户裁决暂缓；不进入 E，不宣称 SL-008 或 D 全部通过。不打 tag。

## 版本交付

用户于 2026-10-16 明确授权「提交并推送」。App 代码已提交并推送至 `FrappeChina/main`，提交 `e1b562104e66ab9b88dcbf5fb798d64d8d63ab72`；主仓库将本回执、状态文档及测试取证脚本／截图一并提交并推送。备份、运行日志与站点配置不纳入版本控制。

## 续跑锚点

- TS-013～017 已完成，下一项为恢复 TS-012 前重新确定 Manufacture 联合验收口径；保留 `test_manufacture_native_loss_semantics_remains_pending` 与原失败证据。
- 测试站浏览器 fixture 已清；365 天数据已回滚；专用 6787 服务已停止。演示站 `bench start` 保持运行，日志仍在 `frappe-bench/logs/bench-start.log`。

## 状态值

`无法实现`——沿用 Part2 的 TS-012 当前联合验收结论；用户授权暂跳后的 TS-013～017 已完成，D 因 TS-012 未验收仍未结束，不能输出 `代码已落地` 或进入 E。

## 复核建议

- 对照 `spc.compute`：不等子组大小采用各组 R/d₂ 的均值；Cpk／Ppk 中心都按方案使用子组均值的均值；窗口规则只标末点。建议按 `test_spc.py` 常量和规则临界序列复算。
- 页面浏览器已覆盖报表跳转、逐点颜色及 tooltip；工作中心过滤的 Quality Inspection → Job Card 连接尚未造带工位的生产中检验单做专项断言，可后续人工补一条该场景。
- 后续产能需求读取包含 TS-012 修改后的卡数量与工时；TS-012 的 Manufacture 联合验收缺口仍须独立处理。流程中未严格逐切片先红后绿／全量的偏离如上，不据最终补验改写历史。
