from src.config import LLM
from src.agent import run

print(f"模型: {LLM['model']}")
print(f"地址: {LLM['base_url']}")
print("输入 'quit' 或 'exit' 退出")
print("-" * 40)

while True:
    user_input = input("\n你: ")
    if user_input.lower() in ("quit", "exit"):
        print("再见！")
        break
    if not user_input.strip():
        continue

    reply = run(user_input)
    print(f"\n模型: {reply}")
