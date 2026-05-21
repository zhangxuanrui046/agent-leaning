import openai
import time
from .config import LLM,RETRY

_client = openai.OpenAI(
    api_key=LLM["api_key"],
    base_url=LLM["base_url"],
)

def chat(messages: list[dict], tools: list[dict] | None = None) -> dict:
    kwargs = {}
    if tools:
        kwargs["tools"] = tools
    max_retries = RETRY["max_retries"]
    base_delay = RETRY["base_delay"]
    for attempt in range(max_retries + 1):
        try:
            response = _client.chat.completions.create(
                model=LLM["model"],
                messages=messages,
                max_tokens=LLM["max_tokens"],
                temperature=LLM["temperature"],
                **kwargs,
            )
            return response
        except (openai.APITimeoutError,
                openai.RateLimitError,
                openai.APIConnectionError) as e:
            if attempt == max_retries:
                raise
            time.sleep(base_delay * (2 ** attempt))
    
    
    
