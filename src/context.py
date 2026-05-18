import tiktoken
import json
from typing import Any
# token计数
def count_tokens(messages:list[dict[str,Any]],model:str = "gpt5.5")->int:
    encoding_name = "cl100k_base"
    encoding = tiktoken.get_encoding(encoding_name)
    tokens_per_message = 3 #每条消息的额外开销，约 3 token
    tokens_per_name = 1 #name字段开销
    total = 0
    for msg in messages:
        total += tokens_per_message
        for key,value in msg.items():
            if key == "role":
                total += len(encoding.encode(value))
            elif key == "content":
                if isinstance(value,str):
                    total += len(encoding.encode(value))
                elif isinstance(value,list):
                    for part in value:
                        if(isinstance(part,dict)) and "text" in part:
                            total += len(encoding.encode(part["text"]))
            elif key == "name":
                total += tokens_per_name
            elif key == "tool_calls":
                total += len(encoding.encode(json.dumps(value,ensure_ascii = False)))
            elif key == "tool_call_id":
                total += len(encoding.encode(value))
    total += 3
    return total

# 消息切分：提取 system、首条 user、保留的尾轮、被丢弃的中间消息
def _split_messages(
    messages: list[dict[str, Any]],
    keep_turns: int,
) -> dict:
    system_msg = None
    first_user_msg = None
    start_idx = 0
    if messages[0].get("role") == "system":
        system_msg = messages[0]
        start_idx = 1

    history_start = start_idx
    for i in range(start_idx, len(messages)):
        if messages[i]["role"] == "user":
            first_user_msg = messages[i]
            history_start = i + 1
            break

    # 从后向前扫描完整的轮次
    turns = []          # turns[0]=最新轮, turns[-1]=最旧轮
    current_turn = []
    i = len(messages) - 1
    while i >= history_start and len(turns) < keep_turns:
        msg = messages[i]
        role = msg.get("role")

        if role == "tool":
            current_turn.append(msg)
            i -= 1
        elif role == "assistant" and msg.get("tool_calls"):
            current_turn.append(msg)
            turns.append(list(reversed(current_turn)))
            current_turn = []
            i -= 1
        elif role == "assistant" and not msg.get("tool_calls"):
            i -= 1
        elif role == "user":
            current_turn = []
            i -= 1
        else:
            break

    # 中间被丢弃的消息 = history_start 到 i+1（扫描停止位置）
    middle_end = i + 1
    if middle_end < history_start:
        middle_end = history_start
    middle_messages = messages[history_start:middle_end]

    return {
        "system_msg": system_msg,
        "first_user_msg": first_user_msg,
        "turns": turns,
        "middle": middle_messages,
    }


# 组装：拼接 head + 占位符 + tail_turns，并按阈值进一步削轮次
def _assemble(
    system_msg: dict | None,
    first_user_msg: dict | None,
    turns: list,
    placeholder_text: str,
    max_tokens: int,
) -> list[dict[str, Any]]:
    compressed = []
    if system_msg:
        compressed.append(system_msg)
    if first_user_msg:
        compressed.append(first_user_msg)
    if turns:
        placeholder = {"role": "user", "content": placeholder_text}
        compressed.append(placeholder)
    for turn in reversed(turns):
        compressed.extend(turn)

    # 若仍超 0.8 倍阈值，继续丢弃最早轮次
    while (
        len(turns) > 1
        and count_tokens(compressed) > max_tokens * 0.8
    ):
        turns.pop()
        compressed = []
        if system_msg:
            compressed.append(system_msg)
        if first_user_msg:
            compressed.append(first_user_msg)
        if turns:
            placeholder = {"role": "user", "content": placeholder_text}
            compressed.append(placeholder)
        for turn in reversed(turns):
            compressed.extend(turn)

    return compressed


# 压缩核心逻辑（公共）
def _compress_core(
    messages: list[dict[str, Any]],
    keep_turns: int = 2,
    max_tokens: int = 8000,
    placeholder_text: str = "[系统提示] 之前的对话历史因长度限制已被压缩。请基于当前可见的上下文继续执行任务。",
) -> list[dict[str, Any]]:
    if not messages:
        return []
    if count_tokens(messages) <= max_tokens:
        return messages
    parts = _split_messages(messages, keep_turns)
    return _assemble(
        parts["system_msg"],
        parts["first_user_msg"],
        parts["turns"],
        placeholder_text,
        max_tokens,
    )

def _format_middle(messages):
    lines = []
    for msg in messages:
        role = msg.get("role")
        if role == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                func = tc["function"]["name"]
                args = tc["function"]["arguments"]
                lines.append(f"调用{func}{args}")
        elif role == "tool":
            content  = msg.get("content","")
            try:
                data = json.loads(content)
                if data.get("success"):
                    # 提取关键字段：result、output、path
                    key_info = {}
                    for k in {"result","output","path"}:
                        if k in data:
                            key_info[k] = data[k]
                    lines.append(f"->成功：{json.dumps(key_info,ensure_ascii = False)}")
                else:
                    lines.append(f"->失败：{data.get('error','')[:80]}")
            except (json.JSONDecodeError,TypeError):
                lines.append(f"->{content[:120]}")
    return "\n".join(lines)


# 摘要生成：调 LLM 将中间轮次蒸馏为要点
def _generate_summary(middle_messages: list[dict[str, Any]]) -> str:
    from src.llm_client import chat

    summary_prompt = (
        "你是一个对话压缩器。以下是一段 Agent 与工具交互的历史记录。"
        "请用 2~5 条简洁的要点（每条以 '- ' 开头）总结其中已完成的关键操作和结果。"
        "只记录事实，不要推测或补充。"
    )
    formatted = _format_middle(middle_messages)
    summary_msgs = [
        {"role": "system", "content": summary_prompt},
        {"role": "user", "content": formatted},
    ]
    try:
        resp = chat(summary_msgs)  # 不带 tools
        return resp.choices[0].message.content.strip()
    except Exception:
        raise  # 由调用方决定回退策略


# 滑动窗口压缩
def compress_messages_sliding_window(
    messages: list[dict[str, Any]],
    keep_turns: int = 2,
    max_tokens: int = 8000,
) -> list[dict[str, Any]]:
    return _compress_core(messages, keep_turns, max_tokens,
        placeholder_text="[系统提示] 之前的对话历史因长度限制已被压缩。请基于当前可见的上下文继续执行任务。")

# 残差连接压缩
def compress_messages_residual_connection(
    messages: list[dict[str, Any]],
    keep_turns: int = 2,
    max_tokens: int = 8000,
) -> list[dict[str, Any]]:
    if not messages:
        return []
    if count_tokens(messages) <= max_tokens:
        return messages

    parts = _split_messages(messages, keep_turns)
    middle = parts["middle"]

    if middle:
        try:
            summary = _generate_summary(middle)
            placeholder_text = (
                f"[上下文摘要] 以下操作已完成：\n{summary}\n\n"
                "请基于以上历史和后续对话继续执行任务。"
            )
        except Exception:
            placeholder_text = (
                "[系统提示] 之前的对话历史因长度限制已被压缩。"
                "请基于当前可见的上下文继续执行任务。"
            )
    else:
        placeholder_text = (
            "[系统提示] 之前的对话历史因长度限制已被压缩。"
            "请基于当前可见的上下文继续执行任务。"
        )

    return _assemble(
        parts["system_msg"],
        parts["first_user_msg"],
        parts["turns"],
        placeholder_text,
        max_tokens,
    )

# 如果工具返回内容过长，应予以截断，防止过长上下文
def truncate_tool_result(content:str,max_chars:int = 2000)->str:
    if len(content) <= max_chars:
        return content
    else:
        truncated = content[:max_chars]
        return f"{truncated}...[内容已截断，原文{len(content)}个字符]"
