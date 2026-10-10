# R4 Part4 补充方案：独立前端裸渲染点

## 事实证据

`Spike/P1S6R4-translation-runtime.json` 在演示站 zh 会话记录了接口词典、页面 boot、运行时消息对象和正文。CSV/API 已返回中文，但仍可见以下界面英文：

| 前端 | 实际渲染点 | 证据 | 结论 |
|---|---|---|---|
| CRM | `frappe-ui` `Onboarding/GettingStartedBanner.vue` 与 `OnboardingSteps.vue` 使用裸字符串 `Getting started`、`Start now`、`0/10 steps`；CRM dashboard 图表数据的系列/单位也有裸字符串 | `frappe-bench/apps/crm/frontend/node_modules/frappe-ui/frappe/Onboarding/*.vue`；页面正文 | CSV 不会被这些组件消费 |
| Insights | `frontend/src2/components/DemoDataBanner.vue:52` 直接写 `Explore with sample data and a pre-built workbook` | 源码与 `/insights/dashboards` 正文 | 该句没有 `__()` 调用；整句 CSV 不能修复 |
| Raven | 源码 `ChatStream.tsx:373-374` 调用 `_()`；生产页 `window.frappe.boot.__messages` 有中文，但 `main.tsx` 的生产分支没有把 `__messages` 赋给 `frappe._messages`。`translate.ts` 只读 `_messages` | 运行时探针：正常页 `_messages` 为空；隔离注入 `boot → _messages` 后正文变为「暂无消息／发送消息开始对话／发送」 | 这是独立前端启动接线缺口，非 CSV 缺词 |

## DEC-026：自有 app 限定适配（用户已批准）

用户选择 A：“追加自有 app 限定适配”。该补充成为 TS-014 的追加执行依据；不放宽完整逐屏验收，不改上游源码，不授权任何版本提交。

自有 app 增加一个 `update_website_context` hook：仅在原始 template 分别为 `www/crm.html`、`www/raven.html`、`www/insights.html` 时切换到自有薄包装模板。包装用 app 前缀 include 当前上游模板（例如 `raven/www/raven.html`），复用上游 boot、权限校验、入口 bundle 与资源 hash，在 `</body>` 前追加本 app 的静态脚本。`web_include_js` 不适用：这三张独立入口没有使用 Frappe website 基模板。

只读 `Spike/P1S6R4-template-probe.py` 已验证三个模板都可经 `context.template` 切换、include 保留原 HTML、只追加一处脚本。探针使用进程内 DictLoader，未向 app 写临时模板或注册 hook。它证明渲染接点可用，不等于在线权限/缓存/加载次序验收。

具体资产与行为：

| 落点 | 行为 | 边界 |
|---|---|---|
| `website_translation.py` 与 `templates/independent_apps/*.html` | 输出来自合并 CSV 词典的限定源词 JSON，追加对应自有脚本 | 仅中文会话与已知入口模板；不复制 bundle，不改官方 app |
| `public/js/raven_messages.js` | 在 boot 已注入、module 执行前，将 `boot.__messages` 接到 `_messages`；已有运行消息不丢失 | 仅 Raven；没有词典时告警并保留原行为 |
| `public/js/independent_app_labels.js` | 对 CRM 入门横幅/帮助面板/图表标签及 Insights 演示横幅建立明确范围的文字适配；有限源词表精确匹配，从 CSV 取目标词；动态步数用 `{0}/{1} steps`、`{0}/{1} steps completed` 等参数化键 | 只监听上述 UI 区域，不把整页业务数据、input value、消息/频道/图表数据键当译名；禁止翻译 `general` 或固定写 `0/10 steps`；缺少字典/范围不匹配必须可诊断 |

CRM 图表 `series.name` 是数据键（`leads`、`won_deals` 等），禁止为翻译改写它；适配只改渲染出来的图例/坐标标题/单位。动态重渲染需有幂等标记/源值记录，防止反复触发观察器。上游组件结构变更时需重新定位，不增加全站通用 DOM 词典替换。

新增验证：先红后绿验证入口范围、非中文退出、已有消息保留、动态数字、重渲染、精确 UI 范围及用户数据不变；测试站在线验证三个入口与路由切换，撤钩后复现英文、接回后中文；检查匿名/非管理员权限、缓存和模块启动次序；README 登记上游 commit 与失效症状。通过后恢复原 TS-014 完整屏核、备份 B/恢复/基准点 C，最后跑 TS-015。三个模板“include”的只读探针与 Raven 浏览器探针都不能替代这些验收。

## 可选处理路径

1. 由对应上游修复裸字符串/生产初始化，再升级锁定 commit；不在本任务改上游目录。
2. **推荐**：由 `frappe_china` 按上节提供限定覆盖接线，翻译内容仍只来自 CSV；代价是新增三张入口薄包装及独立前端覆盖维护面。需要批准追加该范围，才实现产品接线。
3. 对本轮演示验收把这些点列为明确未通过项，登记延迟需求，待独立前端升级时处理。

当前 R4 仅完成了证据与 CSV 可修项；没有把全局 MutationObserver 或未经批准的上游源码修改混入实现。未作路径选择前，TS-014 不标完成。

## 暂停来源

冻结开发方案总纲 §九1：“如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写”；`bricks/receipt.md` 执行纪律4：“发现方案有问题……暂停反馈用户，不自行换方案”。现有 TS-014 规定发现英文只补 CSV，但上述点不消费 CSV，因此需要这次明确的范围裁决。前序 DEC-024/025 仅批准侧栏守卫与固定时间戳，不包含这三个独立入口。
