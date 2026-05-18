import subprocess
import shlex
import os
from pathlib import Path


FORBIDDEN_COMMANDS = {
    "rm", "rmdir", "del", "format", "shutdown", "reboot", "chmod", "chown", "sudo", "su"
}
CMD_BUILTINS = {
    "dir", "mkdir", "md", "rmdir", "rd",
    "type", "echo", "copy", "move", "rename", "ren",
    "cd", "chdir", "set", "cls", "date", "time",
    "find", "findstr", "more", "sort", "comp", "fc",
    "ver", "vol", "title", "color", "mklink",
    "where", "whoami", "hostname",
}

def bash_exec(command:str,sandbox_dir:str,timeout: int  = 30)->dict:
    SANDBOX_DIR = Path(sandbox_dir).resolve()
    SANDBOX_DIR.mkdir(parents = True,exist_ok = True)
    command = command.strip()
    if not command:
        return {"success": False, "error": "错误：命令为空"}
    try:
        tokens = shlex.split(command)
    except ValueError as e:
        return {"success": False, "error": str(e)}
    if not tokens:
        return {"success": False, "error": "错误：命令为空"}

    cmd_name = os.path.basename(tokens[0])
    if cmd_name.lower()  in FORBIDDEN_COMMANDS:
        return {"success": False, "error": f"错误：命令'{cmd_name}'是危险命令"}
    if cmd_name.lower() in CMD_BUILTINS:
        tokens = ["cmd","/c"] + tokens
    try:
        env = os.environ.copy()
        env["HOME"] = str(SANDBOX_DIR)
        env["PWD"] = str(SANDBOX_DIR)

        proc = subprocess.run(
            tokens,
            shell = False,
            cwd = str(SANDBOX_DIR),
            env = env,
            capture_output = True,
            text = True,
            encoding = "utf-8",
            errors = "replace",
            timeout = timeout,
            input = None,
        )
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "错误，命令执行超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    output = proc.stdout
    if(proc.stderr):
        output += "\n[STDERR]\n"+proc.stderr
    return {"success": True, "output": output}
    
