import io
import json
import urllib.error

import pytest

from lex import config, llm


@pytest.fixture
def llm_setup(monkeypatch, tmp_project):
    monkeypatch.setattr(config, "get_api_key", lambda: "FAKE-KEY")
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    return tmp_project


def _response(content):
    body = {"choices": [{"message": {"content": content}}]}
    return io.BytesIO(json.dumps(body).encode("utf-8"))


def test_analyze_success_builds_request(monkeypatch, llm_setup):
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        captured["auth"] = req.headers.get("Authorization")
        return _response("Teisinis atsakymas su CK 6.644 str.")

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    provisions = [{"citation": "CK 6.644 str.", "title": "Ranga", "text": "Rangos tekstas"}]
    out = llm.analyze("Dokumentas", provisions, task="analyze")
    assert out == "Teisinis atsakymas su CK 6.644 str."
    assert captured["url"].endswith("/chat/completions")
    assert captured["auth"] == "Bearer FAKE-KEY"
    assert captured["payload"]["model"] == "test-model"
    assert "CK 6.644 str." in captured["payload"]["messages"][1]["content"]


def test_analyze_no_key_raises(monkeypatch, tmp_project):
    monkeypatch.setattr(config, "get_api_key", lambda: None)
    with pytest.raises(RuntimeError, match="API rakto"):
        llm.analyze("doc", [])


def test_analyze_retries_on_503(monkeypatch, llm_setup):
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(req.full_url, 503, "Service Unavailable", {}, io.BytesIO(b""))
        return _response("OK po pakartojimo")

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    out = llm.analyze("doc", [{"citation": "C", "title": "T", "text": "X"}])
    assert out == "OK po pakartojimo"
    assert calls["n"] == 2


def test_analyze_raises_on_400(monkeypatch, llm_setup):
    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {}, io.BytesIO(b""))

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(urllib.error.HTTPError):
        llm.analyze("doc", [{"citation": "C", "title": "T", "text": "X"}])