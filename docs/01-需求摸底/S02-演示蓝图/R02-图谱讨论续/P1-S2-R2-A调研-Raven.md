# P1-S2-R2 调研报告：Raven（Frappe 生态聊天 App，含 AI）

**调查者**：Claude（主 Session 亲自查证）
**日期**：2026-09-23
**克隆位置**：`Reference/raven`（`--depth 1`，`.gitignore` 已排除）

> **⚠ 本报告的产出方式与同批其它报告不同。** 原派出的子 Agent 完成调查后**两次在"写报告"这一步 API 超时中断**，报告始终未落盘。第二次续跑失败后判定其上下文过重、再试仍会断，故由主 Session 依据本地克隆**亲自重查并书写**。
>
> **好处**：本报告全部结论均为主 Session 直接读码所得，每条都有可复现命令或 `文件:行号`，不存在"采信 Agent 转述"的衰减。
> **代价**：覆盖面窄于原计划——前端挂载链路与 realtime 细节只做到判定级，未逐环展开（见 §6）。

---

## 一、开源结论

| 项 | 值 | 依据 |
|---|---|---|
| 仓库 | `github.com/The-Commit-Company/Raven` | 克隆成功 |
| **许可证** | **AGPL-3.0** | 打开真实 `LICENSE` 文件首二行实读：`GNU AFFERO GENERAL PUBLIC LICENSE / Version 3, 19 November 2007`。**未发现 Flow 那种"文件头写 MIT"的矛盾** |
| 作者 | `Frappe <support@frappe.io>`（官方邮箱） | `pyproject.toml:3-5` |
| 定位 | "Simple, open source messaging tool" | `pyproject.toml:6` |

**与 Flow 的许可证对照**：两者同为 AGPL-3.0。但 Flow 有 51 个 `.py` 文件头写 `License: MIT` 的矛盾，Raven 无此问题；且 Raven 的 publisher 是官方邮箱，Flow 是个人名（`Shrihari Mahabal`）。**Raven 的官方支持信号明显强于 Flow。**

---

## 二、依赖与 v16 兼容

| 项 | 值 | 依据 |
|---|---|---|
| **frappe 版本要求** | **`>=15.0.0,<=17.0.0-dev`** —— **覆盖我们的 16.34.0** ✅ | `pyproject.toml:37-38`（`[tool.bench.frappe-dependencies]`） |
| 是否依赖 ERPNext | **不依赖**（无 `required_apps`，`hooks.py` 内无该键） | `grep required_apps raven/hooks.py` 零命中 |
| Python | `>=3.10` —— 与本项目 3.14 兼容 ✅ | `pyproject.toml:7` |
| Python 依赖 | `linkpreview~=0.9.0`、**`openai>=2.30.0`**、`blurhash-python`、**`openai-agents>=0.17.2`**、`markitdown`、`pandas`、**`google-cloud-documentai`** | `pyproject.toml:10-18` |

**⚠ 但"依赖 ERPNext"这件事有个例外**：`doc_events` 里挂了 **`Employee`** 与 **`Department`** 两个 DocType（见 §5），而这两个来自 **hrms**（本项目未装）。即它不强依赖 ERPNext，但对 hrms 的 DocType 有可选集成——未装时那两组 hook 不触发。

---

## 三、AI 能力的实现机制（本次调查重点）

### 3.1 接哪家 LLM —— **可换，且支持本地模型**

**这一条推翻了"Raven 绑定 OpenAI"的初判。** 依据 `raven_settings.json` 的字段实读（Python json 解析）：

| 字段 | 类型 | 含义 |
|---|---|---|
| `enable_ai_integration` | Check | AI 总开关，**默认 0（关）** |
| `enable_openai_services` | Check | OpenAI 服务开关，默认 1 |
| `openai_api_key` | Password | OpenAI 密钥 |
| `openai_organisation_id` / `openai_project_id` | Data | OpenAI 组织与项目 |
| **`enable_local_llm`** | **Check** | **本地 LLM 开关，默认 0** |
| **`local_llm_provider`** | **Select** | **取值 `LM Studio` / `Ollama` / `LocalAI` / `OpenAI Compatible`** |
| **`local_llm_api_url`** | **Data** | **本地 LLM 的 API 地址** |
| `openai_compatible_api_key` | Password | 兼容模式的密钥 |

**分派逻辑实读**（`raven/ai/agents_integration.py:55-90`）：

1. `bot_doc.model_provider == "Local LLM"` 且 `settings.enable_local_llm` 为真 → 走本地分支；
2. 本地分支要求 `local_llm_api_url` 非空，否则 `frappe.throw`；
3. **密钥处理**：`OpenAI Compatible` 取 `openai_compatible_api_key`，**缺省填字面量 `"sk-key"`**；其余三种（LM Studio / Ollama / LocalAI）**直接填 `"not-needed"`**，代码注释原文：`LM Studio, Ollama, LocalAI don't require API key`；
4. 客户端仍用 `AsyncOpenAI`，但 `base_url` 指向 `local_llm_api_url`；
5. **端点差异**：本地走 `OpenAIProvider(use_responses=False)`（强制 chat/completions），OpenAI 走 `use_responses=True`（走 `/v1/responses`）。

**故结论**：**能换成国内模型或 Claude**——只要该模型提供 OpenAI 兼容端点（DeepSeek / 通义 / 智谱均提供；Claude 需经兼容层如 LiteLLM / one-api 代理）。选 `OpenAI Compatible` 并填 `local_llm_api_url` 即可。

**⚠ 但换成本地/兼容模型有能力损失**（`agents_integration.py:350-375` 实读）：`model_provider == "Local LLM"` 时会**过滤掉七类 hosted 工具**——`CodeInterpreterTool`、`FileSearchTool`、`WebSearchTool`、`ComputerTool`、**`HostedMCPTool`**、`ImageGenerationTool`、`LocalShellTool`，并对每个被跳过的工具写 `frappe.log_error`。**即走本地模型时，MCP、联网搜索、代码解释器、文件检索全部失效**，只剩自定义函数调用。

### 3.2 MCP 支持 —— **有，但仅限 OpenAI 通道**

`grep -rni "mcp"` 全仓实际命中**仅两处**，均在 `raven/ai/agents_integration.py`：`:19` 从 openai-agents SDK `import HostedMCPTool`，`:359` 把它列入本地模型要过滤掉的类型。

**故**：MCP 能力来自 `openai-agents` SDK 的 `HostedMCPTool`，**不是 Raven 自建**；且**走本地模型时被过滤掉**。本项目若想用 MCP，须走 OpenAI 官方通道（即必须联外网 + 付费 key）。

### 3.3 AI 怎么真正操作 ERPNext 数据

**函数类型共 18 种**（`raven_ai_function.json` 的 `type` 字段 options 实读）：

`Get Document` / `Get Multiple Documents` / `Get List` / **`Create Document`** / `Create Multiple Documents` / **`Update Document`** / `Update Multiple Documents` / **`Delete Document`** / `Delete Multiple Documents` / **`Submit Document`** / **`Cancel Document`** / `Get Amended Document` / **`Custom Function`** / `Send Message` / `Attach File to Document` / `Get Report Result` / `Get Value` / `Set Value`

**即读、建、改、删、提交、撤销、跑报表、跑自定义函数全覆盖。**

**"说一句话 → 真的建出一张销售订单"的调用链**（`raven/ai/functions.py` 实读）：

| 环 | 实现 | 位置 |
|---|---|---|
| 建单 | `doc = frappe.get_doc({"doctype": doctype, **data})` → `doc.insert()` | `functions.py:24-43` |
| 默认值注入 | 遍历 `function.parameters`，`do_not_ask_ai` 为真的参数**由配置强制填入、不交给 AI 决定**；AI 未提供的参数用 `default_value` 兜底 | `functions.py:29-41` |
| 提交 | `frappe.get_doc(doctype, id)` → `doc.submit()` | `functions.py:110-121` |
| 撤销 | 同上 → `doc.cancel()` | `functions.py:123-134` |

### 3.4 权限模型 —— **走当前用户权限，未发现绕过**（本节是最关键的一条）

| 查证 | 结果 |
|---|---|
| `grep -rn "ignore_permissions" raven/ai/` | **零命中** |
| 建单方式 | `doc.insert()`，**未传 `ignore_permissions=True`** —— 故走 Frappe 标准权限校验 |
| 执行身份 | `frappe.session.user`（`handler.py:311` 以 `args.get("user", frappe.session.user)`、`:396` `frappe.get_cached_doc("User", frappe.session.user)`、`:419`） |

**故结论**：**AI 以"发起对话的那个用户"的身份执行，权限不放宽。** 该用户建不了销售订单，AI 替他也建不了。这对演示是好消息（不会出现"AI 越权"的尴尬），但也意味着**演示账号的角色权限必须先配好**。

**⚠ 未查实**：`Custom Function` 类型执行的是什么、有没有绕过权限的口子——该类型指向用户自定义的白名单方法，其安全性取决于被指向的那个方法本身。**本次未展开查。**

---

## 四、realtime 与额外进程

| 项 | 结果 | 依据 |
|---|---|---|
| 是否依赖 socketio | **是，重度依赖** —— `publish_realtime` 全仓 **46 处**调用 | `grep -rn "publish_realtime" --include=*.py raven/ \| wc -l` = 46 |
| 是否另起独立进程 | **否** —— `realtime/` 目录下只有 **一个文件** `handlers.js`，无 `package.json`、无独立服务入口。它是挂进 frappe 自带 socketio 服务的 handler，不是新进程 | `ls realtime/` |
| 是否另需新端口 | **否**（推断）——复用 frappe 的 socketio | 由上一条推断，**未实测** |
| 推送通知 | 另有 `push_notification_api_key` / `push_notification_api_secret` / `vapid_public_key` 三个字段，指向 frappe 的 notification relay 服务。**该服务是可选的**（不配则无手机推送） | `raven_settings.json` 字段实读 |

**⚠ 对本项目的具体含义**：本项目有一条已记录的坑——站点 `socketio_port` 必须与 compose 端口映射同号（用 9100，因 9000 落在 Windows 保留段），且 **realtime 断连是静默的**（不报错，只是界面不再自动更新）。Raven 有 46 处 `publish_realtime`，**故它是本项目 realtime 链路是否健康的一个高敏感放大器**：若 socketio 再次错位，Raven 的表现会是"消息发出去了但对方看不到"——**在客户面前这比界面不刷新更难看**。演示前必须实证 realtime 通（本项目已有两标签页验法）。

---

## 五、装上去的代价与风险

### 5.1 ⚠ `doc_events` 对 `"*"` 挂了五个写事件（与 Flow 同型风险）

`raven/hooks.py:131` 起实读：

```
doc_events = {
    "*": {
        "after_insert" / "on_update" / "on_trash" / "on_cancel" / "on_submit"
            → raven.raven_integrations.doctype.raven_document_notification
              .raven_document_notification.run_document_notification
    },
    "User":       { after_insert / on_update / on_trash → raven_user 同步 }
    "Department": { after_insert / on_update / on_trash → controllers.department }
    "Employee":   { after_insert / on_update / on_trash → controllers.employee }
}
```

**即 Raven 与 Flow 一样，全库每一次写操作都过它一道。** 两者若同时安装，**每次写操作要过两道**。

**但两者的风险等级不同**：Flow 零 release / 零 tag / 单 `develop` 分支，无可回退版本点；**Raven 是官方邮箱 publisher、frappe 依赖声明覆盖 v16**。故 Raven 的 `"*"` hook 可接受度高于 Flow。

### 5.2 其它 hook

| 项 | 结果 |
|---|---|
| `override_whitelisted_methods` | **无**（`hooks.py:204` 该键被注释掉） |
| `override_doctype_class` | **无**（`:123` 被注释掉） |
| `after_install` | **有** —— `raven.install.after_install`（**本次未展开查它写什么**） |
| `website_route_rules` | **有** —— `:258`。即它确实是独立 SPA 挂路由形态（与 Flow 的"注入 desk 面板"不同） |
| `app_include_css/js` | **有** —— `raven.bundle.css` / `raven.bundle.js`（`:17`/`:20`），故它**既挂独立路由、又往 desk 注入** |

**对 `regional_overrides` 末位风险的相关性**：Raven **无** `override_whitelisted_methods`、**无** `regional_overrides`，故它本身不与本项目的中国本地化覆盖直接冲突。**但"安装顺序是否把自有 app 挤出末位"这个问题不由 Raven 自身决定**——由 `frappe.get_hooks()` 的合并顺序决定，该问题属接入机制那一路，此处不作结论。

---

## 六、拿不准 / 未能验证的

**全部结论均为静态读码，无一条实跑。** 具体未查实的：

1. **`after_install` 写入什么** —— 未展开。装在已有数据的站点（1 公司 `华东弹簧` / 95 科目 / 已有销售订单）上的实际影响未知。
2. **`Custom Function` 类型的安全边界** —— 见 §3.4 末。
3. **前端挂载链路未逐环展开** —— 只确认 `website_route_rules:258` 存在与前端在 `apps/web`（`pyproject.toml:40` 的 `[tool.bench.assets] build_dir`），**未查**：谁响应 `/raven`、加载哪些资源、怎么认证、怎么取数。这块与 CRM 那路重叠，留给接入机制报告。
4. **是否另需新端口** —— §4 那条是推断，未实测。
5. **本地模型实际可用性** —— 代码支持不等于跑得通。`use_responses=False` 的 chat/completions 路径在 DeepSeek/通义等国内端点上是否真能驱动 function calling，**必须实跑才知道**。这是最该先验的一条。
6. **中文翻译覆盖情况** —— 未查 `locale/`。
7. 未核 stars / 最后提交 / release 列表（原 Agent 报告缺失，主 Session 未补）。

---

## 七、对本项目的直接影响

**一句话**：**能拿它在客户面前演示 AI，且比 Flow 更适合演示**——因为它有官方支持信号、许可证无矛盾、frappe 依赖明确覆盖 v16，而且 **AI 能接国内模型（OpenAI 兼容端点），不必依赖出网与付费密钥**。

### 做这场演示的硬前置条件清单

| # | 条件 | 说明 | 绕不绕得过 |
|---|---|---|---|
| 1 | **一个 OpenAI 兼容的模型端点** | 二选一：① 本地跑 Ollama / LM Studio（免费、免出网、但要本机算力）；② 用国内云端点 DeepSeek/通义/智谱（要 key、要出网但不必翻墙、便宜） | 绕不过 |
| 2 | **`enable_ai_integration` 与 `enable_local_llm` 两个开关都要开** | 两者默认均为 0 | 绕不过 |
| 3 | **Bot 的 `model_provider` 要设为 `Local LLM`** | 否则走 OpenAI 分支、要求 `openai_api_key` 否则 `frappe.throw` | 绕不过 |
| 4 | **演示账号的角色权限必须先配好** | AI 以发起者身份执行、不放宽权限（§3.4） | 绕不过 |
| 5 | **realtime 必须实证通** | 46 处 `publish_realtime`；断连静默，症状是"消息发了对方看不到" | 绕不过 |
| 6 | **接受 MCP / 联网搜索 / 代码解释器失效** | 走本地模型时这七类 hosted 工具被过滤（§3.1） | 只能靠改用 OpenAI 官方通道换回，那就要出网 + 付费 |
| 7 | **要先实跑验证国内端点的 function calling** | §6 第 5 条。**这是最大的未知**——若国内端点在 `use_responses=False` 路径下 function calling 不稳，演示"AI 建出一张销售订单"就不成立 | 绕不过，且**必须在承诺演示内容之前验** |
| 8 | 无需额外进程 / 无需新端口 | §4。这是相对好的一面 | — |

### 最主要的一个反对理由

**`doc_events` 对 `"*"` 挂五个写事件**（§5.1）。它与 Flow 同型；若两者同装，全库每次写操作过两道。本项目正处在"要改服务端修正工艺损耗与费用科目"的阶段，**写路径上多两层第三方 hook 会让问题定位变难**。

### 与 Flow 的取舍建议（供裁决参考）

| 维度 | Raven | Flow |
|---|---|---|
| 官方支持信号 | **强**（官方邮箱） | 弱（个人 publisher、零 release） |
| 许可证 | AGPL-3.0，无矛盾 | AGPL-3.0，**但 51 个 py 头写 MIT** |
| 版本可锁定 | frappe 依赖声明覆盖 v16 | **零 release 零 tag 单 develop 分支** |
| 能否离线 | **能**（Ollama/LM Studio/兼容端点） | **能**（litellm，同样支持 Ollama） |
| 接入形态 | 独立 SPA 挂路由 + desk 注入 | **仅** desk 注入滑出面板 |
| `"*"` 写事件 hook | **有**（5 个） | **有**（5 个） |
| 额外环境改造 | 无需新进程/端口 | **需改 Docker 镜像**（`libgl1`/`libglib2.0-0`） |
| 演示形态 | 聊天室里对话式驱动业务 | desk 内 `ctrl+i` 唤起助手 |

**Claude 的倾向**：**若只装一个，装 Raven。** 理由是官方支持信号、无许可证矛盾、无需改 Docker 镜像三项占优，而 AI 能力两者都能离线。**但"演示形态"这一项要由用户定**——聊天式（Raven）与 desk 内助手式（Flow）给客户的观感不同，这是产品判断而非技术判断。
