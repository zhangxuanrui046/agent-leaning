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

## Day 5 — 2026-05-16（周五）

### 今日目标
- [ ] 

### 完成内容
- 

### 遇到的问题
- 

### 明天计划
- [ ] 

---

## Day 6 — 2026-05-17（周六）

### 今日目标
- [ ] 

### 完成内容
- 

### 遇到的问题
- 

---

## 总结与反思（项目结束后填写）

### 学到了什么
- 

### 踩过的坑
- 

### 如果重来一次，会怎么做
- 
