# P1-S2-R2 A步验证：Master Production Schedule 的 make_mrp 缺失

环境：ERPNext 16.35.0（erpnext HEAD `12cd563 chore(release): Bumped to Version 16.35.0`）/ Frappe v16，站点 `erx.localhost`，本机 Docker。

## ① 判定：go（命题成立）

`make_mrp` 确实不存在，后台任务必抛 `AttributeError`，`MRP Log` DocType 也不存在。并且发现命题**未提到的第二处缺陷**，它改变了缺陷的形状：MPS 的 DocType JSON 里**完全没有 `is_submittable` 这个键**（`grep -c` 结果 0），DB 里 `DocType.is_submittable = 0`。所以 MPS 在界面上**不是可提交单据**，没有提交按钮，`on_submit` 在正常 UI 流程里根本走不到。

即 v16 的 MPS 是两层都没接完的半成品：界面提交不了；绕过界面用 Python API 强行提交则前台静默成功、后台任务失败。**本项目若要用 MPS 做闭环，绕行方案是必需的。**

## ② 实际跑了什么

存在性验证（站点上下文 `../env/bin/python`）：

```
Master Production Schedule: True
MRP Log: False
MRP-ish doctypes: []
  autoname: naming_series: | is_submittable: 0
   naming_series | Select | reqd= 1 | opts= MPS.YY.-.######
   company | Link | reqd= 1 | opts= Company
   posting_date | Date | reqd= 1 | opts= None
   from_date | Date | reqd= 1 | opts= None
   sales_orders | Table | reqd= 0 | opts= Production Plan Sales Order
   material_requests | Table | reqd= 0 | opts= Production Plan Material Request
   items | Table | reqd= 0 | opts= Master Production Schedule Item
class: <class '...master_production_schedule.MasterProductionSchedule'>
hasattr(doc,'make_mrp'): False
mrp-ish attrs: ['enqueue_mrp_creation']
get_attr module-level make_mrp FAILED: AttributeError module '...master_production_schedule' has no attribute 'make_mrp'
```

真建单 + 真提交。只需 4 个必填字段，三个子表全非必填，**不需要 SO / BOM / Material Request 前置数据**：

```
company: 华东弹簧
INSERT OK -> MPS26-000001 docstatus: 0
== meta.is_submittable == 0
== try .submit() ==
SUBMIT returned, docstatus: 1
== reload docstatus from db == 1
```

`.submit()` **前台没有任何报错**，docstatus 落库为 1——因为 `enqueue_doc` 只入队，`msgprint("MRP Log documents are being created in the background.")` 照常发出。入队证据（Redis long 队列）：

```
long | id: erx.localhost||a3b11802-... | func: frappe.utils.background_jobs.execute_job
    kwargs: {... 'method': 'frappe.utils.background_jobs.run_doc_method',
             'kwargs': {'doctype': 'Master Production Schedule',
                        'name': 'MPS26-000001', 'doc_method': 'make_mrp'}}
```

任务停在 QUEUED 是因为本次只起了容器、没跑 `docker/start.sh`，无 worker 消费。故直接调用 worker 实际执行的入口 `frappe.utils.background_jobs.run_doc_method(doctype, name, doc_method)` 复现。

## ③ traceback 原文

```
Traceback (most recent call last):
  File "/workspace/.tmp-verify/verify3.py", line 22, in <module>
    run_doc_method("Master Production Schedule", "MPS26-000001", "make_mrp")
  File "/workspace/frappe-bench/apps/frappe/frappe/utils/background_jobs.py", line 236, in run_doc_method
    getattr(frappe.get_doc(doctype, name), doc_method)(**kwargs)
    ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'MasterProductionSchedule' object has no attribute 'make_mrp'
```

源码实读 `master_production_schedule.py:441-450` 确认调用链：`on_submit` → `enqueue_mrp_creation`（存在）→ 入队 `make_mrp`（不存在）→ 建 `MRP Log`（DocType 不存在）。三处与静态证据完全一致。旁证：`master_production_schedule.js:65` 的 `View MRP` 按钮跳的是 `Material Requirements Planning Report` 报表，**不是** MRP Log 单据——说明 MRP Log 这条线是未完成的设计残留。

## ④ 创建 / 清理了什么

- 启动了 Docker Desktop 守护进程（原本未运行）。未改配置、未 `bench install-app`、未重装站点、未改源码、未做 git 操作；`apps/erpnext` 的 `git status` 为空。
- `Master Production Schedule` / `MPS26-000001` → **已 cancel + delete**，count 归 0。
- 队列里 2 条相关 job（`make_mrp` 与 delete 副产物 `delete_dynamic_links`）→ **已删**，三队列深度均归 0。
- 临时脚本目录 `.tmp-verify\` → **已删**。主仓库 `git status` 只剩本报告目录与原有的 `crm_api.json`。

## ⑤ 未能验证的部分

- 未起 `docker/start.sh`，故**没观测到真实 worker 消费该任务并写 Error Log**；`run_doc_method` 直调等价复现，差异仅在异常是否被 RQ 捕获落 Error Log，`AttributeError` 本身已确定。
- 未在浏览器界面上目视确认"提交按钮不显示"，该结论来自 meta 与 JSON 的 `is_submittable`。
