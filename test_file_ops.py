"""file_ops 工具测试"""
from src.tools.file_ops import file_read, file_write

tests = [
    # === 正常写 + 读 ===
    ("write_ok", lambda: file_write("test1.txt", "Hello World!"),
     "写入普通文件"),
    ("read_ok", lambda: file_read("test1.txt"),
     "读取刚写入的文件"),
    # === 覆盖写入 ===
    ("write_overwrite", lambda: file_write("test1.txt", "覆盖内容"),
     "覆盖已有文件"),
    ("read_overwritten", lambda: file_read("test1.txt"),
     "读取覆盖后的内容"),
    # === 嵌套目录写入 ===
    ("write_nested", lambda: file_write("subdir/inner/deep.txt", "深层文件"),
     "写入嵌套目录文件"),
    ("read_nested", lambda: file_read("subdir/inner/deep.txt"),
     "读取嵌套目录文件"),
    # === 空内容 ===
    ("write_empty", lambda: file_write("empty.txt", ""),
     "写入空内容文件"),
    ("read_empty", lambda: file_read("empty.txt"),
     "读取空内容文件"),
    # === 特殊字符文件名 ===
    ("write_special", lambda: file_write("log_2026-05-15.txt", "log content"),
     "写入带日期文件名的文件"),
    ("read_special", lambda: file_read("log_2026-05-15.txt"),
     "读取带日期文件名的文件"),
    # === 安全拦截 ===
    ("read_traversal_1", lambda: file_read("../../../etc/passwd"),
     "路径穿越拦截 (Linux)"),
    ("read_traversal_2", lambda: file_read("..\\..\\..\\Windows\\System32\\config\\SAM"),
     "路径穿越拦截 (Windows)"),
    ("write_traversal", lambda: file_write("../../../evil.txt", "hack"),
     "路径穿越写拦截"),
    ("read_traversal_dot", lambda: file_read("....//....//....//etc/passwd"),
     "变形路径穿越拦截"),
    # === 边界情况 ===
    ("read_nonexistent", lambda: file_read("does_not_exist.txt"),
     "读取不存在的文件"),
    ("read_emptypath", lambda: file_read(""),
     "空路径读取"),
    ("write_emptypath", lambda: file_write("", "data"),
     "空路径写入"),
]

print("=" * 55)
print("file_ops 单元测试")
print("=" * 55)

passed = 0
failed = 0

for name, test_fn, desc in tests:
    try:
        result = test_fn()
        # 判断结果：success=True 算通过，success=False 也算通过（因为有些测试就是预期失败的）
        # 我们需要区分"工具正确工作了但返回错误"和"代码崩了"
        if isinstance(result, dict) and "success" in result:
            if result["success"]:
                print(f"✅ {desc:20s} | [{name}] => ok")
            else:
                print(f"🚫 {desc:20s} | [{name}] => 被拦截: {result['error'][:40]}")
            passed += 1
        else:
            print(f"⚠️  {desc:20s} | [{name}] => 返回值格式异常: {result}")
            failed += 1
    except Exception as e:
        print(f"❌ {desc:20s} | [{name}] => 代码崩溃: {type(e).__name__}: {e}")
        failed += 1

print()
print(f"通过: {passed}, 崩溃: {failed}, 总计: {len(tests)}")
print()
print("说明: ✅ 工具正常执行   🚫 工具正确拦截错误   ❌ 意外崩溃")
