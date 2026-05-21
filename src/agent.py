import json
from src.llm_client import chat
from src.tool_registry import init_tools,get_tools_schema,execute_tool
from src.config import AGENT,LLM
from src.logger import log_event,init_run
from src.context import (
    count_tokens,
    compress_messages_sliding_window,
    compress_messages_residual_connection,
    truncate_tool_result,
)
context_max_tokens = AGENT["context_max_tokens"]
def run(task: str, verbose: bool = True, messages:list | None = None ):
    if not hasattr(run,"_log_path"):
        run._log_path = None
        run._run_id = None
    if messages is None:
        run_id,path = init_run(log_dir = "logs")
        run._log_path = path
        run._run_id = run_id
        log_event(path,type = "agent_start",task = task,max_turns = AGENT["max_turns"],model = LLM["model"])
    else:
        path = run._log_path
        run_id = run._run_id
    sandbox_dir = AGENT["sandbox_dir"]
    max_turns = AGENT["max_turns"]
    
    init_tools(sandbox_dir)
    tools_schema = get_tools_schema()

    system_prompt = (
    f"运行id：{run_id}。"
    "你是一个具备工具调用能力的智能助手。"
    "你可以使用计算器、读写沙盒内的文件、在 Windows 沙盒中执行命令。"
    "请用中文回答用户，如果必须使用英文工具输出也请解释清楚。"
    "重要：你的当前工作目录就是沙盒根目录。"
    "文件路径和 bash 命令直接使用文件名或相对路径即可，不要添加 workspace/ 前缀。"
    "所有文件操作和命令执行都限制在沙盒内，遵守安全规则。"
)
    if messages is None:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task},
        ]
    else :
        messages.append({"role":"user","content":task})
    total_prompt = 0
    total_completion = 0
    for turn in range(max_turns):
        before_len = len(messages)
        before_tokens = count_tokens(messages)
        compress_fn = compress_messages_residual_connection
        if verbose and before_tokens > context_max_tokens:
            if compress_fn == compress_messages_residual_connection:
                print(f"  [Context] 触发压缩 ({before_tokens}tk > {context_max_tokens}tk)，生成残差摘要中...")
            else :
                print(f"  [Context] 触发压缩 ({before_tokens}tk > {context_max_tokens}tk)")
                
        messages = compress_fn(
            messages,
            keep_turns = 2,
            max_tokens = context_max_tokens,
        )
        if verbose and (len(messages) != before_len or count_tokens(messages) != before_tokens):
            print(f"  [Context] 压缩完成: {before_len}条({before_tokens}tk) → {len(messages)}条({count_tokens(messages)}tk)")
        log_event(path,type = "llm_request",turn = turn,tokens = count_tokens(messages))
        resp = chat(messages, tools=tools_schema)
        log_event(path,type = "llm_response",turn = turn,tokens = vars(resp.usage) if resp.usage else None)
        if resp.usage:
            total_prompt += resp.usage.prompt_tokens
            total_completion  += resp.usage.completion_tokens
        choice = resp.choices[0]

        if choice.message.tool_calls:
            if verbose:
                print(f"[Turn {turn + 1}] 模型调用了 {len(choice.message.tool_calls)} 个工具:")
            messages.append(choice.message.model_dump())

            for tool_call in choice.message.tool_calls:
                func_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                    log_event(path,type = "tool_call",turn = turn,name = func_name,args = args)
                except json.JSONDecodeError as e:
                    tool_result = {"success": False, "error": str(e)}
                    log_event(path,type = "error",message = str(e))
                else:
                    try:
                        tool_result = execute_tool(func_name, args)
                        
                    except Exception as e:
                        tool_result = {"success": False, "error": str(e)}
                        log_event(path,type = "error",message = str(e))

                if verbose:
                    status = "OK" if tool_result.get("success") else "FAIL"
                    result_preview = json.dumps(tool_result, ensure_ascii=False)[:120]
                    print(f"  {status} {func_name}({json.dumps(args, ensure_ascii=False)})")
                    print(f"      -> {result_preview}")
                if isinstance(tool_result,dict):
                    for key in ("content","output"):
                        if key in tool_result and isinstance(tool_result[key],str):
                            tool_result[key] = truncate_tool_result(tool_result[key])
                    log_event(path,type = "tool_result",turn = turn,result = tool_result)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })
            continue

        if choice.message.content is not None:
            log_event(path,type = "agent_end",result = choice.message.content,total_tokens = total_prompt + total_completion)
            if verbose:
                print(f"[Turn {turn + 1}] 模型给出最终答案")
                print(f"[总Token] prompt={total_prompt}, completion={total_completion}")
            return choice.message.content,messages

            

        if verbose:
            print(f"[总Token] prompt={total_prompt}, completion={total_completion}")
        log_event(path,type = "agent_end",result = choice.message.content,total_tokens = total_prompt + total_completion)
        return "模型无返回结果",messages
    log_event(path,type = "agent_end",result = choice.message.content,total_tokens = total_prompt + total_completion)
    if verbose:
        print(f"[总Token] prompt={total_prompt}, completion={total_completion}")
    return f"超过最大轮数限制({max_turns})，任务未完成",messages
    


