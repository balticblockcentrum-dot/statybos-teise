import json
import urllib.request
from datetime import date
from pathlib import Path

from . import config


def check_online(url="https://www.e-tar.lt/"):
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            return r.status == 200
    except Exception:
        return False


def _corpus_path():
    return config.ROOT / config.load_config()["corpus"]["dir"] / "corpus.json"


def sync_from_export(export_path):
    """Prijungia oficialų TAR eksportą (JSON sąrašas arba {'provisions': [...]})."""
    with open(export_path, encoding="utf-8") as f:
        incoming = json.load(f)
    if isinstance(incoming, dict):
        incoming = incoming.get("provisions", [])
    data = json.loads(_corpus_path().read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in data["provisions"]}
    added = 0
    for p in incoming:
        if not p.get("id"):
            continue
        if p["id"] not in by_id:
            added += 1
        by_id[p["id"]] = p
    data["provisions"] = list(by_id.values())
    data["meta"]["updated"] = date.today().isoformat()
    _corpus_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return added, len(data["provisions"])


def refresh_meta():
    if not check_online():
        return False
    data = json.loads(_corpus_path().read_text(encoding="utf-8"))
    data["meta"]["updated"] = date.today().isoformat()
    _corpus_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True