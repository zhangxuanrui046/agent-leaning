import openai
from .config import LLM

_client = openai.OpenAI(
    api_key=LLM["api_key"],
    base_url=LLM["base_url"],
)

def chat(messages: list[dict]) -> dict:
    response = _client.chat.completions.create(
        model=LLM["model"],
        messages=messages,
        max_tokens=LLM["max_tokens"],
        temperature=LLM["temperature"],
    )
    return response
