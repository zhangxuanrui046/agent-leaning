from src.config import LLM
from src.llm_client import chat

print(f"模型: {LLM['model']}")
print(f"地址: {LLM['base_url']}")
print("输入 'quit' 或 'exit' 退出")
print("-" * 40)

messages = []  # 保存对话历史，实现多轮对话

while True:
    user_input = input("\n你: ")
    if user_input.lower() in ("quit", "exit"):
        print("再见！")
        break
    if not user_input.strip():
        continue

    messages.append({"role": "user", "content": user_input})
    resp = chat(messages)
    reply = resp.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})

    print(f"\n模型: {reply}")
