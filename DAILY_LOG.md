# 项目日志

> **项目**：从零实现 Python Agent 系统
> **开始日期**：2026-05-12

---

## Day 1 — 2026-05-12（周一）

### 今日目标
- [x] 理解导师任务要求
- [x] 撰写设计文档 DESIGN.md
- [x] 创建项目日志 DAILY_LOG.md
- [x] 配置 Python 虚拟环境与依赖

### 完成内容
- 梳理了 Agent 系统的四层架构：Loop Manager / Tool Registry / Context Manager / Infra Layer
- 明确了开发顺序：LLM Client → Tools → Loop → Context → Infra
- 创建虚拟环境 `venv`，安装核心依赖：`openai`、`tiktoken`、`pyyaml`

### 遇到的问题
- 无（今天是规划日）

### 明天计划
- [ ] 实现 `llm_client.py`：封装内部 API 调用，含重试逻辑，能成功收发第一轮消息

---

## Day 2 — 2026-05-13（周二）

### 今日目标
- [x] 打通 API 调用（推迟至 Day 4 完成）

### 完成内容
- 未投入（个人时间冲突）

### 遇到的问题
- 无

### 明天计划
- [ ] 补上 API 调用 + 三个工具

---

## Day 3 — 2026-05-14（周三）

### 今日目标
- [x] 实现三个工具（推迟至 Day 4 完成）

### 完成内容
- 未投入（个人时间冲突）

### 遇到的问题
- 无

### 明天计划
- [ ] 集中一天补齐 Day 2~4 的进度

---

## Day 4 — 2026-05-15（周四）⏳ 实际投入约 6h

### 今日目标
- [x] 实现 config.py + llm_client.py（Day 2）
- [x] 实现 calculator.py 工具（Day 3）
- [x] 实现 file_ops.py 工具（Day 3）
- [x] 实现 bash_exec.py 工具（Day 3）
- [x] 编写四个测试文件

### 完成内容
1. **API 层**：`src/config.py` — yaml 配置加载；`src/llm_client.py` — OpenAI 兼容客户端封装，支持多轮对话。遇到 IPv6 连接问题（校园网无 IPv6），通过 Teredo 隧道 + 修正 base_url 为 `/v1` 路径解决。
2. **计算器工具**：`src/tools/calculator.py` — 基于 `ast.parse()` 的安全表达式求值，白名单节点校验 + `__builtins__` 禁用，支持 `+ - * / ** sqrt sin cos log abs ceil floor pi e`。
3. **文件工具**：`src/tools/file_ops.py` — `file_read` / `file_write`，基于 `Path.resolve()` + `relative_to()` 的沙箱路径穿越防护。
4. **命令执行工具**：`src/tools/bash_exec.py` — `subprocess.run(shell=False)` 安全执行，黑名单拦截危险命令，UTF-8 编码处理中文内容。

### 遇到的问题
- **IPv6 连接失败**：校园 WiFi 和手机热点均无 IPv6 地址，通过 Teredo 隧道解决
- **AST 白名单踩坑**：`ast.Num` 在 Python 3.10 已移除、`abs` 是内置函数不在 `math` 模块、末尾逗号导致值变成元组
- **路径穿越检测**：`str.startswith()` 无法区分 `workspace/` 和 `workspace_evil/`，改用 `Path.relative_to()` 解决
- **Windows 编码**：`subprocess` 默认 GBK 解码 UTF-8 文件崩溃，改用 `encoding="utf-8", errors="replace"` 解决
- **`shell=False` + Windows**：`dir`/`type`/`mkdir` 是 cmd 内置命令，需用 `cmd /c` 包一层才能执行

### 明天计划
- [ ] Day 5: 实现工具注册 `tool_registry.py` + Agent Loop `agent.py`
- [ ] Day 6: Context 管理（token 跟踪 + 压缩）

## Day 5 — 2026-05-16（周五）⏳ 实际投入约 4h

### 今日目标
- [x] 实现工具注册 `tool_registry.py`（Day 4）
- [x] 实现 Agent Loop `agent.py`（Day 4）
- [x] 整合 `test_api.py` 端到端测试

### 完成内容
1. **工具注册中心**：`src/tool_registry.py` — `init_tools()` 注册四个工具 + `partial` 绑定 `sandbox_dir`、`get_tools_schema()` 用 `inspect.signature()` + `get_type_hints()` 生成 OpenAI function calling 格式的 JSON Schema、`execute_tool()` 统一调度执行。
2. **Agent Loop**：`src/agent.py` — `run(task, verbose=True)` 实现 `while turn < max_turns` 主循环：chat → 判断 tool_calls 还是 text → 执行工具 → 追加 tool result → 继续循环 → 返回最终答案。支持 verbose 调试模式打印每轮工具调用详情。
3. **`llm_client.chat()` 扩展**：新增可选 `tools` 参数，支持传入工具 Schema。
4. **`test_api.py` 重构**：从手动工具调用逻辑精简为直接调用 `agent.run()`，43行 → 19行。

### 遇到的问题
- **`partial` + `inspect.signature()` 不兼容**：`functools.partial` 绑定 `sandbox_dir` 后，`inspect.signature()` 在 Python 3.10 下未正确剥离已绑定参数，导致 Schema 暴露了 `sandbox_dir`。模型拿到这个参数后疯狂试探各种路径（C:\、D:\、/tmp、/mnt/data...），15 轮全部失败。解决：在 Schema 生成时手动过滤 `sandbox_dir` 参数。
- **`file_read` 忘记传参**：添加 `sandbox_dir` 参数后，`file_read` 内部调用 `safe_resolve_path` 时漏传了 `sandbox_dir`，只有 `file_write` 写对了。
- **`str / str` 类型错误**：`sandbox_dir` 从 config 传入是字符串，但 `safe_resolve_path` 里用了 Path 的 `/` 运算符。需先 `Path(sandbox_dir).resolve()` 转换。
- **bash 重定向在 `shell=False` 下无效**：模型尝试 `cmd /c echo xxx > file` 写文件，但 `>` 重定向需要 shell 解析。`file_write` 修好后模型就不再绕道 bash 了。
- **模型穷举路径耗尽轮数**：当工具持续返回 error 时，模型不会停止而是尝试不同参数，直到 `max_turns=20` 耗尽。说明 Agent Loop 需要后续加入"连续失败 N 次则终止"的保护机制。

### 明天计划
- [ ] Day 6 补进度：Context 管理（`src/context.py` — token 计数 + 历史压缩）
- [ ] 如时间允许，写集成测试（多工具协同场景）

---

## Day 6 — 2026-05-17~18（周六~周日）⏳ 实际投入约 10h

### 今日目标
- [x] 实现 Context 管理：token 计数（已完成）
- [x] 实现滑动窗口压缩策略（已完成）
- [x] 实现残差连接压缩策略（灵感来自 ResNet）（已完成）
- [x] 工具结果截断（已完成）
- [x] 集成到 agent.py（已完成）
- [x] 改进 bash_exec：自动包装 cmd 内置命令（已完成）
- [x] 端到端对比测试（已完成）

### 完成内容

1. **token 计数**：`count_tokens()` — 基于 `tiktoken`（`cl100k_base`），逐字段累积 role/content/tool_calls/tool_call_id，加上 OpenAI 消息格式开销（3 token/条）。支持 content 为 None、content 为 list（多模态）的安全处理。

2. **滑动窗口压缩**：`compress_messages_sliding_window()`
   - 核心逻辑：保留 system + 首条 user + 最近 `keep_turns` 个完整轮次，丢弃中间轮次
   - 轮次边界检测：从后向前逆扫，识别 assistant(tool_calls) + tool 响应的配对关系
   - 二次压缩：while 循环在仍超 0.8 倍阈值时继续丢弃最早轮次
   - 占位符："[系统提示] 之前的对话历史因长度限制已被压缩"

3. **残差连接压缩**：`compress_messages_residual_connection()`
   - 灵感：ResNet 的 `y = F(x) + x`，system + 首条 user 是恒等映射，摘要内容 F(x) 是残差
   - 与滑动窗口的唯一差异：占位符不是固定文本，而是通过 `_generate_summary()` 调用 LLM 将丢弃的中间轮次蒸馏为 2~5 条结构化要点
   - 摘要失败时自动回退到固定占位符
   - `_format_middle()`：将原始消息 JSON 转为可读文本再喂给 LLM 生成摘要，大幅提升摘要质量

4. **代码架构重构**：
   - 提取 `_split_messages()` — 切分 system、首条 user、保留轮次、被丢弃的中间消息
   - 提取 `_assemble()` — 拼接 + while 削轮次
   - `_compress_core()` — 供滑动窗口调用的公共核心
   - 残差连接独立调用 `_split_messages→_generate_summary→_assemble`

5. **工具结果截断**：`truncate_tool_result()` — 超过 2000 字符截断并附加 `...[内容已截断，原文X个字符]`

6. **agent.py 集成**：
   - 每轮 chat() 前调用压缩函数，前 token 数判断 → 需要时压缩
   - 累计 prompt_tokens / completion_tokens，三个出口均打印总 token
   - verbose 模式下打印压缩触发提示（区分残差/滑动窗口）、压缩前后对比
   - 工具结果在追加到 messages 前截断长内容

7. **bash_exec.py 改进**：新增 `CMD_BUILTINS` 集合（dir/mkdir/type/echo/copy 等），自动为 cmd 内置命令添加 `cmd /c` 前缀，消除模型摸索 Windows 命令语法的 3~4 轮浪费。

8. **system_prompt 改进**：明确告知模型当前工作目录就是沙盒根目录，避免路径嵌套（`workspace/workspace/...`）。

9. **测试**：
   - `test_context.py` — 28 个自动化用例，覆盖 count_tokens（7）、truncate（6）、不压缩（3）、压缩（6）、含最终答案（1）、二次压缩（3）、极端阈值（2），0 API 调用
   - 端到端对比测试三组：纯计算 7 步任务、混合工具 7 步任务、错误穿插任务

### 遇到的问题

- **`context_max_tokens` 设太低导致死循环**：`300` 阈值时 system + user 已占大部分预算，压缩后只剩 1 轮上下文，模型无法追踪多步任务进度，在 1+1 和 2+2 之间无限循环。解决：认识到 `count_tokens()` 不计入 tool schema 的 token，实际 API 消耗比测量值高 ~200 token，阈值需留余量。验证合适值：600~1200。

- **`turns = turns[1:]` 删错了方向**：`turns` 列表是逆序收集的（turns[0]=最新轮），`turns[1:]` 删掉了最新一轮而非最旧一轮。已被 `test_context.py` 捕获。修复为 `turns.pop()`。

- **超过 max_turns 不打印 token 统计**：三个出口（正常结束、模型无返回、超时）中只有正常结束打印了 `[总Token]`。已补全。

- **纯滑动窗口的非确定性**：同一个任务、同一个阈值，两次运行结果不同（一次 20 轮失败，一次 8 轮成功）。根因：占位符只告诉模型"你忘了"，模型需要猜自己做到了哪一步，猜对猜错是概率事件。残差连接通过摘要消除了这个不确定性。

- **残差摘要质量依赖输入格式**：直接喂原始 JSON 给 LLM，噪声大、容易漏步骤。`_format_middle()` 将消息转为"调用 xxx → 成功/失败"的可读格式后，摘要质量显著提升。

- **`_format_middle` 实现中的四个笔误**：`tc["function"]["args"]` 应为 `"arguments"`（KeyError）；`key_info = []` 应为 `{}`（TypeError）；`json.dunmps` 拼写错误；VSCode 自动将半角引号转为全角弯引号导致 SyntaxError。

- **压缩前上下文全是错误时，两个策略都救不了**：测试二中 bash 连续失败占满 token 预算，压缩时摘要生成的是"bash 一直报错"，无法帮助模型恢复。解决：修复 bash_exec（`cmd /c` 自动包装）从根源消除错误。结论：垃圾进垃圾出——压缩质量的上限由压缩前上下文质量决定。

- **模型不知道自己已在沙盒根目录**：用户说"在 workspace 下建目录"，模型理解为需要写 `workspace/compare_test`，导致路径嵌套。在 system_prompt 中明确告知当前目录即可。

### 关键对比结论

| 维度 | 滑动窗口 | 残差连接 |
|------|---------|---------|
| 占位符 | "已被压缩，继续执行" | "已完成: - 计算 1+1=2 - 计算 2+2=4 ..." |
| 信息量 | 0 bit（告诉模型忘了） | 结构化记录（告诉模型做了什么） |
| 稳定性 | 随机（模型需要猜进度） | 确定（摘要白纸黑字） |
| 额外成本 | 无 | 1 次不带 tools 的 chat（~300 token） |
| 类比 | 直接截断 | ResNet 残差链接：y = x + F(x) |

### 明天计划
- [x] Day 7: 轨迹日志 + run_id + 多轮对话（已完成）
- [ ] API 重试（推迟至 Day 8）

---

## Day 7 — 2026-05-20（周二）⏳ 实际投入约 4h

### 今日目标
- [x] 实现 logger.py：轨迹日志（trajectory JSONL）
- [x] 实现唯一 run_id（时间戳 + 随机后缀）
- [x] 集成 logger 到 agent.py（7 种事件类型全覆盖）
- [x] 实现多轮对话支持（agent.py messages 参数）
- [x] 更新 test_api.py 支持多轮对话和清空重置
- [x] 项目审计：AUDIT.md
- [ ] API 自动重试（推迟至明天）

### 完成内容

1. **logger.py 实现**：
   - `init_run(log_dir)` → 生成 `run_id`（`%Y%m%d-%H%M%S` + 4 位随机字符）+ 创建 `logs/traj_{run_id}.jsonl`，返回 `(run_id, path)`
   - `log_event(path, **kwargs)` → 追加一行 JSON 到 jsonl，自动附加 `timestamp` 字段
   - timestamp 从 Unix 时间戳改为人可读的 `strftime("%Y-%m-%d %H:%M:%S")` 格式

2. **run_id 设计**：
   - 格式：`20260520-233425-jgkj`（15 位时间 + 4 位随机）
   - 优势：比 `uuid4().hex[:8]` 更具可管理性——文件名排序即时间排序，一眼看出运行时刻
   - 加 4 位随机后缀防止同一秒两次运行冲突

3. **agent.py logger 集成**：
   - 闭包模式存储 `log_path`：`if not hasattr(run, "_log_path")` 首次初始化，后续调用复用，不通过返回值传递
   - 覆盖 7 种事件：`agent_start`、`llm_request`、`llm_response`、`tool_call`、`tool_result`、`error`、`agent_end`
   - 三个出口（正常、无返回、超时）均记录 `agent_end`
   - tool_result 记在截断之后，日志不膨胀

4. **多轮对话支持**：
   - `agent.py`：`run(task, messages=None)` — 首次 `messages=None` 新建，后续传入则追加
   - `test_api.py`：维护 `messages` 变量，支持 `clear` 命令重置对话
   - 多轮模式下不重复 `init_run`——log 文件首次创建，后续复用

5. **AUDIT.md**：逐条对照原始 4 项要求，记录完成状态、7 个代码缺陷、未完成的 4 个 Infra 模块及实现方案

### 遇到的问题

- **`init_run` 解包遗漏**：`path = init_run()` 只接了一个值，实际返回 `(run_id, path)` 元组，导致 `path` 接到 `run_id` 字符串，日志写到错误位置。修复为 `run_id, path = init_run(...)`。

- **`max_turns` 定义前使用**：`log_event(..., max_turns=max_turns, ...)` 写在了 `max_turns = AGENT["max_turns"]` 之前。交换两行位置解决。

- **`AGENT["max_tokens"]` vs `AGENT["max_turns"]`**：config 里的键是 `max_turns`，误写为 `max_tokens` 导致 KeyError。

- **`LLM["models"]` vs `LLM["model"]`**：config 键是单数 `model`，误写为复数。同时 `model` 在 `LLM` 段不在 `AGENT` 段，需额外 `from src.config import LLM`。

- **`CompletionUsage` 不可 JSON 序列化**：`resp.usage` 是 openai 的对象，不是普通 dict。`json.dumps` 报 `TypeError`。修复为拆成独立字段：`prompt_tokens=resp.usage.prompt_tokens, completion_tokens=resp.usage.completion_tokens`。

- **`log_event` 记 `tool_result[key]` 在 for 循环外**：循环变量 `key` 泄漏到循环外，当 tool_result 无 `content`/`output` 字段（如 calculator 返回 `result`）时，`tool_result["output"]` 触发 KeyError。修复为记录完整 `tool_result` dict，且移入 `isinstance` 判断块内。

- **闭包存 path 的方案选择**：最初想用函数属性 `run._log_path` 存，差点被 `hasattr` 的初始化和 `messages is None` 时的分支逻辑绕晕。最终确认：`hasattr` → 首次置 None → `messages is None` 时 init_run 覆盖 → 后续调用直接读 `run._log_path`。三路分支正确。

### 关键学习

- `uuid4` 是随机数（不暴露机器信息），`uuid1` 含 MAC + 时间戳
- `Path("/")` 运算符就是路径拼接，Windows 自动转 `\`
- `**kwargs` 在函数定义处打包参数为 dict，在调用处解包 dict 为参数
- `json.dumps(ensure_ascii=False)` 保留中文原样，不加会在日志看到 `\uXXXX`
- `time.time()` 返回 Unix 时间戳（秒），`strftime()` 转为人可读格式
- Python 的 for 循环变量在循环结束后仍然存在（变量泄漏），容易在循环外误用

### 明天计划
- [ ] API 自动重试（指数退避）
- [ ] `$` 成本计算
- [ ] main.py 入口
- [ ] 修复 AUDIT.md 中记录的其余缺陷
