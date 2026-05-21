# Python Agent 系统

> 从零实现，不依赖 LangChain 等框架。

---

## 摘要

本项目用纯 Python 实现了一个可与大语言模型（GPT-5.5）交互、自主调用工具、完成复杂任务的 Agent 系统。核心架构包括四层：**Agent Loop**（ReAct 循环，控制思考→行动→观察的节奏）、**Tool Registry**（4 个工具的统一注册与调度：安全计算器、沙箱文件读写、Windows 命令执行）、**Context Manager**（tiktoken 计数 + 滑动窗口 + 残差连接两种压缩策略）、**Infra Layer**（JSONL 轨迹日志、API 指数退避重试、token/$ 成本统计、唯一 run_id）。在上下文压缩方面，受 ResNet 残差连接启发，提出了用 LLM 实时摘要替代传统滑动窗口占位符的方案，实验对比表明残差连接的稳定性和信息保留度显著优于纯滑动窗口。项目全部原始需求 100% 完成，部分超出。

---

## 快速开始

### 环境

- Python 3.10+
- Windows / Linux / macOS

### 安装

```bash
pip install openai tiktoken pyyaml
```

### 配置

编辑 `config.yaml`，填入 API 信息：

```yaml
llm:
  api_key: "your-key"
  base_url: "https://your-api.com/v1"
  model: "gpt-5.5"
```

### 运行

```bash
# 交互模式（持续对话，输入 clear 重置，exit 退出）
python test_api.py

# 单次任务
python -c "from src.agent import run; print(run('计算 123*456')[0])"

# 运行测试
python test_context.py      # context 28 个单元测试
python test_calculator.py    # 计算器边界测试
python test_file_ops.py      # 文件操作边界测试
python test_bash_exec.py     # bash 执行边界测试
python test_retry.py         # API 重试验证
```

---

## 项目结构

```
agent/
├── config.yaml              # 配置文件（API、agent、pricing）
├── src/
│   ├── agent.py             # Agent Loop 核心（144 行）
│   ├── llm_client.py        # LLM API 封装 + 指数退避重试
│   ├── tool_registry.py     # 工具注册 + Schema 自动生成
│   ├── context.py           # Token 计数 + 滑动窗口/残差连接压缩
│   ├── logger.py            # JSONL 轨迹日志 + run_id
│   ├── config.py            # 配置加载器
│   └── tools/
│       ├── calculator.py    # 安全计算器（AST 白名单）
│       ├── file_ops.py      # 沙箱文件读写
│       └── bash_exec.py     # Windows 命令执行（沙箱 + 黑名单）
├── logs/                    # 运行时轨迹日志
├── workspace/               # 文件操作沙箱目录
├── DESIGN.md                # 系统设计文档
├── DAILY_LOG.md             # 每日开发日志
├── FINAL_REPORT.md          # 最终审计报告
└── TABLES.md                # 报告用表格
```

---

## 核心特性

| 模块 | 特性 |
|------|------|
| Agent Loop | ReAct 模式，3 种停止条件，工具报错自动恢复，多轮对话记忆 |
| Tools | calculator / file_read / file_write / bash_exec，沙箱隔离，路径穿越防护 |
| Context | 两种压缩策略（滑动窗口 + ResNet 启发式残差连接），工具结果截断 |
| Infra | trajectory JSONL 日志、API 指数退避重试、token/$ 成本、唯一 run_id |

---

## 关键技术点

- **安全计算器**：`ast.parse()` 白名单校验 + `__builtins__: {}` 禁用，防止代码注入
- **沙箱文件操作**：`Path.resolve()` + `relative_to()` 路径穿越防护
- **安全命令执行**：`subprocess.run(shell=False)` + 危险命令黑名单 + cmd 内置自动包装
- **残差连接压缩**：受 ResNet `y = F(x) + x` 启发，将丢弃的中间轮次用 LLM 蒸馏为结构化摘要接回上下文，比纯滑动窗口更稳定
- **API 重试**：指数退避 1s→2s→4s，只重试可恢复错误
- **run_id**：`%Y%m%d-%H%M%S-序号` 格式，日志文件名与条目双重关联

---

## 环境信息

| 项目 | 内容 |
|------|------|
| 操作系统 | Windows 11 |
| Python | 3.10.11 |
| 核心依赖 | openai 2.36.0 / tiktoken 0.12.0 / PyYAML 6.0.3 |
| 模型 | GPT-5.5（上下文窗口 1,050,000 tokens） |
| 代码量 | 10 个源文件，约 740 行 |
