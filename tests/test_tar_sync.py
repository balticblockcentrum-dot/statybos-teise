import json
from datetime import date

from lex import tar_sync


def test_sync_list_adds_and_merges(tmp_project):
    incoming = [
        {"id": "ck-6-644", "citation": "CK 6.644 str.", "text": "ATNAUJINTAS tekstas"},
        {"id": "nauja-1", "citation": "NAUJA 1 str.", "text": "Nauja norma"},
        {"citation": "be id"},
    ]
    export = tmp_project / "export.json"
    export.write_text(json.dumps(incoming, ensure_ascii=False), encoding="utf-8")
    added, total = tar_sync.sync_from_export(export)
    assert added == 1
    data = json.loads((tmp_project / "data" / "corpus.json").read_text(encoding="utf-8"))
    assert total == len(data["provisions"]) == 4
    by_id = {p["id"]: p for p in data["provisions"]}
    assert by_id["ck-6-644"]["text"] == "ATNAUJINTAS tekstas"
    assert "nauja-1" in by_id
    assert data["meta"]["updated"] == date.today().isoformat()


def test_sync_dict_form(tmp_project):
    export = tmp_project / "export.json"
    export.write_text(json.dumps({"provisions": [{"id": "x-1", "text": "X"}]}), encoding="utf-8")
    added, _ = tar_sync.sync_from_export(export)
    assert added == 1


def test_check_online_success(monkeypatch):
    class R:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(tar_sync.urllib.request, "urlopen", lambda *a, **k: R())
    assert tar_sync.check_online() is True


def test_check_online_failure(monkeypatch):
    def boom(*a, **k):
        raise OSError("offline")

    monkeypatch.setattr(tar_sync.urllib.request, "urlopen", boom)
    assert tar_sync.check_online() is False


def test_refresh_meta_offline(monkeypatch, tmp_project):
    monkeypatch.setattr(tar_sync, "check_online", lambda: False)
    assert tar_sync.refresh_meta() is False