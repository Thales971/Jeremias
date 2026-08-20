from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"

DEFAULTS: dict[str, Any] = {
    "user_name": "chefe",
    "city": "Valinhos",
    "personality": "zueira",
    "language": "pt-BR",
    "xai_api_key": "",
    "openrouter_api_key": "",
    "groq_api_key": "",
    "wake_word": "jeremias",
    "voice_enabled": True,
    "voice_rate": 175,
}


def load() -> dict[str, Any]:
    data = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            data.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass
    env_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if env_key and not data.get("xai_api_key"):
        data["xai_api_key"] = env_key
    or_key = os.environ.get("OPENROUTER_API_KEY")
    if or_key and not data.get("openrouter_api_key"):
        data["openrouter_api_key"] = or_key
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key and not data.get("groq_api_key"):
        data["groq_api_key"] = groq_key
    if data.get("personality") not in ("zueira", "formal"):
        data["personality"] = "zueira"
    return data


def save(data: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
