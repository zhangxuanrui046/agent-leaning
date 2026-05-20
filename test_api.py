"""交互式 Agent 测试 —— 通过 agent.run() 调用 LLM + 工具"""
from src.config import LLM
from src.agent import run

print(f"模型: {LLM['model']}")
print(f"地址: {LLM['base_url']}")
print("输入 'quit' 或 'exit' 退出")
print("-" * 40)

messages = None
while True:
    user_input = input("\n你: ")
    if user_input.lower() in ("quit", "exit"):
        print("再见！")
        break
    if user_input.lower() == "clear":
        messages = None
        print("对话已重置")
        continue
    if not user_input.strip():
        continue

    reply,messages = run(user_input,messages = messages)
    print(f"\n模型: {reply}")
