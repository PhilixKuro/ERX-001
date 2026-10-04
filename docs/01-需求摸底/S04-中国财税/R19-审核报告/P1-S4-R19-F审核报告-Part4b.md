# P1-S4-R19 F 审核报告 · Part4b（FD-083 复核：README 1901 来源四条）

> 对象：frappe_china `README.md`「已知限制」1901 来源条（`cd5d565..6cb779c`，现位于 `README.md:129-135`）及其后的月末结转条（`:136`）
> 标准：R18 `P1-S4-R18-F审核报告.md` FD-083 行（:139）与「当场修清单」#2（:171）；R18 Part4 P4-04（:51）与逐项表 FD-050 行（:39）；上游 erpnext v16.35.0（`12cd563`）源码；erpnext／frappe `locale/zh.po`
> 方法：只读码与 grep。没跑测试，没写站点。站点只做了 3 次 SELECT：HDTH 的 `stock_adjustment_account` 与永续盘存开关、`account_type='Temporary'` 的明细科目按 `creation` 排序、Item／Stock Reconciliation 相关 Property Setter（结果为空）。

## 覆盖自证

- 查了：README diff 全文；`stock_entry.py:811-863`（validate_item 回填）、`:2665-2750`（get_item_details 回退链）、`:3377-3393`（load_items_from_bom 成品行）、`:3695-3726`（按已转移物料带出原料）；`stock_entry_utils.py:100-134`；`bom.py:1497-1613`；`stock_entry_type.py:100-140、291-346`；`job_card.py:1735-1745`；`item.py:178-193、292-330`、`item.json:257-265`、`item.js:134-187`；`subcontracting_receipt.py:930-950`；`stock_reconciliation.py:66-81、975-990、1421-1429`、`stock_reconciliation.js:45-56、246-262`、`.json:54-60`；`stock_controller.py:754-830`；frappe `database.py:595-680`、`query.py:1207-1240、1336-1362`（get_value 默认排序）；两份 zh.po 与 app `translations/zh.csv`；`closing.py:92-128`。
- 跳过：没在浏览器里验证物料表单「期初库存」字段是否可见（P4b-03 是读码推断）；没实跑 `get_difference_account`（P4b-01 的取值是读码加 SELECT 推断）；BOM 生产时 1901 借贷是否相互抵消（R18 已列为推演，本片没往下查）；Material Transfer 等其它用途是否在 1901 上留对冲行。

## 已修项复核表

| # | README 写法 | 上游实际（文件:行） | 一致否 |
|---|---|---|---|
| 1 | 物料移动（其他出库、其他入库等手工录入的行）：物料与物料组都没有默认费用科目时落 1901 | `stock_entry.py:2726` 所有用途先取物料默认值再取物料组默认值；`:2737-2738` 其他出库同一取法（R17 以前说它例外，不对）；`:2740-2743` 两者都空时取 Company `stock_adjustment_account`。`:851-852` 由 validate_item 在行上为空时回填，所以手工行和 API 建的行都走这条。其他入库（Material Receipt）没有单独分支，回退链相同 | ✅ |
| 2 | 按 BOM 或作业卡带出的行：BOM 只看物料默认值，作业卡完全不取，物料组上设的不起作用 | BOM：`bom.py:1513` 只 join `Item Default`，`:1606-1613` 为空或公司不符时取 `stock_adjustment_account`，回填后 validate_item 不再覆盖；`stock_entry.py:3391-3393` 的 BOM 成品行也只看物料级，为空直接取 1901。作业卡：`stock_entry_type.py:291-326` 取的字段里没有费用科目，`:320-328` 一律取 1901。**但**作业卡成品行（`stock_entry_type.py:333-346`）和按已转移物料带出的原料（`stock_entry.py:3699、3723`）只取物料级默认，为空时留空，再由 validate_item 按物料组回退 | ⚠ 原料行一致；「作业卡完全不取」对作业卡成品行不成立（P4b-04） |
| 3 | 物料主数据填了「期初库存」：保存物料时自动建物料移动，贷方直接记 1901 | `item.py:192-193` 只在 `after_insert` 触发；`:318-327` 调 `make_stock_entry` 时没传费用科目；`stock_entry_utils.py:107` 定为其他入库，`:133-134` 在 `is_opening == "No"` 时取 Company `stock_adjustment_account`，回填后 validate_item 不改。借库存科目、贷 1901。只发生在新建物料首次保存时 | ✅（「保存物料时」可更准确写成「新建物料保存时」，不影响结论；字段可达性见 P4b-03） |
| 4a | 委外收货的分摊损失 | `subcontracting_receipt.py:942-944` 分摊差额 `divisional_loss` 无条件取 `stock_adjustment_account` | ✅（界面词见 P4b-02；README 的避免办法挡不住它，见 P4b-01） |
| 4b | 服务端建的期初库存调账 | `stock_reconciliation.py:68-71` validate 时差异科目为空就取 `stock_adjustment_account`，不分目的；`:981-987` 期初目的只拒绝损益类科目，1901 是资产类，能通过 | ✅ |
| 5 | 界面词：其他出库、其他入库、物料移动、物料默认值、期初库存、库存调账、物料组 | erpnext `zh.po`：Material Issue→其他出库 `:30693-30694`；Material Receipt→其他入库 `:30707-30708`；Stock Entry→物料移动 `:52227-52228`；Item Default(s)→物料默认值 `:27228-27229、27236-27237`；Opening Stock→期初库存 `:34123-34124`；Stock Reconciliation→库存调账 `:52482-52483`；Item Group→物料组 `:27392-27393`。frappe `zh.po` 没有这些 msgid，app `zh.csv` 也没有覆盖 | ✅ |
| 5' | 界面词：BOM、作业卡、委外收货 | BOM→物料清单 `:7095-7096`；Job Card→**生产任务单** `:28401-28402`；Subcontracting Receipt→委外入库 `:53328-53329` | ❌ 三个都不是界面词（P4b-02） |
| 6 | 避免办法：物料组与每个物料的「物料默认值」都设好费用科目；期初库存不在物料上填，改用库存调账录入 | 设费用科目对第 1 条有效，对第 2 条的 BOM 行有效；对作业卡原料行（`stock_entry_type.py:320-328`）和委外分摊损失（`subcontracting_receipt.py:942-944`）无效。「改用库存调账」：服务端建的调账不传差异科目仍落 1901，这正是 README 第 4 条自己列的来源；界面上目的选「期初库存」时，默认差异科目由 `get_difference_account` 取（`stock_reconciliation.py:1421-1429`），按读码会取到最新建的 Temporary 明细科目 `5711072 罚款支出`（损益类），保存时会被 `:981-987` 拦下 | ❌ 部分无效，且和第 4 条自相矛盾（P4b-01） |
| 7 | 月末结转「结转后该月又有凭证变动」只看损益类、`2221000` 全部明细、`3103`，12 月另含 `1901`；口径为草案 | `closing.py:92-101` `_closing_read_accounts`：`2221000` 下全部明细，加 `3103`，12 月加 `1901` 下全部明细；`:116` 加上 `root_type IN ('Income','Expense')`。README 标了「口径为草案，待会计确认」 | ✅（交叉印证分片 2） |

## 开放查漏新发现表

| 编号 | 严重程度 | 定位 | 问题 | 违背的标准 | 建议修法 | 建议档位 | 待裁决点 | 证据 |
|---|---|---|---|---|---|---|---|---|
| P4b-01 | 低 | app `README.md:135`「避免办法」 | **避免办法覆盖不了它列出的所有来源，期初库存那半句还会把人引回 1901。** ① 设费用科目挡不住作业卡原料行和委外分摊损失，两者无条件取 Company 科目；README 第 2 条也写了「作业卡完全不取」，避免办法却没说这条挡不住。② 「改用库存调账录入」没说差异科目怎么填。S7 用脚本造数时不传差异科目，就是第 4 条的「服务端建的期初库存调账」，照样落 1901。在界面上把目的选为「期初库存」，默认差异科目按读码取最新建的 Temporary 明细科目。本科目表有 18 个这类科目，大多是损益类，最新的是 `5711072 罚款支出`，保存时会报「差异科目必须是资产/负债类科目」。这时用户最容易手选 Company 默认的 1901，校验也放得过。R17 Part5 P5-03 说这里取到的是 `9999 临时开账科目`，读码结论与之相反 | R18 当场修清单 #2 的意图（给出可行的避免办法）；R18 P4-04「补救办法会误导 S7 造数据」 | 改写为：「物料组的『物料组默认值』和每个物料的『物料默认值』都设好默认费用科目，这能挡住第 1 条和 BOM 带出的行。作业卡原料行和委外分摊损失挡不住，只能事后转出。期初库存不要在物料上填，改用库存调账，目的选『期初库存』，差异科目手选 `9999 临时开账科目`；用脚本建时须显式传差异科目。」 | 本Session修 | ① 期初差异科目是否定为 9999（这是会计口径，需会计确认）；② `get_difference_account` 取到损益类科目，要不要另开一条，在 app 里覆盖或给 18 个 Temporary 科目纠偏（超出本 README 范围） | `stock_entry_type.py:320-328`；`subcontracting_receipt.py:942-944`；`stock_reconciliation.py:68-71、981-987、1421-1429`；`stock_reconciliation.js:246-262`；frappe `database.py:664-667` 把默认排序改写为 `creation`，`query.py:1358` 未写方向时默认 desc；SELECT：HDTH 最新建的 Temporary 明细科目是 `5711072 罚款支出 - HDTH`（Expense，2026-10-01 11:38:59.03），`9999 临时开账科目` 最早建；科目表 `cn_smes_chart_of_accounts2024.json` 中 `"account_type": "Temporary"` 共 18 处。没实跑 `get_difference_account` |
| P4b-02 | 观察（在「低／观察」之间） | app `README.md:131、134` | 「作业卡」「BOM」「委外收货」都不是 zh.po 的界面词，界面上分别显示为「生产任务单」「物料清单」「委外入库」。R18 当场修清单 #2 写的是「界面词按 erpnext zh.po 取」，列出的四个词都已照办，这三个没在列表里 | R18 当场修清单 #2「界面词按 zh.po 取」；`docs/开发守则.md` 用界面词的惯例 | 改为「物料清单（BOM）」「生产任务单」「委外入库」 | 本Session修（可与 P4b-01 一起改） | 「BOM」行内常用，是否保留并加注 | erpnext `zh.po:7095-7096、28401-28402、53328-53329`；zh.po 中另有 28 处字符串用了「作业卡」（如 `:28406`「作业卡分析」），上游本身译名不统一，但单据名是「生产任务单」 |
| P4b-03 | 观察 | app `README.md:133`；上游 `item.json:257-265`、`item.js:145-148、184-187` | 「期初库存」字段在标准物料表单里很可能看不到：json 设了 `hidden: 1`，且 `depends_on` 要求是新单据；`item.js` 只在已保存的单据上 `toggle_display` 放开，新单据在 `:145-148` 就提前 return 了；快速录入也不含该字段，因为没设 `allow_in_quick_entry`。所以 README 说的「填了」，实际路径多半是脚本、API 或数据导入。结论不受影响，避免办法仍然对；只是读者在界面上找不到这个字段，可能以为与己无关，而 S7 脚本造数恰好走这条 | 准确描述上游行为 | 可改为「新建物料时带了『期初库存』（脚本、API 或导入；标准表单默认不显示）」；或保持不改 | 延迟或不修 | 是否值得在浏览器里核一次 | 读码推断，没在浏览器验证；站点上 Item.opening_stock 没有 Property Setter |
| P4b-04 | 观察 | app `README.md:131` | 「作业卡完全不取」只对作业卡带出的**原料行**成立。作业卡成品行（`stock_entry_type.py:333-346`）和工单按已转移物料带出的原料（`stock_entry.py:3699、3723`）只取物料级默认，为空时留空，再由 validate_item 按物料组回退，所以物料组设的费用科目对它们有效。README 写得宽了一些，方向是偏保守，不会让人少设科目 | 准确描述上游行为 | 可改为「作业卡带出的原料行完全不取」 | 延迟或不修（或并入 P4b-01 一起改） | — | `stock_entry_type.py:291-346`；`stock_entry.py:851-852、2726、3699-3726` |

## 交接摘要

- FD-083 R18 指出的三处都已改对：其他出库不再被排除；物料组挡不住 BOM 和作业卡原料行；补了物料「期初库存」。四条来源与上游一致，只有「作业卡完全不取」写宽了（P4b-04）。
- 界面词：列入当场修清单的四个词都对上了 zh.po；「作业卡」「BOM」「委外收货」三个不是界面词（P4b-02）。
- 主要问题在避免办法（P4b-01）：挡不住作业卡原料行和委外损失；「改用库存调账」没说差异科目，脚本造数仍落 1901，界面默认还会取到损益类 Temporary 科目，然后被校验拦下。和 R17 P5-03 的「取到 9999」结论相反，需主会话或收口裁定。
- 月末结转条与 `closing.py:92-128` 一致，标了草案。
- 跨片：本片依赖 R18 Part4 的定位；P4b-01 ② 涉及科目表 Temporary 标注（分片中归科目表或安装那片的可交叉看）。

## 盲区自述

- 没实跑 `get_difference_account`，也没在界面上新建期初库存调账；P4b-01 的「取到 5711072」是读码加 SELECT 排序推断，假设 `frappe.db.get_value` 走 `query.py` 非兼容分支的默认 desc。
- 没在浏览器看物料表单（P4b-03）。
- 没查 Material Transfer、Repack、Disassemble 等其它用途在 1901 上留下的借贷对冲行，也没查 BOM 生产时是否净额为零（成本中心不同时可能不抵消）。
- 没查 Purchase Receipt、Delivery Note 等非库存凭证路径是否在别处取 `stock_adjustment_account`。grep 全仓非测试代码只有上表这几处，外加 `accounts/utils.py:1910` 的 `get_journal_entry`；后者是库存科目与总账对平的工具，按调用方传入的科目记账，没深查。
- 18 个损益科目标为 Temporary 是否另有用途（如纳税调整标记），没追溯来源。
