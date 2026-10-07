# F 复核分片报告 · 片 5（对象：R6 开发方案 SL-011～012／TS-017～020 范围内的 R9 修复 / 审核标准：R9 F 审核报告 FD-007②、FD-009、FD-013、FD-036 的问题描述与建议 ＋ R6 C开发方案 ＋ R6 C讨论记录 DEC-023～028）

**轮次**：P1-S5-R10｜**步骤**：F 复核分片 5｜**日期**：2026-10-07｜**执行者**：Claude 子 Agent（只读）
**依据**：[R9 F审核报告](../R09-F审核/P1-S5-R9-F审核报告.md)（FD-007、009、013、033、034、036 行，当场修清单 #2／#9／#21，裁决去向表）；[R9 Part5](../R09-F审核/P1-S5-R9-F审核报告-Part5.md)（全文）；[R9 SB修复回执](../R09-F审核/P1-S5-R9-SB修复回执.md)（全文）；[R6 C开发方案](../R06-开发方案/P1-S5-R6-C开发方案.md)（§接口、任务 17～20、SL-011／012）；[R6 C讨论记录](../R06-开发方案/P1-S5-R6-C讨论记录.md)（DEC-027 行、F7～F10、LG-014）；`docs/开发守则.md`「删公司要清的子表行」；`docs/业务规则.md`
**被审范围**：`frappe_china` `4b21aae..9d53d39` 中的 `accounting/hr.py`、`accounting/company.py`、`README.md`「已知限制」报销与删公司两条、`tests/test_company_hr_lifecycle.py`；两站只读查询

## 覆盖自证

- **读全的**：本片通用说明；R9 Part5 全文；R9 收口报告的覆盖、验证门、问题清单、当场修清单、状态值、复核建议各节；SB 回执全文；`hr.py`（HEAD 全文，1-141）、`company.py` 全文（1-222）；`test_company_hr_lifecycle.py` 1-360；`hooks.py` 155-162；`frappe_china` 两次提交里 `README.md`、`company.py`、`hr.py`、三个测试文件的 diff。
- **按需读的**：R6 方案的 §接口伪代码、任务 17／19／20、SL-011／012 原文；R6 讨论记录的 DEC-027、F7～F10、LG-014；R7 D 回执头部（核 FD-034）。
- **对照的上游**：`frappe/__init__.py` `logger()`；`frappe/utils/logger.py` `get_logger`、`default_log_level`；`frappe/utils/local.py` `LocalProxy.__setattr__`／`__delattr__`（判 `patch.object(hr.frappe.db, …)` 打到哪）；`frappe/database/database.py` `count`／`delete` 签名；`frappe/model/delete_doc.py`（`on_trash` 先于链接检查、`add_to_deleted_document`、`delete_permanently` 缺省 `False`）；`hrms/hooks.py` Company 钩子、`hrms/overrides/company.py` `handle_linked_docs`、`set_expense_claim_type_accounts`；`erpnext` `Company.on_trash`、`Account.on_trash`；`nestedset.on_trash`。
- **静态检查**：全 app grep `db.exists("DocType"`；写了一个 AST 扫描脚本，对导入了 `from frappe import _` 的 21 个模块（`frappe_china/` 全部 `.py`，含测试）查 `_` 的一切局部绑定（赋值、解包、循环变量、形参、`except … as _`、函数内 import）。`docker/` 下的脚本同扫。
- **只读查询**（容器 `erx001-frappe-1`）：两站 `Tax Rule`／`Expense Claim Account` 指向不存在公司的行、`Expense Claim Account` 指向不存在科目的行、`_FCT`／`FCT` 前缀公司数、公司列表；两站 `information_schema` 取带 `company` 列的基表（各 194 张）后逐表查悬空（SQL 从标准输入送入，首尾加哨兵行确认 194 条语句都执行了）；两站报销类型名与报销行科目号；两站 `frappe.get_doc_hooks()` 的 Company 项；在 `docker exec` 环境里只读打印 `frappe.logger("frappe_china")` 的有效级别与处理器；`logs/frappe_china.log` 与站点日志的大小、时间；容器里 web／worker／schedule 进程的 `DEV_SERVER` 环境变量；测试站 `tabDeleted Document` 中被删报销通用科目的记录。
- **变异期间的处理**：主会话变异期间（`hr.py`、`install.py`、`realtime_check.py` 被临时改动），这三个文件一律以 `git show HEAD:` 为准。本报告的 `hr.py` 行号都按 HEAD 核过（工作区与 HEAD 的 md5 不同，`git status` 为空，是换行符差异）。
- **跳过**：不跑测试、不做变异（硬约束）；没有构造「用户手建无号科目被删」的写站场景；FD-008 的 `is_cn_company` 接 dict 行为归片 1，本片只核了它对 SL-011／012 的连带影响。临时脚本与查询文件都放在 `.claude/r10-tmp/`，用完已删。

## R9 已修项复核

| R9 项 | 修于（当场／SB） | 定位（文件:行） | 落地 | 生效 | 原问题消失 | 说明 |
|---|---|---|---|---|---|---|
| FD-007② | 当场 | `hr.py:135-141`；`test_company_hr_lifecycle.py:163-180`、`:96-104` | ✅ | ✅ | ✅ | **判据一致**：全 app `db.exists("DocType"` 只有 `hr.py:31`、`:86`、`:137` 三处，三处都查 `EXPENSE_CLAIM_TYPE_DOCTYPE`（另两处在测试的 `setUpClass`，也查 `Expense Claim Type`）。**断言有判别力**：被测函数以位置参数调用 `frappe.db.count(EXPENSE_CLAIM_ACCOUNT_DOCTYPE, {...})`、`frappe.db.delete(EXPENSE_CLAIM_ACCOUNT_DOCTYPE, {...})`（`:139-140`），过滤 `c.args[:1] == (EXPENSE_CLAIM_ACCOUNT,)` 能抓到。`exists_without_hrms` 只让 `exists("DocType", "Expense Claim Type")` 答否，其余照查；所以去掉守卫，或守卫改回查 `Expense Claim Account`，都会走到 `count`，`touched` 非空，断言变红。`patch.object(hr.frappe.db, …)` 经 `LocalProxy.__setattr__` 落在真实 db 实例上，是全局生效的，块内 `delete_doc("Company")` 走 `on_trash` 时同样被观测。关键字参数漏判只是潜在缺口，见 P5-03 |
| FD-007②（顺序） | — | `delete_doc.py:173-183`；两站 `get_doc_hooks()` | — | ✅ | — | 删公司时，先跑 ERPNext 控制器 `Company.on_trash`（裸 SQL 删 Account 等，不做链接检查），再按钩子顺序跑 `hrms…handle_linked_docs`、`frappe_china…on_trash`，之后才检查链接。两站实测钩子顺序一致。本轮只换了守卫查的 DocType，顺序与 R9 读码结论相同，没有连带影响 |
| FD-009 | SB | `hr.py:114`、`:118`、`:124`、`:126-128`；`test_company_hr_lifecycle.py:304-321`；`README.md:144` | ✅ | ⚠️ | ⚠️ | **测试打得中**：`logger = frappe.logger("frappe_china")` 在函数体内、每次调用时才取（`:114`），不是模块级。`patch.object(hr.frappe, "logger")` 替换的是 `frappe` 模块属性，所以被测函数拿到的是 `logger.return_value`，`.warning` 的调用都被记录。删掉 `:128` 后，删除分支一条 warning 都不发，本例又不走保留分支，调用列表为空，断言失败。SB「变异下失败、列表为 `[]`」在读码上说得通。**新测试走对了那条 join**：手建科目不填 `account_number`（NULL），`ifnull(acc.account_number,'')=''` 命中；报销行 `Travel` 先改指向它，join 条件 `acc.name = eca.default_account` 成立。结果是改挂到 `5602130`，无 GL、无链接，于是被删。**措辞**：保留分支 `Keeping generic expense claim account %s: …`，删除分支 `Deleted generic expense claim account %s after repointing its rows`，都带科目名。README「删掉或因已有凭证、链接而保留都记 warning」与代码分支相符。**不足**：这条 warning 只有设了 `DEV_SERVER` 的进程才会写进日志文件，`bench` 命令行、测试、生产部署里都被级别过滤掉了，见 P5-01。另外，删除本来就留了 `Deleted Document`，R9 说的「不留痕迹」原本就不完全成立，见 P5-01 |
| FD-036 | 当场 | `company.py:39-40` | ✅ | ✅ | ✅ | 循环变量已改为 `_attempt`，加了注释。AST 扫描 `frappe_china/` 下导入了 `_` 的 21 个模块，**没有任何**对 `_` 的局部绑定（赋值、解包、`for`、形参、`except as`、函数内 import 都查了）。`closing.py:406` 只是一条说明不用 `_, end =` 的注释。`docker/` 下的脚本没有导入 `_`，无命中 |
| FD-013 | 当场（数据） | 两站 `tabTax Rule` 等；`frappe-bench/logs/s5-r9-fd013-taxrule-backup.tsv` | ✅ | — | ✅（数据）／⚠️（建议后半） | 测试站：`Tax Rule` 悬空 0，`Expense Claim Account` 悬空（按公司）0，按科目 0。查询时公司只有 `_Test Company`、`_Test Company 1`、`_FCT CRM 验证`，没有测试中途的临时公司。194 张带 `company` 列的表逐表泛查：**0 行悬空**。演示站同查，全为 0（公司只有华东弹簧有限公司）。备份文件在，27 行（表头加 26 行）。R9 建议的后半句「以后的残留核对加上 `Tax Rule`」，在主仓库与 app 的两次提交里都没有落到任何文档或检查里，见 P5-02 |

**一句话**：5 行中，FD-007②（含顺序核查）、FD-036 三层都成立；FD-013 数据已清，但建议后半句没落地；FD-009 代码与测试成立，但 warning 在默认级别下会被吞掉。

## 延迟／不做项登记核对

| R9 项 | 裁决去向 | 登记位置 | 描述与实情一致否 | 说明 |
|---|---|---|---|---|
| FD-033 | 不做 | R9 收口报告问题清单第 184 行、裁决去向表「不做（7）」 | 一致 | 裁决栏写「LG-014 的答案（两站报销类型都是英文名）留档于本报告」。本轮复查两站报销类型都是 `Calls,Food,Medical,Others,Travel`，与留档说法相符。R6 讨论记录 LG-014 仍是「待验证」，这是「不做」的应有结果，不算漏改。代码 `hr.py:23-25` 没动，风险描述仍然成立 |
| FD-034 | 不做 | 同上，第 185 行 | 一致 | R7 D 回执头部仍只写 `8433978`，与「不做」相符 |

## 业务规则合规核

| 规则条款 | 本轮改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 间接（报销改挂目标、无号科目删除） | 合规（规则未经专家确认） | 改挂目标仍按 `account_number` 取本表科目；本轮只加了日志与 README 说明，没改映射与判定 |
| BR-002 报表构成 | 否 | 不涉及 | — |
| BR-003 增值税税率 | 否 | 不涉及 | 删 `Tax Rule` 只在删公司时发生，本轮没改 |
| BR-004 增值税月末结转 | 否 | 不涉及 | — |
| BR-005 附加税 | 否 | 不涉及 | — |
| BR-006 资产负债表平衡 | 否 | 不涉及 | — |
| BR-007 价税分离 | 否 | 不涉及 | — |
| DEC-028 兜底 `5602250` | 否（README 原句保留） | 仍为草案·待领域专家确认 | README:144 仍标「待领域专家确认」 |

## 集成点登记（交接摘要）

- **本片依赖**
  - 片 1：FD-008 改后的 `backfill_cn_expense_claim_accounts` 把 `get_all` 返回的 dict 交给 `is_cn_company`（`hr.py:75-80`）。它和 SL-012 共用 `set_cn_expense_claim_accounts`，本片没复核 dict 分支，归片 1。`hr.py` 现在在模块导入时从 `company` 导入 `is_cn_company`，而 `company.py` 对 `hr` 的导入都在函数体内，不构成循环导入（读码）。
  - 主会话：FD-007② 断言判别力的实测（见第 ⑤ 节 1、2）。
- **本片暴露**
  - `repoint_generic_expense_claim_accounts` 的日志与留痕：warning 只在 `DEV_SERVER` 进程（容器里 `bench start` 拉起的 web／worker／schedule）写进 `logs/frappe_china.log` 与站点 `logs/frappe_china.log`；`docker exec … bench …`、`run-tests`、`after_app_install` 下级别是 ERROR，warning 被丢弃。被删科目在 `tabDeleted Document` 有记录（`delete_permanently` 缺省为 `False`），可以从桌面恢复。
  - 两站：194 张带 `company` 列的表无悬空行，可作为本轮之后的基线（测试站查询时只有 3 家公司）。
  - 别片若写「删公司残留核对」类检查，口径目前只在 R6 TS-020 第 2 步里（只查报销行），`Tax Rule` 没有写进任何常驻文档。

## 自证复核

| 被审产物声称（R9 报告／SB 回执／文档） | 实际复核 | 一致否 |
|---|---|---|
| R9 当场修清单 #9：`hr.py:134` 守卫改查 `Expense Claim Type`，测试 `:167-177` 断言不发报销表语句 | HEAD 守卫在 `:137`（SB 在同文件前面加了几行，行号后移）；测试断言在 `:168-177` | 一致（行号随 SB 偏移） |
| R9 当场修清单 #2：删 26 行，删后全库悬空 `Tax Rule` 为 0 | 两站现为 0；194 表泛查 0；备份 27 行 | 一致 |
| R9 当场修清单 #21：`company.py:39-40` 改名 | 一致；全 app 无同形遮蔽 | 一致 |
| SB 回执：`hr.py:125-128` 删除分支加 `logger.warning` | HEAD 在 `:126-128`（注释 `:126`、`append` `:127`、`warning` `:128`） | 一致 |
| SB 回执：变异删 warning 一行后 `test_sl012_6_1b` 失败，`warning` 列表为 `[]` | 读码成立：`logger` 每次调用时取、patch 打在 `frappe` 模块上；本例不走保留分支 | 读码一致（未亲自复现） |
| SB 回执／README:144：删掉或保留都「记 warning 日志」 | 代码确实调了 `warning`。但日志级别取 `frappe.log_level or default_log_level`，没设 `DEV_SERVER` 时是 ERROR。`docker exec` 环境实测有效级别 ERROR、`isEnabledFor(WARNING)=False`；两份 `frappe_china.log` 都是 0 字节、最后修改于 10-06 21:07，可 SB 全量回归（10-07 21:39 结束）跑过的 `test_sl012_3` 走的是真实 logger、会删通用科目 | **部分一致**（P5-01） |
| SB 回执：README 写明「判通用只看无号」「不要指向无号科目」「会被删」「记 warning」四点 | 四点都在 README:144；与 DEC-027 原文「有凭证或仍被引用则保留并告警」及失效条件「中式公司出现合法的无号明细科目被用作报销科目时」相符。删除也告警是 FD-009 裁决新加的，不冲突 | 一致 |
| R9 FD-009 问题描述：「删掉且不留日志」 | `frappe.delete_doc("Account", …)` 没传 `delete_permanently`，缺省 `False`，会写一条 `Deleted Document`（`delete_doc.py:225-226`、`:237-247`），可以恢复。R9 的「不留痕迹」说法过重 | 不一致（对 R9 原判的修正，见 P5-01） |
| R9 FD-013 建议：「以后的残留核对加上 `Tax Rule`」 | `git diff 2fb2641..d7b89d6 -- docs`（R9 报告目录除外）与 app diff 里都没有新增 `Tax Rule`、残留、悬空相关文字；`开发守则.md:91` 仍只点名 `Expense Claim Account` | **不一致**（P5-02） |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准／意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P5-01 | 低 | `hr.py:114`、`:128`；`frappe/utils/logger.py:12`、`:80`；`README.md:144` | FD-009 加的 warning 只在设了 `DEV_SERVER` 的进程里落盘。Frappe logger 级别取 `frappe.log_level or default_log_level`，`default_log_level` 在没有 `DEV_SERVER` 时是 ERROR。证据：① 在 `docker exec` 环境（`DEV_SERVER` 为空）里只读取 `frappe.logger("frappe_china")`，有效级别 ERROR，`isEnabledFor(WARNING)` 为假；② `logs/frappe_china.log` 与 `sites/test.localhost/logs/frappe_china.log` 都是 0 字节，修改时间 10-06 21:07，可 SB 全量回归（10-07 21:39）跑过的 `test_sl012_3` 用真实 logger 删了通用科目；③ 容器里 `bench start` 拉起的 web／worker／schedule 进程都带 `DEV_SERVER=true`，所以演示站从桌面保存公司时日志能写进去。结果是：命令行、`after_app_install`、测试，以及任何生产部署（不设 `DEV_SERVER`）里，「记 warning 日志」都不成立。另外，删除本来就写了 `Deleted Document`（`delete_permanently` 缺省 `False`），这才是在任何环境下都在的痕迹，README 没提 | 开发守则「静默失败自成一类」；FD-009「删了须留痕」的意图；README 说法要与实情一致 | (a) README:144 把「记 warning 日志」改成「被删科目留在『已删除文档』里可恢复；开发模式下另记 warning 日志」；或 (b) 删除分支改用 `frappe.log_error`（写 Error Log，所有环境都在），或在 `delete_doc` 之后以返回值／`msgprint` 告诉保存公司的人。只改文档就是 (a) | 新Session修 | 只改 README 措辞 (a)，还是换留痕方式 (b) | 待裁决 |
| P5-02 | 观察 | `docs/开发守则.md:91`；R6 方案 TS-020 第 2 步；R9 FD-013 建议后半 | FD-013 建议的「以后的残留核对加上 `Tax Rule`」没有落地：R9 当场修只做了删数据（当场修清单 #2）。删公司残留核对的唯一书面口径仍是 R6 TS-020 的那条 SQL（只查报销行），开发守则「删公司要清的子表行」一节也只点名 `Expense Claim Account`，没提 `Tax Rule`，也没提「全库带 `company` 列的表泛查」这一招。下次有人强删公司，同类残留仍然只能靠审核偶然发现 | R9 FD-013 建议；IT-002「不留悬空行」 | 在开发守则那一节补半句：清理对象还有中式公司的 `Tax Rule`（DEC-025）；残留核对用「`information_schema` 取带 `company` 列的表逐表左连 `tabCompany`」泛查。写入前按常驻文件契约判定写哪里 | 本Session修 | 写进开发守则，还是只算 R9 裁决时有意不做后半句 | 待裁决 |
| P5-03 | 观察 | `test_company_hr_lifecycle.py:176` | `touched` 只认位置参数（`c.args[:1]`）。被测函数现在用位置参数，所以断言**当前**有判别力。如果以后把 `clear_company_expense_claim_accounts` 改写成 `frappe.db.delete(doctype=…)`，或改用 `frappe.qb`、`frappe.db.sql`，守卫失效时这条断言也照样过。同文件 `:208` 的 SL-011 ⑤③ 已经兼顾了 `kwargs.get("doctype")`，两处写法不一致 | 开发守则「判据必须能区分」（防回归的强度） | 过滤改为同时认 `kwargs` 的 `doctype`／`dt`；或换成更直接的断言：块内先插一行该公司的报销行，断言 `clear…` 返回 0 且该行仍在 | 延迟或不修 | — | 待裁决 |

## 本片盲区自述

- **没有实跑**：FD-007② 与 FD-009 的判别力都是读码判断。FD-009 的变异采信 SB 回执；FD-007② 的 M2 变异，R9 时全绿，修后有没有重跑，本片不知道（见交回主会话 ⑤）。
- **P5-01 的证据**：日志级别是在 `docker exec` 起的 python 里只读打印的，加上日志文件为空作旁证。没有在 web 进程里实际触发一次删除去看文件里是否出现那行（要写站）。
- **没往这些方向找**：`repoint` 的 join 不限 `is_group`。如果报销行指向的是一个无号**组**科目，`delete_doc` 会抛 `NestedSetChildExistsError` 之类的非 `LinkExistsError` 异常，导致保存公司失败。这一段本轮没改，R9 已审过，本片只记为盲区，未核实 HRMS 是否从源头拦住组科目。保留分支里 `frappe.throw(…, LinkExistsError)` 被捕获后，消息会不会仍留在 `message_log`、在界面弹给用户，没有核。
- **FD-013 泛查的时间点**：查询时测试站没有临时公司，但主会话随后在跑变异，变异期间新建、删除的公司没在本片查询的时间窗里。
- **范围外**：FD-008（`is_cn_company` 接 dict、backfill）归片 1，本片只确认了导入关系。
