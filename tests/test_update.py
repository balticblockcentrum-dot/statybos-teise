import hashlib
import io
import json
import zipfile

import pytest

from lex import update


def test_ver_tuple_ordering():
    assert update._ver_tuple("1.2.3") == (1, 2, 3)
    assert update._ver_tuple("0.10.0") > update._ver_tuple("0.9.9")
    assert update._ver_tuple("bad") == (0,)


def test_check_update_newer(monkeypatch, tmp_project):
    monkeypatch.setattr(update, "_get_json", lambda url: {"version": "99.0.0", "url": "u", "sha256": "x"})
    m = update.check_update()
    assert m and m["version"] == "99.0.0"


def test_check_update_same_returns_none(monkeypatch, tmp_project):
    monkeypatch.setattr(update, "_get_json", lambda url: {"version": update.VERSION})
    assert update.check_update() is None


def test_check_update_older_returns_none(monkeypatch, tmp_project):
    monkeypatch.setattr(update, "_get_json", lambda url: {"version": "0.0.1"})
    assert update.check_update() is None


def test_check_update_no_url(monkeypatch, tmp_project):
    cfg = json.loads((tmp_project / "config.json").read_text(encoding="utf-8"))
    cfg["update"]["app_manifest_url"] = ""
    (tmp_project / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    assert update.check_update() is None


def _zip_bytes(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buf.getvalue()


def test_apply_update_installs_and_preserves_user_data(monkeypatch, tmp_project):
    files = {
        "cli.py": "print('new')",
        "lex/update.py": "VERSION='99.0.0'",
        "config.json": "SHOULD_NOT_COPY",
        "data/corpus.json": "SHOULD_NOT_COPY",
    }
    data = _zip_bytes(files)
    manifest = {"version": "99.0.0", "url": "https://example.test/u.zip", "sha256": hashlib.sha256(data).hexdigest()}
    monkeypatch.setattr(update.urllib.request, "urlopen", lambda req, timeout=None: io.BytesIO(data))
    update.apply_update(manifest, staging=tmp_project / "staging")
    assert (tmp_project / "cli.py").read_text(encoding="utf-8") == "print('new')"
    assert "SHOULD_NOT_COPY" not in (tmp_project / "config.json").read_text(encoding="utf-8")
    assert "SHOULD_NOT_COPY" not in (tmp_project / "data" / "corpus.json").read_text(encoding="utf-8")


def test_apply_update_rejects_bad_checksum(monkeypatch, tmp_project):
    data = _zip_bytes({"cli.py": "x"})
    manifest = {"version": "99.0.0", "url": "https://example.test/u.zip", "sha256": "wrong"}
    monkeypatch.setattr(update.urllib.request, "urlopen", lambda req, timeout=None: io.BytesIO(data))
    with pytest.raises(RuntimeError, match="checksum"):
        update.apply_update(manifest, staging=tmp_project / "staging")