import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVICE = "statybos_teise_llm"
KEY_USER = "api_key"


def load_config():
    with open(ROOT / "config.json", encoding="utf-8") as f:
        return json.load(f)


def get_api_key():
    try:
        import keyring
        return keyring.get_password(SERVICE, KEY_USER) or os.environ.get("LEX_LLM_API_KEY")
    except Exception:  # noqa: BLE001 — keyring gali būti neprieinamas, tada env
        return os.environ.get("LEX_LLM_API_KEY")


def set_api_key(key):
    import keyring
    keyring.set_password(SERVICE, KEY_USER, key)