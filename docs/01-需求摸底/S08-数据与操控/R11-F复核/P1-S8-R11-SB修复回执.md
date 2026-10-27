# SB回执（对象：代码 / 依据：R11 F 复核报告 `新Session修` 1 项＋R05 开发方案）

**轮次**：P1-S8-R11（`plannedDev` SB，附属 R11 F，不占 Round）｜**日期**：2026-10-27｜**执行者**：Claude（Opus 5.5；Workflow 预设 CodeX，同 S8 D 步偏离）｜**打tag**：否

**清单**：复核报告裁为 `新Session修` 的 FD-037。待裁决点 2026-10-27 开工前答复：修法选①不删文件的锁；站点操作锁 `operation.py` 一起改。原文已填回复核报告裁决列。`出方案修` 的 FD-043 走 C 步，本步不动。

**起点**：`frappe_china` `a2912dd`、`frappe_debug` `4e8c78e`（R11 F 当场修后，`docker/apps.json` 锁定的提交）。

**提交**（用户 2026-10-28 许可）：`frappe_debug` `14077b7` 已推送，`docker/apps.json` 已锁定；`frappe_china` 未改。整场重跑留到 R12 C、R13 D 落地之后（见未做项）。

## 逐项执行结果
| 任务 | 报告项号 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| 1 | FD-037 | 新增 `frappe_debug/demo/locks.py`（`acquire`:24、`release`:44、`site_lock`:52：在 `sites/{site}/locks/{name}.lock` 上 `fcntl.flock`，文件建了就不删，超时抛 `filelock.Timeout`，每 0.05 秒轮询一次）；`demo/registry.py:20-26`（`_registry_lock`：包 `site_lock("frappe_debug_snapshots", timeout=30)`，超时转 `frappe.utils.file_lock.LockTimeoutError`，与原 `frappe.utils.synchronization.filelock` 超时时抛的类型相同）；同文件 7 处 `with filelock("frappe_debug_snapshots")` 改为 `with _registry_lock()`（:140、145、150、164、254、283、299）；新增 `tests/test_locks.py` 3 条 | ✅完成 | 2026-10-27 | 按裁决①。锁文件名、路径、超时 30 秒都照旧，只换实现，调用方一处未动。原生 `filelock` 释放时先 `unlink` 再解锁，正是竞争窗口所在；新锁不 `unlink`，另一进程 `os.open` 总能打开同一个 inode，也就不必像 filelock 那样核 `st_nlink`。旧锁文件留在原处，新锁直接复用，不用迁移。新锁不可重入，读过原代码：登记表锁内没有嵌套再取同一把锁的路径（`_read_unlocked`／`_write_unlocked`／`_claim_refill_unlocked` 都不取锁） |
| 2 | FD-037 | `frappe_debug/demo/operation.py:17-25`（`operation`：`locks.acquire("frappe_debug_demo_operation", timeout)`／`locks.release(fd)`，去掉 `filelock.FileLock` 与 `Path`） | ✅完成 | 2026-10-27 | 按裁决「一起改」。超时仍转 `DemoOperationBusy`（FD-014 的「请稍后重试」），`site_operation` 装饰器与 `runner._run_generate` 的 `operation(timeout=10)` 不用改。原实现每次调用都新建一个 `FileLock` 实例，同一进程内嵌套取锁本来就超时（容器内实测：持锁时另建实例 `acquire(timeout=0)` 得 `Timeout`），新锁不可重入与此相同，不是新行为。另查过所有 `site_operation` 函数与 `operation()` 调用点：没有在持锁时再进另一个 `site_operation` 的路径（`_run_generate` 调的是 `generate.__wrapped__`；`replenish` 由 `_replenish_after_response` 在响应结束、换库锁已释放后调用）。`test_workspace` 里「生成与换库同锁」用例照过 |
| 3 | FD-037 | 复验：挂载目录探针 `Spike/P1S8R11-SB/site_lock_probe.py`、锁相关 7 个测试模块、全量门禁、整场重跑预跑（RS-006） | ⚠️部分 | | 探针与模块测试已过（见「复验结果」）；全量门禁见「全量验证」。**整场重跑预跑未做**：用户 2026-10-28 裁决，等 FD-043 的 C 方案（R12）与代码（R13）都落地后整场只重跑一次，FD-037 与 FD-043 一并复验，省掉一轮约两小时 |

## 复验结果
| 报告项号 | 报告的判定标准 | 怎么复验的 | 实测结果 |
|---|---|---|---|
| FD-037 | 修后用 `Spike/P1S8R11-F/p3/lock_unlink_probe.py` 在挂载目录复跑应为 0 | 原探针只测 `filelock`，测不到新锁，故另写 `Spike/P1S8R11-SB/site_lock_probe.py`：同一目录、同样 4 进程×300 次，先跑修前的 `filelock` 作对照，再跑修后的 `locks.site_lock`。在挂载目录 `sites/test.localhost/locks/r11sb-probe` 与容器本地 `/tmp/r11sb-probe` 各跑一次 | 挂载目录：`filelock` 217/1200 次 `FileNotFoundError`（与 R11 F 的 216/1200 一致，复现成立），`site_lock` **0/1200**；`/tmp` 两者均 0 |
| FD-037 | 凡取这把锁的接口都不再偶发报错（问题描述） | 新增 `tests/test_locks.py`：释放后锁文件仍在且能再取、持锁时 `timeout=0` 抛 `Timeout`、4 进程×200 次在锁内做无保护的读改写计数（互斥失效就会丢更新；`TemporaryDirectory` 在容器本地 `/tmp`，挂载目录上的竞争由上一行探针覆盖）。连同调用方模块一起跑：`test_locks` 3/3、`test_registry` 9/9、`test_workspace` 16/16、`test_switch` 12/12、`test_snapshot` 4/4、`test_progress` 6/6、`test_scenario_runner` 9/9 | 通过。计数 800/800、错误 0。真实接口层面的复验（演示中途 `save_progress`／`switch_to_act`／`snapshot_status` 不再 500）要等整场预跑与换库实跑，见未做项 |

## 全量验证
| 门 | 结果 |
|---|---|
| `frappe_debug` Python 全量 | 197/197，退出码 0（`spawn` 修后重跑，日志 `frappe-bench/logs/s8-r11sb-full-frappe_debug-2.log`）。首轮 197/197 但退出码 134，见偏离与暂停。基线 194，新增 `test_locks` 3 条 |
| `frappe_china` Python 全量 | 486/486＋6＋4，与基线相同（本步未改该 app） |
| Node | `frappe_debug` 102/102、`frappe_china` 116/116，与基线相同 |
| Ruff check／format | 两 app 通过。门禁跑完后 `registry.py` 报 I001（import 顺序），`ruff check --fix` 修正后复查通过 |
| 构建 | `bench build --app frappe_debug`、`--app frappe_china` 退出码 0 |

脚本 `Spike/P1S8R11-SB/gates.sh`，摘要 `frappe-bench/logs/s8-r11sb-gates.summary`。

## 偏离与暂停

- **开工前暂停 1 次**（复核报告留的待裁决点）：用户 2026-10-27 答「选①、`operation.py` 一起改」，FD-043 同时答「改评分口径，无单月份不计分」。
- **执行中暂停 1 次**：按 RS-006 改了演示代码就要整场重跑预跑，开跑时已 23:50。场景终点取预跑当天，SPC 候选计划按 E＝2026-10-27 筛，一跨日就要先在 `s8r9` 重筛。用户先裁「明天做全套」，2026-10-28 改为：本 Session 先提交推送，新 Session 做 FD-043 的 C 方案和代码，之后整场只重跑一次，两项一起验。本步因此停在 ⚠️，不标 `修复已落地`。
- **门禁中发现自己的测试有问题，已当场修**：首轮全量 `frappe_debug` 197/197 通过，但进程退出码 134。原因是 `tests/test_locks.py` 用 `fork` 起子进程，Python 3.14 在解释器退出时 abort（`Fatal Python error: gilstate_tss_set`）。单独跑这个模块能复现，`test_registry` 单独跑退出码为 0。用户选「先修再提交」，改成 `spawn` 后单独跑 3/3，退出码 0。只动了测试，演示代码没动。
- 复核报告判定标准里的探针只测 `filelock`，测不到新锁，所以另写了一份探针，修前、修后同场对照（见「复验结果」）。标准没有放宽。

## 新增约定
| 约定 | 类别（命名/位置/错误处理/依赖/跨层调用） | 在哪个任务确立 |
|---|---|---|
| `frappe_debug` 跨进程的站点级锁一律用 `frappe_debug.demo.locks`（`site_lock`／`acquire`＋`release`），不用 `filelock.FileLock` 或 `frappe.utils.synchronization.filelock`：后两者释放时删锁文件，在 Windows 挂载目录上会偶发 `FileNotFoundError`。锁文件放 `sites/{site}/locks/`，超时抛 `filelock.Timeout`，由调用方转成自己的错误类型 | 位置／依赖／错误处理 | 任务 1、2 |

`switch.py` `_refill_lock` 给 shell `flock` 命令用的锁文件不在此列：shell `flock` 不删文件，没有这个问题，本步未动。

## 未做项
| 项 | 为什么没做 |
|---|---|
| 整场重跑预跑（RS-006）与真实接口复验 | 用户 2026-10-27 裁决明天做全套（见偏离与暂停）。做法：先在 `s8r9` 带各幕整场彩排，重筛 SPC 候选计划；把计划拷到 `erx`，回基库、清快照与工作库，整场预跑；跑完核工作库 `verify` 与 27 份快照登记，再在 web 日志里搜 `FileNotFoundError` 与 `frappe_debug_snapshots`，应为 0 |

## 状态值

**暂未给出**：任务 3 为 ⚠️。代码已改，探针与模块测试已过，整场重跑预跑还没跑，所以不标 `修复已落地`。下一 Session 跑完全套后再定状态。

## 复核建议

1. **修得最勉强的那项**：没有绕过症状的修法。报告指出的根因是「释放时删锁文件」，新锁不删文件。可查 `demo/locks.py:24-49`，对照 filelock 3.20.4 `_unix.py` `_release` 读。
2. **修复引入的连带影响**：改动的文件是 `demo/locks.py`（新增）、`demo/registry.py`、`demo/operation.py`、`tests/test_locks.py`（新增），落在报告列的范围（`registry.py` 7 处调用与 `operation.py`）之内。调用方一处未动。行为上有两处差别。一是超时：登记表锁仍抛 `LockTimeoutError`，但不再像 Frappe 的 `filelock` 那样先写一条 Error Log。原来的 Error Log 只在 30 秒超时才写，演示里从没出现过。二是轮询间隔：filelock 缺省 0.05 秒，新锁也取 0.05 秒。
3. **拿不准处**：探针是 4 进程连续抢锁的压力测试，单人讲演时的实际并发低得多。0/1200 说明竞争窗口已消失，但「演示中途不再 500」要等整场预跑与换库实跑之后才能下结论。
