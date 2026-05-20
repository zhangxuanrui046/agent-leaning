"""calculator 工具测试"""
from src.tools.calculator import calculate

tests = [
    # === 正常运算 ===
    ("2+3", "简单加法"),
    ("2+3*4", "运算符优先级"),
    ("(2+3)*4", "括号"),
    ("2**10", "幂运算"),
    ("-5 + 3", "负数"),
    ("17 % 5", "取模"),
    # === 数学函数 ===
    ("sqrt(16)", "平方根"),
    ("sin(0)", "正弦"),
    ("cos(0)", "余弦"),
    ("log(1)", "自然对数"),
    ("exp(0)", "指数"),
    ("ceil(3.14)", "向上取整"),
    ("floor(3.14)", "向下取整"),
    ("abs(-10)", "绝对值"),
    # === 常量 ===
    ("pi", "圆周率"),
    ("e", "自然常数"),
    ("pi * 2", "常量运算"),
    # === 边界 & 错误 ===
    ("100/0", "除零"),
    ("1/0", "另一个除零写法"),
    ("sqrt(-1)", "负数开方"),
    ("1++", "语法错误"),
    ("", "空表达式"),
    # === 安全拦截 ===
    ("__import__('os')", "双下划线模块导入"),
    ("open('/etc/passwd')", "文件操作"),
    ("exec('print(1)')", "exec调用"),
    ("1+1; print('x')", "多语句"),
]

print("=" * 50)
print("calculator 单元测试")
print("=" * 50)

passed = 0
failed = 0

for expr, desc in tests:
    result = calculate(expr)
    if result["success"]:
        print(f"✅ {desc:12s} | {expr:30s} => {result['result']}")
        passed += 1
    else:
        print(f"❌ {desc:12s} | {expr:30s} => {result['error']}")
        failed += 1

print()
print(f"通过: {passed}, 失败(预期内): {failed}, 总计: {len(tests)}")
