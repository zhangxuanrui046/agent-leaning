import ast
import math

def safe_eval(expr: str)->float:
    tree = ast.parse(expr,mode = 'eval')
    allowed_nodes = {
        ast.Expression, #根节点
        ast.Constant,   #数字常量
        ast.UnaryOp,    #一元运算符
        ast.UAdd,       #正号
        ast.USub,       #负号
        ast.BinOp,      #二元运算符
        ast.Add,        #加法
        ast.Sub,        #减法
        ast.Mult,       #乘法
        ast.Div,        #除法
        ast.Mod,        #取模
        ast.Pow,        #幂
        ast.Call,       #函数调用
        ast.Name,       #函数名或变量名
        ast.Load,       #加载上下文

    }
    for node in ast.walk(tree):
        if type(node) not in allowed_nodes :
            raise ValueError(f"非法操作：{type(node).__name__}")
        if isinstance(node,ast.Call):
            if not isinstance(node.func,ast.Name):
                raise ValueError(f"非法函数调用")
            allowed_function = {'sin','cos','tan','sqrt','log','exp','abs','ceil','floor'}
            if node.func.id not in allowed_function:
                raise ValueError(f"不存在的函数调用：{node.func.id}")
    # 编译并执行
    code = compile(tree,'<string>','eval')
    # 注入math模块中的安全函数
    safe_locals = {f:getattr(math,f) for f in ['sin','cos','tan','sqrt','log','exp','ceil','floor']}
    safe_locals["pi"] = math.pi
    safe_locals["e"] = math.e
    safe_locals["abs"] = abs
    safe_globals = {"__builtins__":{}}
    return float(eval(code,safe_globals,safe_locals)) 
def calculate(expr:str)->dict:
    try:
        result = safe_eval(expr)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

