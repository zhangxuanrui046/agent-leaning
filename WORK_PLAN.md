# 两周工作计划

> **起止日期**：2026-05-12（周一）~ 2026-05-25（周日）
> **每日投入**：2~3 小时
> **总工时预估**：约 28 小时（含 buffer）

---

## 第一周：核心功能（把 Agent 跑起来）

### Day 1 — 5月12日（周一）✅ 已完成
**主题：规划与环境搭建**

- [x] 理解任务需求，拆解为四个模块
- [x] 撰写 [DESIGN.md](DESIGN.md) 设计文档
- [x] 创建 Python 虚拟环境，安装 openai / tiktoken / pyyaml
- [x] 创建项目目录结构

**产出**：可运行的 venv + 完整设计文档

---

### Day 2 — 5月13日（周二）⏳ 2.5h
**主题：打通 API 调用**

- [ ] 向导师确认内部 API 的三个信息：`base_url`、`api_key`、`model` 名称
- [ ] 将信息填入 `config.yaml`
- [ ] 实现 `src/config.py`：用 `yaml.safe_load()` 加载配置文件
- [ ] 实现 `src/llm_client.py`：
  - 封装 `openai.OpenAI(api_key=..., base_url=...)` 客户端
  - 写一个 `chat(messages)` 函数，收发第一条消息
  - 用硬编码的 messages 测试：发一句 "Hello"，确认能收到回复
- [ ] **里程碑**：在终端看到模型回复的第一句话

**关键代码量**：约 40 行

---

### Day 3 — 5月14日（周三）⏳ 2.5h
**主题：实现三个工具**

- [ ] 实现 `src/tools/calculator.py`：
  - 用 `ast.parse()` 做安全的白名单表达式检查
  - 支持 `+ - * / ** sqrt sin cos log` 等
- [ ] 实现 `src/tools/file_ops.py`：
  - `file_read(path)` — 读文件，路径约束在 sandbox 内
  - `file_write(path, content)` — 写文件，同样做路径约束
- [ ] 实现 `src/tools/bash_exec.py`：
  - `subprocess.run(cmd, shell=False, timeout=30, cwd=sandbox_dir)`
  - 简单危险命令黑名单
- [ ] 每个工具写好后，单独在 Python 交互环境中测试一下

**关键代码量**：约 80 行（三个文件合计）

---

### Day 4 — 5月15日（周四）⏳ 3h
**主题：工具注册 + Agent Loop（核心！）**

- [ ] 实现 `src/tool_registry.py`：
  - 工具注册字典 `{name: callable}`
  - 生成 OpenAI 兼容的 `tools` 参数（JSON Schema 列表）
  - `execute_tool(name, args)` 统一调度函数
- [ ] 实现 `src/agent.py` 的初版 Agent Loop：
  - `while turn < max_turns:` 主循环
  - 构建 messages → 调用 LLM → 解析响应
  - 如果响应有 `tool_calls`：执行工具 → 把 tool result 追加到 messages → 继续
  - 如果响应只有文本：打印最终答案，退出
  - 工具报错时：catch 异常 → 包装成 tool 消息 → 让模型自己修正
- [ ] 用 calculator 做第一个端到端测试：
  - "计算 123 * 456 再除以 7" → 应该看到模型调用 calculator → 返回结果
- [ ] **里程碑**：Agent 第一次自主调用工具完成任务

**关键代码量**：约 120 行

---

### Day 5 — 5月16日（周五）⏳ 2.5h
**主题：Context 管理（token 跟踪 + 历史压缩）**

- [ ] 实现 `src/context.py`：
  - `count_tokens(messages)`：用 `tiktoken` 统计整套 messages 的 token 数
  - `maybe_compress(messages, max_tokens)`：
    - 如果 token 数没超阈值 → 原样返回
    - 如果超了 → 保留 system + 第一条 user，只留最近 N 轮，中间丢弃
- [ ] 集成到 Agent Loop：
  - 每轮调用 LLM 前统计输入 token 数
  - 每次追加消息后检查是否超过阈值
  - 超过时自动执行压缩
- [ ] 测试：故意设置低阈值（如 2000 token），造一段长对话验证压缩是否生效

**关键代码量**：约 60 行

---

### Day 6 — 5月17日（周六）⏳ 2h（轻量日）
**主题：自由练习 / 补进度**

- [ ] 回顾前 5 天的代码，确保每个模块都理解
- [ ] 如果有没跑通的地方，今天优先修通
- [ ] 尝试让 Agent 用 file_ops 和 bash_exec 做一些简单组合任务
- [ ] 如果进度领先：提前看 Day 7 的内容

---

## 第二周：基础设施 + 打磨

### Day 7 — 5月18日（周日）休息
如果精力充沛可以提前看 Day 8 内容，但不强制。

---

### Day 8 — 5月19日（周一）⏳ 2.5h
**主题：日志系统 + Run ID**

- [ ] 实现 `src/logger.py`：
  - `init_run()` → 生成 `uuid4()` 作为 run_id，创建 `logs/traj_{run_id}.jsonl`
  - `log_event(run_id, event)` → 追加一行 JSON 到 jsonl
  - 事件类型：`agent_start`, `llm_request`, `llm_response`, `tool_call`, `tool_result`, `agent_end`, `error`
- [ ] 在 Agent Loop 中埋点：每个关键步骤都调用 `log_event()`
- [ ] 跑一次完整任务，打开 `.jsonl` 文件验证每一行都记录正确
- [ ] **里程碑**：能完整复盘一次 Agent 运行的所有细节

**关键代码量**：约 70 行

---

### Day 9 — 5月20日（周二）⏳ 2h
**主题：API 重试 + 成本统计**

- [ ] 在 `src/llm_client.py` 中加入重试逻辑：
  - `for attempt in range(max_retries):` 循环包裹 API 调用
  - 捕获 `openai.APITimeoutError`、`openai.RateLimitError`、`openai.APIConnectionError`
  - 用 `time.sleep(base_delay * (2 ** attempt))` 做指数退避
  - 不重试 `AuthenticationError`（401 没意义重试）
- [ ] 实现成本统计：
  - 每次 API 调用后记录 `input_tokens` 和 `output_tokens`
  - 累计到 run 结束，按模型单价计算美元成本
  - 在 Agent 结束时打印汇总：`Total: 12345 tokens, $0.42`
- [ ] 测试：故意断开网络，看重试是否生效

**关键代码量**：约 50 行

---

### Day 10 — 5月21日（周三）⏳ 3h
**主题：集成测试 + 复杂任务**

- [ ] 设计 3 个"集成测试场景"，覆盖所有工具和功能：
  1. **计算 + 文件**："计算 1 到 100 的累加和，把结果写到 `result.txt`"
  2. **Bash + 文件**："列出 workspace 下所有 .txt 文件，统计它们的总行数"
  3. **错误恢复**："算一下 100/0" → 期待模型看到 calculator 报错后自己修正
- [ ] 逐个场景跑通，修复遇到的 bug
- [ ] 检查日志文件是否完整记录了每次运行的轨迹
- [ ] **里程碑**：三个工具协同工作，Agent 稳定可靠

---

### Day 11 — 5月22日（周四）⏳ 2.5h
**主题：打磨 — 终端交互体验**

- [ ] 实现 `src/main.py` 入口：
  - `python main.py` → 交互模式，持续对话
  - `python main.py --task "计算 1+1"` → 单次模式，完成任务就退出
  - `python main.py --dry-run` → 不调 API，只打印会做什么（调试用）
- [ ] 终端输出美化（可选，用 `colorama` 或 `rich`）：
  - 不同角色用不同颜色：system 灰色、assistant 绿色、tool 蓝色、error 红色
- [ ] 加 `--verbose` 参数控制日志详细程度

**关键代码量**：约 60 行

---

### Day 12 — 5月23日（周五）⏳ 3h
**主题：安全加固 + 边界情况**

- [ ] **安全审查**：
  - calculator：确认 `ast.parse()` 白名单没有遗漏危险节点
  - file_ops：测试 `../../../etc/passwd` 等路径穿越攻击是否能被拦截
  - bash_exec：确认 `shell=False` 且危险命令黑名单生效
- [ ] **边界情况**：
  - 模型不调用工具直接给出答案时是否正常退出
  - 模型连续调用同一个工具很多次时是否卡死
  - 上下文压缩后模型是否丢失了关键信息
  - 超大工具输出（如 cat 一个大文件）是否被截断
- [ ] 补充 DESIGN.md 中"其他可补充的"你想到的任何功能

---

### Day 13 — 5月24日（周六）⏳ 2h
**主题：文档完善 + 代码整理**

- [ ] 通读所有代码，删除调试用的 `print()`，确保函数命名清晰
- [ ] 在 DESIGN.md 的"踩过的坑"部分记录整个项目中遇到的问题
- [ ] 在 DAILY_LOG.md 填写"总结与反思"
- [ ] 确保 `config.yaml` 里没有真实的 API key（如果有，改回占位符）
- [ ] 用 `python main.py --task "..."` 跑一次最终演示任务，截图保存

---

### Day 14 — 5月25日（周日）⏳ 1h
**主题：收尾 + 准备汇报**

- [ ] 运行最后一次完整测试
- [ ] 检查项目文件是否整洁（无临时文件、无敏感信息）
- [ ] 在 DAILY_LOG.md 写最终总结
- [ ] **交付物清单**：
  - 可运行的代码
  - [DESIGN.md](DESIGN.md) 设计文档
  - [DAILY_LOG.md](DAILY_LOG.md) 项目日志
  - [WORK_PLAN.md](WORK_PLAN.md) 本计划（勾选完成状态）
  - `logs/` 目录下至少 3 条完整 trajectory 日志作为演示

---

## 时间分配总览

```
Week 1  ████████████████████░░░░  核心功能开发      ~13h
Week 2  ████████████████████░░░░  基础设施 + 打磨   ~15h
        ────────────────────────
Total                            ~28h (每天约 2.3h)
```

| 模块 | 预计工时 | 难度 |
|------|---------|------|
| LLM Client | 2.5h | ⭐ |
| 三个工具 | 2.5h | ⭐⭐ |
| Agent Loop | 3h | ⭐⭐⭐ |
| Context 管理 | 2.5h | ⭐⭐ |
| 日志 + Run ID | 2.5h | ⭐ |
| 重试 + 成本 | 2h | ⭐ |
| 集成测试 | 3h | ⭐⭐⭐ |
| 打磨 + 安全 | 5.5h | ⭐⭐ |
| 文档 + 收尾 | 4.5h | ⭐ |

> **给你的建议**：最难的是 Day 4（Agent Loop），花再多时间也值得把它吃透。Loop 一旦跑通，后面的功能都是"往循环里加东西"，会越来越顺。
