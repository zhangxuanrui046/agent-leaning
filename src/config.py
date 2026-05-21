from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    _cfg = yaml.safe_load(f)

LLM = _cfg["llm"]
AGENT = _cfg["agent"]
RETRY = _cfg["retry"]
LOGGING = _cfg["logging"]
PRICING = _cfg["pricing"]
