# showcase：客户演示用示意界面

纯静态 HTML，双击打开（`file://`），不连 ERPNext、不起服务、不走网络。可以拷到 U 盘带去现场。来由见 `docs/01-需求摸底/S09-演示材料/`（P1-S9 R01 DEC-009）。

## 目录

| 路径 | 内容 |
|---|---|
| `shared/index.html` | 设计语言样板页：配色、字体、指标卡、按钮、状态、进度条、四类图表、表格、预警、能不能接 |
| `shared/tokens.css` | 设计变量：颜色、字号、间距、圆角、阴影，深浅两套取值 |
| `shared/components.css` | 通用组件，类名统一用 `sc-` 前缀 |
| `shared/theme.js` | 深浅主题切换；`SC.chart()` 建 ECharts 图，切换主题时自动重画 |
| `shared/data.js` | 各界面共用的一份假数据，挂在 `window.SC_DATA` |
| `shared/vendor/` | ECharts 5.6.0（Apache-2.0，许可文件同目录），从 `frappe_china` 拷来 |
| `sales/index.html` | 销售工作台（销售负责人，默认浅色）：商机与能不能接、漏斗、线索、报价试算、重点客户、应收账龄、在手订单交期；点商机或客户从右侧滑出详情（P1-S9 R03） |
| `{界面}/index.html` | 其余界面各一个子目录，后续各 Round 建 |

## 新界面怎么接

```html
<html lang="zh-CN" data-theme="dark">  <!-- 数字孪生、驾驶舱默认 dark，其余默认 light -->
<link rel="stylesheet" href="../shared/tokens.css">
<link rel="stylesheet" href="../shared/components.css">
<body class="sc">
...
<script src="../shared/vendor/echarts-5.6.0.min.js"></script>
<script src="../shared/data.js"></script>
<script src="../shared/theme.js"></script>
```

- 颜色只用 `tokens.css` 里的变量，不要写死；ECharts 里用 `SC.css("--st-alarm")` 取色。
- 地址栏加 `?theme=light` 或 `?theme=dark` 可以覆盖默认主题，`SC.toggleTheme()` 切换。
- 本地 JSON 在 `file://` 下用 `fetch` 读不了，数据一律放进 `.js` 文件。
- 字体用系统自带的苹方和微软雅黑，不打包字体文件。

## 假数据（`shared/data.js`）

**名字**沿用一年期场景（`frappe_debug/data/scenario.yaml`）：华东弹簧有限公司、30 家「城市＋弹簧厂」客户、钢丝供应商01～12、5 个产品、3 种钢丝、员工「HDTH 场景员工 01」起。**规模**扩成 11 台设备：卷簧机-1～4、回火炉-1～2、磨端机-1～2、喷丸机-1、检验台-1、包装线-1。在手订单的数量也放大了，否则设备负荷显不出忙闲。这一处与九幕现场演示的规模不同，演示时口头说明一句即可。

「今天」固定为 2026-11-02 10:30（场景的终点）。文件上半部是原始数据，下半部「派生」由原始数据算出，**不要手改派生结果**，要改就改原始数据：

| 派生字段 | 算法 |
|---|---|
| `products[].unitCost`、`salesOrders[].margin` | 钢丝成本 ＋ 工序工时 × 设备小时费率 × 制造费用系数 3.5 |
| `workOrders[].operations`、`finishDate`、`risk` | 按交期先后排程：每道工序取「上道完工」和「设备空出」中较晚的时刻；每天 480 分钟，周日休息；计划数量按工序损耗反算 |
| `workstations[].load` | 未来 6 个工作日的剩余工时 ÷ 可用工时 |
| `ctp(product, qty, wantDate)` | 能不能接：插在现有排程之后，每道工序挑最早空出的同类设备，并检查钢丝够不够、是否要等在途或新采购 |
| `quote(customer, product, qty, wantDate, price?)` | 报价试算：单价缺省取标准价；返回未税与含税金额、毛利、`ctp()` 结果、接下后的信用占用、账期，以及警示（会晚、缺钢丝、超信用额度、有逾期、毛利低于 20%） |
| `customers[].creditUsage` | （应收 ＋ 在手订单含税额）÷ 信用额度 |
| `customers[].history`、`yearRevenue`、`trend3m` | 近 12 个月每月销售额（未税、已开票口径）与单数，逐月合计等于 `monthly[]`；当月已开票的发票先落到对应客户，余额按客户等级和走势分摊，建档前的月份为 0。另起随机种子，不影响 SPC 读数。`trend3m` 为近 3 个月对前 3 个月，单太稀的为空 |
| `materials[].suggestQty` | 库存 ＋ 在途低于再订货点时，按经济订货量给建议（订货成本 80，持有成本率 18%） |
| `spc` | X̄-R 控制限取前 16 组计算；按 Nelson 第 2 条判异；算 Cpk |
| `kpi` | 汇总指标与预警清单；`kpi.funnel` 商机漏斗（到达过各阶段的商机数），`kpi.aging` 应收账龄与近期开票回款 |

目前这份数据能讲的情节：

| 情节 | 数据里的体现 |
|---|---|
| 车间瓶颈 | 卷簧机-1 未来 6 天负荷超过 100%；`SAL-ORD-2026-00316`、`00317` 预计晚于交期 |
| 质量异常 | 卷簧机-2 压簧 3.0 的自由长度连续 9 组偏上，SPC 判异 |
| 设备待料 | 60Si2Mn φ8.0 钢丝低于安全库存，卷簧机-4 在等到货 |
| 设备停机 | 喷丸机-1 计划保养 |
| 接不下的单 | 商机 `CRM-DEAL-2026-00087`（常州弹簧厂 4 万支）比客户要的日期晚 1 天 |
| 回款问题 | 泰州弹簧厂信用额度占用约 96%，并有逾期应收 |
| 客户走势 | 常州弹簧厂近 3 个月销售额比前 3 个月涨 55%（它正谈着商机 087）；泰州弹簧厂跌 38% |

要核对数字，可以在浏览器控制台里看 `SC_DATA`，也可以用 node 跑：`node -e "global.window={};require('./shared/data.js');console.log(window.SC_DATA.kpi)"`。
