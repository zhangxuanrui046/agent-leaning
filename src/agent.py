import json
from src.llm_client import chat
from src.tool_registry import init_tools,get_tools_schema,execute_tool
from src.config import AGENT

def run(task: str, verbose: bool = True) -> str:
    sandbox_dir = AGENT["sandbox_dir"]
    max_turns = AGENT["max_turns"]
    init_tools(sandbox_dir)
    tools_schema = get_tools_schema()

    system_prompt = (
        "你是一个具备工具调用能力的智能助手。"
        "你可以使用计算器、读写沙盒内的文件、在 Windows 沙盒中执行命令。"
        "请用中文回答用户，如果必须使用英文工具输出也请解释清楚。"
        "所有文件操作和命令执行都限制在沙盒内，遵守安全规则。"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]
    for turn in range(max_turns):
        resp = chat(messages, tools=tools_schema)
        choice = resp.choices[0]

        if choice.message.tool_calls:
            if verbose:
                print(f"[Turn {turn + 1}] 模型调用了 {len(choice.message.tool_calls)} 个工具:")
            messages.append(choice.message.model_dump())

            for tool_call in choice.message.tool_calls:
                func_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError as e:
                    tool_result = {"success": False, "error": str(e)}
                else:
                    try:
                        tool_result = execute_tool(func_name, args)
                    except Exception as e:
                        tool_result = {"success": False, "error": str(e)}

                if verbose:
                    status = "OK" if tool_result.get("success") else "FAIL"
                    result_preview = json.dumps(tool_result, ensure_ascii=False)[:120]
                    print(f"  {status} {func_name}({json.dumps(args, ensure_ascii=False)})")
                    print(f"      -> {result_preview}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })
            continue

        if choice.message.content is not None:
            if verbose:
                print(f"[Turn {turn + 1}] 模型给出最终答案")
            return choice.message.content

        return "模型无返回结果"

    return f"超过最大轮数限制({max_turns})，任务未完成"


