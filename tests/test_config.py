import keyring

from lex import config


def test_load_config(tmp_project):
    cfg = config.load_config()
    assert cfg["llm"]["model"] == "test-model"
    assert cfg["corpus"]["dir"] == "data"


def test_get_api_key_from_keyring(monkeypatch):
    monkeypatch.setattr(keyring, "get_password", lambda s, u: "TEST-VALUE")
    assert config.get_api_key() == "TEST-VALUE"


def test_get_api_key_env_fallback(monkeypatch):
    monkeypatch.setattr(keyring, "get_password", lambda s, u: None)
    monkeypatch.setenv("LEX_LLM_API_KEY", "ENV-VALUE")
    assert config.get_api_key() == "ENV-VALUE"


def test_get_api_key_keyring_error_falls_back(monkeypatch):
    def boom(s, u):
        raise RuntimeError("no backend")

    monkeypatch.setattr(keyring, "get_password", boom)
    monkeypatch.setenv("LEX_LLM_API_KEY", "ENV-VALUE")
    assert config.get_api_key() == "ENV-VALUE"


def test_set_api_key(monkeypatch):
    captured = {}
    monkeypatch.setattr(keyring, "set_password", lambda s, u, k: captured.update(service=s, user=u, key=k))
    config.set_api_key("NEW-VALUE")
    assert captured == {"service": config.SERVICE, "user": config.KEY_USER, "key": "NEW-VALUE"}