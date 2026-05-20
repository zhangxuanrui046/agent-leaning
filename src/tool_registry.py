import inspect
from typing import Any,get_type_hints
from functools import partial

#类型映射
_TYPE_MAP: dict[type,str] = {
    str:"string",
    int:"integer",
    float:"number",
    bool:"boolean",
}
#工具描述
_TOOL_DESCRIPTIONS: dict[str, str] = {
    "calculator": "安全计算数学表达式，支持 + - * / () 以及 sin, cos, sqrt 等数学函数。",
    "file_read": "读取沙盒内指定文件的内容，返回文本。",
    "file_write": "将文本内容写入沙盒内的指定文件，会自动创建父目录。",
    "bash_exec": "在 Windows 沙盒环境中执行一条命令（使用 cmd /c），可以调用 dir、type、findstr 等内置命令。",
}
#全局注册表
_tools: dict[str,callable] = {}

#工具注册函数
def init_tools(sandbox_dir:str):
    from .tools import calculator
    from .tools import file_ops
    from .tools import bash_exec
    _tools["calculator"] = calculator.calculate
    _tools["file_read"] = partial(file_ops.file_read,sandbox_dir = sandbox_dir)
    _tools["file_write"] = partial(file_ops.file_write,sandbox_dir = sandbox_dir)
    _tools["bash_exec"] = partial(bash_exec.bash_exec,sandbox_dir = sandbox_dir)

#生成OpenAI兼容的工具列表
def get_tools_schema()->list[dict[str,any]]:
    schemas = []
    for tool_name,func in _tools.items():
        sig = inspect.signature(func)
        inner = func.func if isinstance(func,partial) else func
        hints = get_type_hints(inner)

        properties = {}
        required=  []
        for param_name,param in sig.parameters.items():
            if param_name == "sandbox_dir":
                continue
            py_type = hints.get(param_name,str)
            json_type = _TYPE_MAP.get(py_type,"string")

            properties[param_name] = {
                "type":json_type,
                "description":f"{param_name}参数",
            } 

            if param.default is inspect.Parameter.empty:
                required.append(param_name)
        schema = {
            "type":"function",
            "function":{
                "name":tool_name,
                "description":_TOOL_DESCRIPTIONS.get(tool_name, f"执行 {tool_name} 工具"),
                "parameters":{
                    "type":"object",
                    "properties":properties,
                    "required":required,
                },
            },
        }

        schemas.append(schema)
    return schemas


#工具调用
def execute_tool(name:str,args:dict)->dict:
    tool = _tools.get(name)
    if tool is None:
        return {"success":False,"error":f"未知工具:{name}"}
    try:
        result = tool(**args)
        return result
    except Exception as e:
        return {"success":False,"error":str(e)}
