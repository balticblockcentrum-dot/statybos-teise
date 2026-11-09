import json
import urllib.request

from . import config

SYSTEM = (
    "Esi Lietuvos statybos, sutarčių ir darbo teisės ekspertas. Atsakyk lietuvių kalba, "
    "tiksliai ir praktiškai, kaip patyręs advokatas. TAU PRIVALOMA remtis TIK pateiktomis "
    "teisės normomis (kontekste) ir cituoti jas tiksliai (įstatymas + straipsnis). "
    "Jei konteksto nepakanka, aiškiai tai pasakyk ir nurodyk, kad reikia patikrinti aktualią "
    "redakciją Teisės aktų registre (TAR) arba kreiptis į advokatą. Nekurk straipsnių numerių. "
    "Kiekvieno atsakymo gale pridėk pastabą, kad tai teisinė pagalba, o galutinius teismui "
    "skirtus dokumentus turi peržiūrėti licencijuotas advokatas."
)


def _build_context(provisions):
    lines = []
    for p in provisions:
        lines.append(f"[{p['citation']}] {p['title']}: {p['text']}")
    return "\n".join(lines)


def analyze(document_text, provisions, task="analyze"):
    cfg = config.load_config()["llm"]
    key = config.get_api_key()
    if not key:
        raise RuntimeError("Nėra API rakto. Paleiskite setup_key.py.")

    instruction = (
        "Išanalizuok žemiau pateiktą dokumentą ir parengk atsakymą. "
        if task == "analyze"
        else "Remdamasis dokumentu ir normomis, parengk siunčiamą dokumentą (pretenziją/atsakymą/ieškinio projektą). "
    )
    user = (
        f"{instruction}\n\n=== TAIKYTINOS NORMOS (kontekstas) ===\n{_build_context(provisions)}\n\n"
        f"=== DOKUMENTAS ===\n{document_text}\n\n"
        "Formatas: 1) Santrauka; 2) Taikytinos normos (su citatomis); 3) Analizė; "
        "4) Siunčiamo dokumento tekstas; 5) Rizikos ir žingsniai (įskaitant teismą); 6) Pastaba dėl advokato peržiūros."
    )
    payload = {
        "model": cfg["model"],
        "temperature": cfg.get("temperature", 0.2),
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
    }
    req = urllib.request.Request(
        cfg["base_url"].rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.load(resp)
    return body["choices"][0]["message"]["content"]