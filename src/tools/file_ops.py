import os
from pathlib import Path

WORKSPACE_DIR = Path("./workspace").resolve()
WORKSPACE_DIR.mkdir(parents = True,exist_ok = True)

def safe_resolve_path(user_path:str)->Path:
    #去掉用户输入的'/'或'\',防止绝对路径
    user_path = user_path.lstrip("/\\")
    full_path = (WORKSPACE_DIR/user_path).resolve() #拼接成新的绝对路径
    try:
        full_path.relative_to(WORKSPACE_DIR)
    except ValueError:
        raise PermissionError("路径越界")
    return full_path

def file_read(path:str)->dict:
    try:
        file_path = safe_resolve_path(path)
        if not file_path.is_file():
            return {"success": False, "error": f"错误：文件不存在 - {file_path.relative_to(WORKSPACE_DIR)}"}
        with open(file_path,'r',encoding='utf-8') as f:
            content = f.read()
        return  {"success": True, "path":str(file_path), "content": content}
    except PermissionError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def file_write(path:str,content:str)->dict:
    try:
        file_path = safe_resolve_path(path)
        file_path.parent.mkdir(parents = True,exist_ok = True)
        with open(file_path,'w',encoding='utf-8') as f:
            f.write(content)
        return  {"success": True, "path":str(file_path)}
    except PermissionError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}



