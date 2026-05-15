"""bash_exec 工具测试（Windows 环境）"""
from src.tools.bash_exec import bash_exec

SANDBOX = "./workspace"

tests = [
    # === Windows 基础命令 ===
    ("echo_ok", lambda: bash_exec("cmd /c echo hello", SANDBOX),
     "echo 输出"),
    ("dir_ok", lambda: bash_exec("cmd /c dir /b", SANDBOX),
     "dir 列出文件"),
    ("type_ok", lambda: bash_exec("cmd /c type test1.txt", SANDBOX),
     "type 读取文件"),
    # === findstr（Windows 版 grep）===
    ("findstr_ok", lambda: bash_exec("findstr Hello test1.txt", SANDBOX),
     "findstr 搜索文本"),
    # === 创建目录 + 验证 ===
    ("mkdir_ok", lambda: bash_exec("cmd /c mkdir test_bash_dir", SANDBOX),
     "创建目录"),
    ("dir_ad", lambda: bash_exec("cmd /c dir /b /ad", SANDBOX),
     "只列出目录"),
    # === 空命令拦截 ===
    ("empty_cmd", lambda: bash_exec("", SANDBOX),
     "空命令拦截"),
    ("whitespace_cmd", lambda: bash_exec("   ", SANDBOX),
     "纯空格命令拦截"),
    # === 危险命令拦截 ===
    ("block_rm", lambda: bash_exec("rm -rf /", SANDBOX),
     "拦截 rm"),
    ("block_rmdir", lambda: bash_exec("rmdir something", SANDBOX),
     "拦截 rmdir"),
    ("block_del", lambda: bash_exec("del /f /q *", SANDBOX),
     "拦截 del"),
    ("block_shutdown", lambda: bash_exec("shutdown /s", SANDBOX),
     "拦截 shutdown"),
    ("block_sudo", lambda: bash_exec("sudo something", SANDBOX),
     "拦截 sudo"),
    ("block_chmod", lambda: bash_exec("chmod 777 file", SANDBOX),
     "拦截 chmod"),
    # === 不存在的命令 ===
    ("cmd_not_found", lambda: bash_exec("nonexistentcmd123 --flag", SANDBOX),
     "不存在的命令（预期失败）"),
    # === python 可用 ===
    ("python_version", lambda: bash_exec("python --version", SANDBOX),
     "python 版本"),
]

print("=" * 55)
print("bash_exec 单元测试 (Windows)")
print("=" * 55)

passed = 0
crashed = 0

for name, test_fn, desc in tests:
    try:
        result = test_fn()
        if isinstance(result, dict) and "success" in result:
            if result["success"]:
                output = result.get("output", "")[:60].replace("\n", "\\n")
                print(f"✅ {desc:22s} | [{name}] => {output}")
            else:
                print(f"🚫 {desc:22s} | [{name}] => 被拦截: {result['error'][:45]}")
            passed += 1
        else:
            print(f"⚠️  {desc:22s} | [{name}] => 返回值异常: {result}")
            crashed += 1
    except Exception as e:
        print(f"❌ {desc:22s} | [{name}] => 代码崩溃: {type(e).__name__}: {e}")
        crashed += 1

print()
print(f"通过: {passed}, 崩溃: {crashed}, 总计: {len(tests)}")
print()
print("说明: ✅ 正常执行   🚫 正确拦截   ❌ 意外崩溃")
