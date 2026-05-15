# Agent 系统设计文档

> **目标**：从零开始，用纯 Python（不依赖 LangChain 等框架）实现一个可与大模型交互、调用工具、完成任务的 Agent 系统。

---

## 一、什么是 Agent？

**一句话**：Agent = 大模型 + 工具 + 循环。

传统使用大模型的方式是"一问一答"：你提问题，模型给你答案。而 Agent 的思路是让模型**自己决定什么时候需要调用工具**，工具执行后把结果还给模型，模型再决定下一步怎么做，如此循环，直到得出最终答案。

类比：你（用户）是老板，模型是你的助手，工具有计算器、文件系统、终端。你说"帮我把桌面上所有 Python 文件的行数统计出来"，助手会：
1. 思考：我需要先列出文件 → 调用 `bash ls`
2. 拿到文件列表 → 对每个文件调用 `bash wc -l`
3. 汇总结果 → 返回给你

这个"思考→行动→观察→思考..."的循环就叫 **Agent Loop**。

---

## 二、系统架构总览

```
┌──────────────────────────────────────────────────────────┐
│                        Agent                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Loop    │  │  Tool    │  │ Context  │  │  Infra   │ │
│  │ Manager  │  │ Registry │  │ Manager  │  │  Layer   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │             │             │             │        │
│  ┌────┴─────────────┴─────────────┴─────────────┴────┐   │
│  │                 LLM Client (OpenAI API)            │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

四个核心模块各司其职：
- **Loop Manager**：控制"思考→行动→观察"的循环，决定何时停止
- **Tool Registry**：管理所有可用工具，提供统一的调用接口
- **Context Manager**：管理对话历史，控制 token 用量
- **Infra Layer**：日志、重试、成本统计等基础设施

---

## 三、Agent Loop（核心循环）

### 3.1 基本原理

Agent Loop 的本质是一个 `while` 循环，伪代码：

```
while 未达到停止条件:
    1. 将当前消息历史发给大模型
    2. 大模型返回响应
    3. 如果响应是"最终答案" → 停止
    4. 如果响应是"调用工具" → 执行工具，将结果加入历史，回到步骤1
```

### 3.2 关键实现细节

**消息格式（OpenAI Chat Completions API 格式）**

每条消息有三个角色：
- `system`：系统提示词，定义 Agent 的行为规则
- `user`：用户的问题
- `assistant`：模型的回复（可能包含工具调用）
- `tool`：工具执行的结果

一个完整的对话历史就是一个消息列表 `[{role: ..., content: ...}, ...]`。

**工具调用（Function Calling / Tool Use）**

模型不会真的去执行工具，它只是**告诉你它想调用哪个工具、传什么参数**。比如模型返回：

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "function": {"name": "calculator", "arguments": "{\"expression\": \"2+3\"}"}
    }
  ]
}
```

你的代码负责解析这个 JSON，真正去调用 `calculator` 函数，然后把结果作为一条 `tool` 角色消息追加到历史中。

### 3.3 停止条件

三种情况循环会终止：

| 条件 | 判断方式 |
|------|----------|
| 模型给出最终答案 | 模型的回复没有 `tool_calls`，只有文本 `content` |
| 达到最大轮数 | 设置 `max_turns`（如 20），超过则强制停止 |
| 用户中断 | `KeyboardInterrupt`（Ctrl+C）|

### 3.4 工具报错时的恢复

工具执行可能失败（如：计算器收到非法表达式、bash 命令超时）。恢复策略很简单：

1. 捕获异常，**不要把异常抛给用户**
2. 将错误信息包装成 tool 角色的消息：`"Error: calculator failed - division by zero"`
3. 把这条消息追加到历史中，让模型看到错误后自行修正

这就和人一样：你试了一个方法发现不对，你会根据错误信息调整策略。

---

## 四、工具系统（Tools）

### 4.1 设计思路

所有工具遵循统一接口：

```python
# 每个工具都是一个函数，接收参数字典，返回字符串结果
def tool_calculator(expression: str) -> str:
    ...

def tool_file_read(path: str) -> str:
    ...

def tool_bash_exec(command: str) -> str:
    ...
```

然后用一个注册表（字典）管理：

```python
TOOLS = {
    "calculator": tool_calculator,
    "file_read": tool_file_read,
    "file_write": tool_file_write,
    "bash_exec": tool_bash_exec,
}
```

同时每个工具需要一个 JSON Schema 描述参数，供 API 的 `tools` 参数使用。

### 4.2 三个工具的实现要点

**1. Calculator（计算器）**

- 核心：使用 Python 的 `eval()` 但必须做安全限制
- 安全措施：先用 `ast.parse()` 解析表达式，检查是否只包含安全的节点类型（数字、运算符、`math` 模块函数如 `sqrt`、`sin` 等）
- 只允许白名单内的数学函数，拒绝任何可能执行代码的表达式

**2. 文件读写**

- 限定工作目录（sandbox 目录），所有路径操作都在这个目录内
- 用 `os.path.realpath()` 解析真实路径，用 `.startswith()` 检查是否越界
- 读写都用 `with open()`，注意处理 Unicode 编码问题

**3. Bash 命令执行（简单沙箱）**

- 使用 `subprocess.run()` 执行命令
- 必须设置的三个安全参数：
  - `shell=False`：不通过 shell 执行，防止注入
  - `timeout=30`：超时杀死，防止死循环
  - `cwd=sandbox_dir`：限定工作目录
- 捕获 stdout 和 stderr，截断过长输出（如限制 5000 字符）
- 维护一个危险命令黑名单（如 `rm -rf /`、`shutdown` 等），对用户输入做检查

---

## 五、Context 管理（Token 管理）

### 5.1 为什么需要管理 Context？

大模型的 API 有两个硬限制：
1. **上下文窗口有限**：比如 128K token。超过就直接报错
2. **按 token 计费**：你发的越多花的钱越多

而且随着对话轮数增加，历史消息越来越长，不仅花钱多，模型的注意力也会被稀释（lost-in-the-middle 问题）。

### 5.2 Token 计数

需要引入 `tiktoken` 库（OpenAI 官方的 token 计数工具）：

- 每轮发送前，统计当前消息列表的总 token 数
- 每轮收到回复后，统计回复消耗的 token 数
- 累计记录，用于最终的成本核算

### 5.3 超阈值策略

设定一个安全阈值（如 `max_tokens` 的 80%），当历史消息超过阈值时，执行压缩：

**策略一：滑动窗口（简单，推荐先用）**
- 永远保留 `system` + 第一条 `user` 消息
- 只保留最近 N 轮对话，丢弃中间轮次

**策略二：摘要压缩（更高级）**
- 调用模型对早期对话做摘要："之前的对话中，用户问了 X，你做了 Y，得到了 Z"
- 用摘要替换原始历史
- 优点是保留了关键信息，缺点是额外消耗一次 API 调用

建议先用策略一，后续再升级到策略二。

---

## 六、基础设施与可观测性

### 6.1 完整 Trajectory 日志

每次运行记录一个 `.jsonl` 文件，每一行是一条 JSON，记录：

```
{timestamp, run_id, step, type, data}
```

- `agent_start`：记录本次运行的参数（模型、max_turns、时间戳）
- `llm_request`：发给 API 的消息（或消息的 token 数摘要）
- `llm_response`：API 返回的完整内容
- `tool_call`：调用了哪个工具、传了什么参数
- `tool_result`：工具返回了什么结果
- `agent_end`：最终结果、总 token 数、总耗时
- `error`：任何异常信息

这样任何一次运行都可以完整复现和排查。

### 6.2 API 报错自动重试

网络不是 100% 可靠的。需要实现指数退避重试：

| 重试次数 | 等待时间 |
|----------|----------|
| 第 1 次失败 | 等 1 秒 |
| 第 2 次失败 | 等 2 秒 |
| 第 3 次失败 | 等 4 秒 |
| 第 4 次失败 | 等 8 秒 |

最多重试 3~5 次，全部失败后才报错。注意只重试可恢复的错误（网络超时、429 限流），不重试不可恢复的错误（401 认证失败）。

### 6.3 Token 数和成本统计

需要知道模型的定价（以 OpenAI 为例）：

```
总成本 = input_tokens × input单价 + output_tokens × output单价
```

你的导师给了内部 API，你应该问清楚具体的单价。统计在整个 Agent 运行结束后汇总输出。

### 6.4 唯一 Run ID

使用 Python 内置的 `uuid.uuid4()` 生成。每次运行产生一个唯一 ID，用作：
- 日志文件名的一部分：`trajectory_{run_id}.jsonl`
- 每条日志记录的关联键

如果需要复现某次运行，可以恢复当时的随机种子、参数配置。

### 6.5 其他可补充的

- **彩色终端输出**：使用 `rich` 库或简单的 ANSI 颜色码区分不同类型的日志
- **进度指示**：Agent 思考时显示 spinner，让用户知道程序没卡死
- **配置文件**：用 YAML/JSON 配置文件存储 API key、模型名、默认参数
- **Dry-run 模式**：不实际执行工具，只打印"会调用什么工具"，方便调试
- **交互模式 vs 单次模式**：交互模式持续对话，单次模式处理一个任务就退出

---

## 七、项目文件结构建议

```
agent/
├── DESIGN.md            ← 你现在看的这个
├── DAILY_LOG.md         ← 每日项目日志
├── requirements.txt     ← Python 依赖
├── config.yaml          ← 配置文件（API key, 模型参数）
├── src/
│   ├── main.py          ← 入口
│   ├── agent.py         ← Agent 核心（Loop）
│   ├── llm_client.py    ← LLM API 封装（含重试）
│   ├── tool_registry.py ← 工具注册与管理
│   ├── tools/
│   │   ├── calculator.py
│   │   ├── file_ops.py
│   │   └── bash_exec.py
│   ├── context.py       ← Token 跟踪与历史压缩
│   ├── logger.py        ← Trajectory 日志
│   └── config.py        ← 配置加载
├── logs/                ← 运行时生成的日志
│   └── traj_<run_id>.jsonl
└── workspace/           ← 文件操作的沙箱目录
```

---

## 八、开发顺序建议

按照依赖关系，建议你按以下顺序动手：

| 阶段 | 内容 | 预计掌握的内容 |
|------|------|---------------|
| **Day 1** | 搭环境 + 写 LLM Client（能调用 API 就行） | API 调用、消息格式 |
| **Day 2** | 实现三个工具（calculator, file_ops, bash_exec） | 工具设计、安全沙箱 |
| **Day 3** | 实现 Agent Loop（不含 context 管理） | 循环逻辑、tool calling 解析 |
| **Day 4** | 加 Context 管理（token 统计 + 滑动窗口） | tiktoken、消息压缩 |
| **Day 5** | 加 Infra 层（日志、重试、成本、run_id） | 可观测性、异常处理 |
| **Day 6** | 集成测试 + 修 bug + 完善文档 | 系统整合、调试 |

---

## 九、关键概念速查

| 概念 | 简单解释 |
|------|----------|
| Token | 模型处理文本的最小单位，~1 个英文单词 ≈ 1.3 token，1 个汉字 ≈ 2 token |
| System Prompt | 给模型设定"人设"和规则的提示词，每轮对话最开头 |
| Tool Calling | OpenAI API 的一种模式，模型返回函数调用请求而非文本 |
| Context Window | 模型能"看到"的最大 token 数上限 |
| 指数退避 | 每次失败后等待时间翻倍的重试策略 |
| Trajectory | Agent 一次运行的完整"轨迹"记录 |

---

> **写给刚入门的你**：不要被这些术语吓到。Agent 的本质就是一个"会调用工具的 while 循环"。先把最简单的循环跑通（用 calculator 一个工具），再逐步加功能。一次只做一件事。
