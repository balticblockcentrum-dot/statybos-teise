import json
import math
import re
from collections import Counter

from . import config

_TOKEN = re.compile(r"[a-zA-ZąčęėįšųūžĄČĘĖĮŠŲŪŽ0-9]+", re.UNICODE)


def _tokens(text):
    return [t for t in _TOKEN.findall(text.lower()) if len(t) > 2]


def load_corpus():
    path = config.ROOT / config.load_config()["corpus"]["dir"] / "corpus.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _doc_text(p):
    return " ".join(filter(None, [p.get("law"), p.get("title"), p.get("text")]))


class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = docs
        self.k1 = k1
        self.b = b
        self.toks = [_tokens(d) for d in docs]
        self.n = len(docs)
        self.avgdl = sum(len(t) for t in self.toks) / max(1, self.n)
        self.tf = [Counter(t) for t in self.toks]
        df = Counter()
        for t in self.toks:
            df.update(set(t))
        self.idf = {w: math.log(1 + (self.n - c + 0.5) / (c + 0.5)) for w, c in df.items()}

    def search(self, query, top_k=5):
        q = _tokens(query)
        scores = []
        for i, tf in enumerate(self.tf):
            dl = len(self.toks[i])
            s = 0.0
            for w in q:
                if w not in tf:
                    continue
                idf = self.idf.get(w, 0.0)
                f = tf[w]
                s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            scores.append((s, i))
        scores.sort(reverse=True)
        return [(i, s) for s, i in scores[:top_k] if s > 0]


def retrieve(query, top_k=5):
    data = load_corpus()
    provisions = data["provisions"]
    engine = BM25([_doc_text(p) for p in provisions])
    hits = engine.search(query, top_k)
    return [provisions[i] for i, _ in hits]