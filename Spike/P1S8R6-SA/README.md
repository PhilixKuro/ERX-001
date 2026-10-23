# HT-015 / LG-002 实机探针

2026-10-23，新Session SA。只使用从s8dev克隆的专属站点`s8ht015.localhost`，未修改生产码。D待验表已填go；此go以方案的scheduler关闭、生成期间不换库及A6分离克隆为边界。在途任务明确仍会写原库。

## 结果

| 观测 | 实测 |
|---|---|
| 换库后新任务（同一个nofork worker进程） | 5.54秒读写B |
| 换库前排队、换后开始的fork任务 | 12.58秒读写B |
| 换库前已开始的fork任务 | 换后6.44秒继续读写A |
| 超过60秒的新任务 | fork/nofork均读写B |
| 同一个scheduler进程 | 换后5.58秒、67.68秒读写B；原生Scheduled Job任务体也读写B |
| scheduler关闭对照 | tick前后专属队列均0 |
| 目标前缀未删除 | 数据库原始值7，独立新进程get_cached_doc读旧缓存4 |
| 删除目标前缀 | 删除18键、立即剩0键，独立新进程读7 |
| A6分离克隆 | 子进程启动后0.010秒切B；32.96秒完成从显式源A克隆，目标标记A |

当前源码`frappe.init`仅在`is_request=True`时启用配置缓存，原生RQ与scheduler默认不走该缓存。探针在启动worker/scheduler时特意先用`is_request=True`预热A库缓存，后台仍即时读B。

`ht015_probe.py`把探针模块仅注册到当前进程的`frappe.ht015_probe`命名空间；不往app目录落文件。fork worker用RQ Worker与Frappe原生execute_job；nofork用FrappeWorkerNoFork。scheduler只重定向队列传输并限定单站tick，保留原生初始化、活动/到期筛选、ScheduledJobType.enqueue、run_scheduled_job与执行链；未启动全局遍历所有站点的scheduler。scheduler站点配置保持pause_scheduler=1，只有受控探针进程的内存conf解除暂停，以免任何全局scheduler碰到该克隆站。

## 证据与清理

定长证据在`evidence/ht015-run.log`、`ht015-redis.log`、`ht015-detached.log`、`ht015-cleanup.log`。原始日志、worker输出及状态信号留在未受管的`frappe-bench/logs/ht015-*`。

已停止自己启动的两个worker和scheduler；子进程克隆已退出。专属站点、A/B/克隆目标三个库、专属DB用户、目标Redis前缀、专属RQ作业与队列键均清理；清理后查数据库无`_ht015`前缀残留。s8dev的6787服务继续运行，未改s8dev站点配置或scheduler设置；未访问test或erx数据库。

## 重跑

必须先确认专属站点及上述库名不存在。`setup.py`从标准输入接收`docker compose -f docker/compose.yaml config --format json`，凭据只在内存/子进程环境中，不打印。它从s8dev克隆A/B并创建专属DB用户。随后容器内以bench/env/bin/python运行`run_ht015.py`（PYTHONPATH指向本目录）、`redis_ht015.py`；`detached_ht015.py`同样从标准输入接收compose配置。最后运行`cleanup_ht015.py`（同样接compose配置）。每个脚本中的直接Frappe初始化前均先进入bench/sites。

`run_ht015.py`要求新的空`logs/ht015-state`目录；已有证据须先另存。各脚本运行日志重定向到bench/logs，不把长跑进程输出直接写本目录。setup从运行中的s8dev作一致性dump，本探针只验证通用数据库/任务/缓存行为，不验证整场业务数据一致性，也不替代TS-021/022后续浏览器验收。
