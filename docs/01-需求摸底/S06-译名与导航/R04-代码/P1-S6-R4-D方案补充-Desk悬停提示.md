# R4 Part4 补充方案：Desk 悬停提示裸渲染

## 事实与范围

正式提取器包含可见元素的 `title` 与 `placeholder`，不能为了通过验收删掉这些属性。`Spike/P1S6R4-screens-forms-v6/result.json` 中生产计划、库存凭证和首页仍有英文。

- `frappe/public/js/frappe/form/controls/button.js:27` 用 `df.title || df.label` 直接填 `title`；`:84` 仅给按钮正文调用 `__(df.label, null, df.parent)`。`Spike/P1S6R4-context-probe.cjs` 实测 `__('Get Sub Assembly Items')` 已为中文，按钮正文也为中文，未译的是悬停提示。包括获取半成品、获取采购/调拨物料、更新单价与可用量。
- 首页搜索按钮 `title="Search"` 未消费 CSV，正文/快捷键正常；精确选择器需在只读 DOM 探针中定下。
- `Global Defaults` 在 `.form-details` 内是单例记录名，不是界面字段标签；按需求 §4.9 用户数据排除，不改其值。单号系列、用户姓名、主数据名称同理按带理由的选择器排除。

## DEC-027：限定实现（用户已批准 A）

1. 自有 `desk_patches.js` 包装 `ControlButton.prototype.set_label`：先完整委托原方法；仅 zh、未设置自定义 `df.title` 时，使用 `__(df.label, null, df.parent)` 更新该按钮的 `title`。保留返回值、参数和点击处理，不改元数据、数据值或非中文会话；幂等标记防止重复包装。类/方法缺失告警并保留原行为。
2. 首页搜索提示仅对已确认的官方搜索按钮挂载点修正为 `__('Search')`，与原创建方法组合；不用全站属性扫描/词典替换。先验证原方法与选择器，再实现。
3. 所有译文仍来自 CSV，官方重叠登记测试清单；README 记录上游 commit、失效症状与复验路径。
4. 测试先红后绿覆盖原方法/返回值、zh/en、显式 title 保留、上下文、幂等与缺接点；真实页面撤钩/接回截图证明英文 title 消失且原按钮行为可用。回到 TS-014 完整核、备份 B/恢复 A/C，TS-015 最终全量后方能完成 D。

## 裁决路径

| 选项 | 描述 | 优点 | 缺点 |
|---|---|---|---|
| A（推荐） | 批准上述两处自有 app 限定适配 | 维持完整中文与属性验收，不改上游 | 增加两处前端覆盖维护面 |
| B | 等上游修复并升级锁定版本 | 避免本地包装 | 本轮验收继续受阻 |
| C | 将这些悬停提示列为延期并修改验收范围 | 可继续收尾 | 演示仍有英文提示 |

用户已批准 A，执行上述范围。首页只读 DOM 与源码探针确认选择器 `.desktop-search-wrapper #desktop-navbar-modal-search`；与其原接线方法 `AwesomeBar.setup(selector)` 组合，仅该 selector 匹配时修 title。暂停依据：冻结方案总纲 §九1“如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写”；先前 DEC-026 只涵盖独立前端，不涵盖 Desk 控件。
