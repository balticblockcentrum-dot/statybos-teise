import sys

import pytest

import cli


def test_analyze_unsupported_format_exits_1(monkeypatch, tmp_path, capsys):
    p = tmp_path / "doc.xyz"
    p.write_text("x", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["statybos-teise", "analyze", str(p)])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    assert "Klaida:" in capsys.readouterr().err


def test_analyze_missing_file_exits_1(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(sys, "argv", ["statybos-teise", "analyze", str(tmp_path / "nera.txt")])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    assert "Klaida:" in capsys.readouterr().err


def test_retrieve_prints_citations(monkeypatch, tmp_project, capsys):
    monkeypatch.setattr(sys, "argv", ["statybos-teise", "retrieve", "rangos sutartis", "-k", "3"])
    cli.main()
    assert "CK 6.644 str." in capsys.readouterr().out