from lex import corpus


def test_tokens_filters_short():
    toks = corpus._tokens("CK 6.644 rangos sutartis ir")
    assert "rangos" in toks
    assert "sutartis" in toks
    assert "644" in toks
    assert "ir" not in toks
    assert "6" not in toks


def test_bm25_ranks_relevant_first():
    docs = [
        "rangos sutartis rangovas užsakovas darbai kaina",
        "netesybos delspinigiai bauda termino praleidimas",
        "sutarčių laisvė teisės pareigos",
    ]
    engine = corpus.BM25(docs)
    hits = engine.search("rangos sutartis rangovas", top_k=3)
    assert hits[0][0] == 0
    assert all(score > 0 for _, score in hits)


def test_bm25_no_match_returns_empty():
    engine = corpus.BM25(["rangos sutartis", "netesybos"])
    assert engine.search("visiškai nerelevantu žodžiai", top_k=5) == []


def test_retrieve_returns_provision_dicts(tmp_project):
    res = corpus.retrieve("rangos sutartis rangovas", top_k=2)
    assert len(res) >= 1
    assert res[0]["citation"] == "CK 6.644 str."
    assert all(isinstance(p, dict) and "citation" in p for p in res)


def test_retrieve_respects_top_k(tmp_project):
    res = corpus.retrieve("sutartis netesybos rangos", top_k=1)
    assert len(res) == 1