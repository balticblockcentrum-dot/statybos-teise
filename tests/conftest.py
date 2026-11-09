import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lex import config


@pytest.fixture
def provisions():
    return [
        {
            "id": "ck-6-644", "law": "LR civilinis kodeksas", "article": "6.644",
            "title": "Rangos sutarties samprata", "citation": "CK 6.644 str.",
            "text": "Rangos sutartis: rangovas įsipareigoja atlikti darbą pagal užsakovo užduotį, o užsakovas priima rezultatą ir sumoka kainą.",
        },
        {
            "id": "ck-6-71", "law": "LR civilinis kodeksas", "article": "6.71",
            "title": "Netesybos", "citation": "CK 6.71 str.",
            "text": "Netesybos yra piniginė suma už prievolės neįvykdymą ar termino praleidimą (delspinigiai, bauda).",
        },
        {
            "id": "ck-6-154", "law": "LR civilinis kodeksas", "article": "6.154",
            "title": "Sutarčių laisvė", "citation": "CK 6.154 str.",
            "text": "Šalys laisvai sudaro sutartis ir nustato tarpusavio teises bei pareigas (sutarčių laisvė).",
        },
    ]


@pytest.fixture
def tmp_project(monkeypatch, tmp_path, provisions):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    cfg = {
        "llm": {"base_url": "https://example.test/v1", "model": "test-model", "temperature": 0.2},
        "corpus": {"dir": "data", "tar_dataset": "https://data.gov.lt/datasets/2613/"},
        "update": {"app_manifest_url": "https://example.test/manifest.json"},
    }
    (tmp_path / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    corpus = {"meta": {"note": "test", "updated": "2026-01-01"}, "provisions": provisions}
    (data_dir / "corpus.json").write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    return tmp_path