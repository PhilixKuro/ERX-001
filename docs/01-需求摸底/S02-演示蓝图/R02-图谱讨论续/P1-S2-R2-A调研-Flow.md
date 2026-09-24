# P1-S2-R2-A 调研：Flow

调研日期：2026-09-23
本项目环境：Frappe 16.34.0 + ERPNext 16.35.0
克隆位置：`D:\ERX-001\Reference\flow`（源自 `github.com/frappe/flow_client`，浅克隆）

---

## 一、「Flow 是什么」的认定过程

### 1.1 候选清单与逐条证据

| # | 候选 | 证据 | 结论 |
|---|---|---|---|
| 1 | `frappe/flow` 仓库 | GitHub API `/repos/frappe/flow` → `Not Found`；`curl -I https://github.com/frappe/flow` → **HTTP 404**；`git ls-remote` → `Repository not found`。分页取全 `frappe` 组织公开仓库（5 页 × 100），**列表中无 `flow`**，只有 `flow_client` | **不可直接访问**（见 1.2 的推断） |
| 2 | `frappe/flow_client` | API：描述 `Frappe Flow — native AI agents, tools, and triggers for Frappe`；AGPL-3.0；73 star / 32 fork / 20 open issue；默认分支 `develop`；创建 2026-06-02，最后 push 2026-08-12。克隆后 `flow/hooks.py:1` 为 `app_name = "flow"`，README 标题即 `# Flow` | **✅ 认定对象** |
| 3 | Frappe 官方「Frappe Flow」产品页 | `https://frappe.io/flow` → **404**。抓取 `frappe.io/products` 全文：`overflow` 命中 35 次，**独立单词 `flow` 命中 0 次**（正则 `(^|[^a-z])flow([^a-z]|$)`） | **官网尚未列为正式产品** |
| 4 | Frappe Framework 内置 `Workflow` DocType | 框架自带的审批流引擎，与 AI 无关，**本来就在 v16 里、无需"引入"** | 排除：用户说的是"AI 模块"，语义不符 |
| 5 | PyPI `frappe-flow` | `frappe-flow` 0.1.4，summary `An open-source agent harness.`，依赖 `fastapi / litellm / textual / uvicorn`，requires-python `>=3.14`，作者 Shrihari Mahabal（与候选 2 的 `app_publisher` 同一人） | 排除：这是**独立的 CLI/TUI agent harness**，不是 Frappe app，依赖里没有 frappe |
| 6 | 第三方 `Frappe-FlowAgent` | `MirzaAreebBaig/Frappe-FlowAgent`，社区帖《Open Source Visual AI Workflow Automation for Frappe/ERPNext》 | 排除：非官方、非 `frappe` 组织，与"引入官方 AI 模块"语义不符 |
| 7 | Frappe Cloud 闭源/仅托管 | `flow_client` 是 AGPL 公开源码且可克隆成功，不构成闭源 | 排除 |

### 1.2 关于 `frappe/flow` 404 的判断

仓库名与 app 名不一致，有两条**直接的代码内证据**指向"曾用名 `frappe/flow`"：

- `README.md:8` 的 CI badge 仍指向 `https://github.com/frappe/flow/actions/workflows/ci.yml`（未随改名更新）
- `flow/patches/rename_ai_to_flow.py`：一次把 15 个 DocType 从 `AI *` 批量改名为 `Flow *`（`AI Agent → Flow Agent` 等），并改 `Module Def` `AI → Flow`。说明该 app 历史名为 `ai`，后改为 `flow`

GitHub 对改名仓库通常保留 301 重定向，而此处是**干净的 404**——这更像是 `frappe/flow` 这个名字已被一个**新的私有仓库占用**（占用后旧重定向失效）。但这一点我无法直接证实，列入「拿不准的」。

### 1.3 认定结论

**"Flow" = `github.com/frappe/flow_client`，安装后 app 名为 `flow`，官方定位「AI agents for Frappe」。**

理由：用户称其为"AI 模块"，这是关键线索——候选 2 是 `frappe` 组织下唯一同时满足「名为 flow」「是 AI」「是可装的 Frappe app」三项的对象。候选 4（内置 Workflow）虽同名语义但非 AI，候选 5 同名但非 Frappe app。

**需提请用户注意的歧义**：若用户本意是"审批流/工作流"，那是框架内置的 `Workflow` DocType，v16 已自带，不需要引入任何 app。

---

## 二、五问逐条作答

### 2.1 开源与许可证

| 项 | 值 | 证据 |
|---|---|---|
| 许可证 | **AGPL-3.0-or-later** | 打开真实文件 `license.txt:1-2` = `GNU AFFERO GENERAL PUBLIC LICENSE / Version 3`；`pyproject.toml` `license = "AGPL-3.0-or-later"`；`hooks.py:6` `app_license = "agpl-3.0"` |
| Star / Fork | 73 / 32 | GitHub API |
| Open issues | 20 | GitHub API |
| 最后提交 | **2026-08-12**（`4a3189b` Merge PR #89 from frappe/better_frontend） | `git log` |
| Release / Tag | **零 release、零 tag** | API `/releases` 与 `/tags` 均返回空 |
| 分支 | **只有 `develop` 一个分支** | API `/branches` |
| 体积 | 567 KB | API |

**AGPL 注意**：AGPL 的网络条款要求——若经修改后通过网络提供服务，须向使用者提供修改后源码。二次开发项目需评估此义务（Frappe/ERPNext 自身也是 AGPL，故并非新增风险类别，但 Flow 若被改动则各自独立计算）。

⚠️ 源码内部存在**许可证声明不一致**：65 个 Python 文件的文件头写 `# License: MIT. See LICENSE`（如 `flow/boot.py:2`、`flow/lib/model.py:2`），而仓库根 `license.txt` 是 AGPL-3.0。这是 Frappe 官方模板遗留的常见笔误，但**若要商用分发，此处需向上游确认**。

### 2.2 依赖与兼容

| 项 | 值 | 证据 |
|---|---|---|
| 依赖 ERPNext？ | **否，纯 Frappe** | 全仓库 grep `erpnext`（py/json/toml/txt）**零命中**；`hooks.py` 无 `required_apps` |
| 要求 Frappe 版本 | **`>=16.0.0-dev,<18.0.0`** | `pyproject.toml` `[tool.bench.frappe-dependencies]` |
| 要求 Python | **`>=3.14,<3.15`** | `pyproject.toml` `requires-python` |
| 有 v16 兼容分支/release？ | **没有专门的 version-16 分支，只有 `develop`** | API `/branches` 仅 `develop` |
| CI 测试基准 | `--frappe-branch develop` + Python 3.14 | `.github/workflows/ci.yml:52,66` |

**兼容性判定**：版本区间 `>=16.0.0-dev,<18.0.0` **覆盖我们的 16.34.0**，Python 3.14 与 v16 硬要求一致（v16 上游 `requires-python = ">=3.14,<3.15"`，已与本项目记忆中的 bench init 坑一致），故**技术上兼容**。但 CI 只针对 `frappe:develop` 跑，**没有针对 v16 稳定分支的验证**，且无 tag 可锁定版本——只能跟 `develop` 滚动。

**Python 侧新增依赖较重**：`litellm`（锁窄区间 `>=1.83.0,<1.83.8`）、`lancedb`、`pdfplumber`、`python-docx`、`rapidocr`、`onnxruntime`。其中 `onnxruntime` + `rapidocr` 是 OCR 推理栈，还需 apt 包 `libgl1`、`libglib2.0-0`（`pyproject.toml` `[deploy.dependencies.apt]`）——**在我们的 Docker 环境里意味着要改镜像**。

### 2.3 它做什么

核心 DocType（共 16 个，`flow/flow/doctype/`）：

| DocType | 职责 |
|---|---|
| `Flow Provider` | provider 级凭据与 endpoint（字段：`provider` / `api_key`(Password) / `base_url` / `extra_params`(JSON)） |
| `Flow Model` | 模型配置，`model_id` 形如 `anthropic/claude-sonnet-4-6` |
| `Flow Tool` | 可复用工具，模块路径或内联脚本 |
| `Flow Agent` | 指令 + 模型 + 工具组合 |
| `Flow Trigger` | 按 DocType 事件或 cron 触发 agent |
| `Flow Knowledge Base` / `Source` / `Chunk` / `Settings` | RAG 知识库与切块 |
| `Flow Session` / `Run` / `Session Message` / `Session Attachment` | 会话与执行审计 |

**"AI"部分的具体实现**：

- **接哪家 LLM**：通过 **`litellm`** 统一接入，`model_id` 走 `provider/model` 格式。**可换 provider**——`Flow Provider` / `Flow Model` 均可设 `base_url`，README 明确支持 **Ollama / LM Studio 等本地 provider**。
- **是否必须联外网与付费 key**：**不必然**。用本地 provider（Ollama）可离线。但**开箱默认路径需要付费 key**（README 指引填 `anthropic/claude-sonnet-4-6`）。
- **向量库**：**`lancedb`，本地落盘**（`flow/knowledge/store.py:18,28-33`，路径在 site 目录下，测试库名 `lancedb_test`），不依赖外部向量服务。
- **Embedding**：走 `litellm`，凭据解析与 chat 模型同源（`flow/knowledge/embedder.py:4-8`），模型在 `Flow Knowledge Settings.embedding_model` 指定。

**内置工具**（`flow/tools/builtins.py`）：`find_doctypes` / `describe` / `read` / `create` / `update` / `delete` / `run_action` / `execute`。工具调用可要求**人工确认**后执行，每次 run 落库审计。

`execute` 是沙箱 Python（`flow/tools/builtins.py:203-240` → `flow/utils/safe_exec.py`）：禁 `import`、禁下划线属性、禁 `frappe.db.sql` / `frappe.qb` / `frappe.get_all`，只留 `frappe.get_list` 等**走权限校验**的入口；禁用 `open` / `eval` / `exec` / `getattr` 等 builtins。设计上 **agent 的读写不越过当前用户权限**。

### 2.4 接入机制（重点）

| 机制 | 做法 | 文件:行 |
|---|---|---|
| **前端形态** | **不是独立 SPA、也不是 desk 内页面**，而是注入 desk 的**滑出式覆盖面板**（slide-in overlay）。Vue 3 app 挂到运行时创建的 `div#flow-root`（`position:fixed`，右侧，`zIndex:1040`），CSS 全部以该 id 作用域隔离，避免污染 desk | `frontend/src/main.js:10-58` |
| **路由挂载** | **无 `website_route_rules`、无 `www/`**。hooks 里 grep `website_route`/`override`/`fixtures` **零命中**。资源靠 `app_include_js` / `app_include_css` 注入，带 mtime 版本串 | `flow/hooks.py:17-27` |
| 构建产物 | Vite 打成**单个 IIFE bundle + 单个 CSS**，输出到 `flow/public/flow_panel/`，供 desk 直接加载 | `vite.config.js:5-8,30-45` |
| **唤起方式** | `frappe.ui.keys.add_shortcut` 注册 **`ctrl+i`** | `frontend/src/main.js:117-124` |
| **后端通讯** | `frappe.xcall` 调白名单方法 + **SSE 流式**（`fetch('/api/method/...')` 读流）。7 个白名单端点：`start_run` / `resume_run` / `stop_run` / `recover_session` / `submit_feedback` / `get_agent_tools` / `attach_file` | `flow/api/api.py:20,43,65,81,107,147,166`；`frontend/src/api/client.js:57-90`；`frontend/src/api/stream.js:7,43` |
| **`doc_events`（关键）** | **对 `"*"`（所有 DocType）挂 5 个事件**：`after_insert` / `on_update` / `on_submit` / `on_cancel` / `on_trash` → `flow.triggers.dispatch` | `flow/hooks.py:29-37` |
| `override_*` | **无**任何 `override_whitelisted_methods` / `override_doctype_class` | `flow/hooks.py`（grep 零命中） |
| 其他 hooks | `extend_bootinfo = flow.boot.boot_session`；`after_migrate = flow.assistant.sync_builtin_assistant`；`ignore_links_on_delete`；`Flow Session` 日志 90 天清理 | `flow/hooks.py:43-62` |
| **额外进程/服务** | **不需要独立进程**。但依赖既有 **scheduler**（`cron */5` 跑 `dispatch_scheduled`、`daily` 跑知识库同步）和 **worker 队列**（`frappe.enqueue`） | `flow/hooks.py:49-58`；`flow/triggers/triggers.py:31-37` |
| migration patch | `pre_model_sync`: `rename_ai_to_flow`（改名 15 个 DocType，含 `__Auth` 表里 password 字段迁移、删旧 Workspace）；`post_model_sync`: `remove_frontend_tooling`（清理已撤回的 `read_screen`/`navigate`/`fill`/`act` 工具行） | `flow/patches.txt`；两个 patch 文件 |

**`doc_events: "*"` 的代价**：本项目**每一次**文档 insert/update/submit/cancel/trash 都会多走一次 `flow.triggers.dispatch`。该函数有早退保护——非 5 个事件名直接 return、Flow 自身 5 个 DocType 跳过、`in_install`/`in_migrate` 跳过（`flow/triggers/triggers.py:19-24`），随后查该 DocType 的 trigger 表。即便无 trigger 配置，**每次写操作仍会多一次查询开销**，且这是**全局侵入**。

**安装命令有误**：README 写 `bench get-app flow`，但 bench 对裸 app 名只依次探测 `frappe/` 与 `erpnext/` 两个组织（`bench/utils/__init__.py:454-471` `find_org`），而 `frappe/flow` 与 `erpnext/flow` **均为 404**（已实测）。故实际必须用完整 URL：

```
bench get-app https://github.com/frappe/flow_client --branch develop
```

（本次调研**未执行**任何 `bench install-app`，未动 Docker 环境。）

### 2.5 与 Raven 的关系

| 维度 | Flow | Raven |
|---|---|---|
| 出品方 | `frappe` 组织，`app_publisher` 为个人 Shrihari Mahabal | `frappe` 组织，`author` 为 Frappe 官方 |
| 定位 | AI agent / 工具 / 触发器框架 + desk 侧边 AI 面板 | 团队即时通讯平台（792 star，有独立站 ravenchat.ai） |
| AI 模块 | 全部核心即 AI | **有 `Raven AI` 模块**（`raven/modules.txt` 列出），DocType 含 `Raven AI Function` / `Raven Bot AI Prompt` / `Raven AI File Source` / `Raven Bot Instruction Template` 等 |
| LLM 接入 | **litellm**，多 provider、可指 `base_url` 走本地 | **绑定 OpenAI**：依赖 `openai>=2.30.0` + `openai-agents>=0.17.2`（`pyproject.toml`） |
| Python 要求 | `>=3.14,<3.15` | `>=3.10` |
| 能否只装其一 | **能**，互不依赖（Flow 无 `required_apps`） | **能** |

**关系判定**：**同属 frappe 组织但非同一团队产物，功能部分重叠、整体互补。**

- 重叠：两者都能做"聊天式 AI 助手 + 调用 Frappe 数据的工具"。Raven AI 走 OpenAI Assistants/Agents 路线，Flow 走自研 litellm agent runtime。
- 互补：Raven 的载体是**聊天室**（多人协作、频道），Flow 的载体是**desk 内个人面板 + 事件/定时触发的自动化**。Raven 无 `doc_events` 级的全局触发器，Flow 无团队消息。
- 若两者同装，会出现**两套 AI 配置与两处 LLM 凭据**，且 Raven 侧受限于 OpenAI。

---

## 三、拿不准的

1. **`frappe/flow` 404 的真实原因**。代码内有改名痕迹（README badge 指向 `frappe/flow`、`rename_ai_to_flow.py`），但 GitHub 返回干净 404 而非 301 重定向。我推断是该名字被新的私有仓库占用，**但无法证实**；也可能是 `flow_client` 本就独立命名、README badge 从未正确过。
2. **`flow_client` 这个仓库名的含义**。名字暗示它是某个"Flow 服务端"的 client，而 PyPI 上存在同作者的独立 harness `frappe-flow`（fastapi + litellm + textual）。两者是否为「harness 服务端 + Frappe 端 client」的配套关系，**我没有找到直接证据**（克隆下来的代码里未见对 `frappe-flow` 包的依赖，`pyproject.toml` 依赖列表中没有它）。若确为配套，则可能还有未公开的服务端组件。
3. **官方定位与支持承诺**。`frappe.io` 无产品页、零 release、零 tag、`app_publisher` 是个人邮箱而非 `support@frappe.io`（对比 Raven 用的是官方邮箱）。这更像**官方孵化中的早期项目**而非已发布产品，但我无法确认 Frappe 是否有正式支持计划。LinkedIn 有「Frappe Flow - A sneak preview」贴（2025-09），未取到正文。
4. **65 个文件头 MIT vs 根目录 AGPL 的矛盾**以哪个为准。按惯例根 LICENSE 优先（且 `pyproject.toml` 也写 AGPL），但商用前应向上游求证。
5. **最后 push 2026-08-12，距今约 6 周**，而 `updated_at` 是 2026-09-22（通常只是 star/issue 活动）。是短期停顿还是放缓，样本不足以判断。
6. **实际运行表现未验证**。本次只做静态阅读，未安装、未跑测试，OCR/onnxruntime 在本项目 Windows Docker 环境下能否装通**完全未验证**。

---

## 四、对本项目的直接影响

**该不该引入：现阶段不引入，先观察。** Flow 技术上兼容我们的 16.34.0，能力也确实对口（desk 内 AI 助手 + 事件驱动自动化 + 本地 RAG，且可换本地 LLM 免付费 key），值得列入后续候选；但当前成熟度不足以进入一个正在做需求摸底的项目。

**最主要的一个反对理由**：**它没有任何可锁定的版本——零 release、零 tag、只有 `develop` 一个分支，且 CI 只针对 `frappe:develop` 验证。** 引入就等于把一个会滚动变动的第三方 app 绑进本项目，而它同时通过 `doc_events: "*"`（`flow/hooks.py:29-37`）挂在**所有 DocType 的五个写事件**上——一旦上游 `develop` 引入回归，影响面是全库写操作，而我们无法回退到某个已验证的版本点。

次要顾虑（不作为主理由，供权衡）：`onnxruntime` + `rapidocr` + apt 包 `libgl1`/`libglib2.0-0` 需改 Docker 镜像，与本项目已记录的 Windows Docker 环境坑叠加；文件头 MIT 与根目录 AGPL 的声明矛盾在商用分发前需澄清。

**若用户本意是"审批流"**：那是 Frappe v16 内置的 `Workflow` DocType，**无需引入任何 app**，直接在 desk 里配置即可。
