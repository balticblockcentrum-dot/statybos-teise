import json
import time
import urllib.error
import urllib.request

from . import config

SYSTEM = (
    "Esi Lietuvos statybos, sutarčių ir darbo teisės ekspertas ir atstovauji "
    "UAB „Baltic block centrum Šilalė“ interesams. Atsakyk lietuvių kalba, tiksliai ir praktiškai, "
    "kaip patyręs advokatas, VISADA siekdamas apginti įmonės interesus: teik įmonei palankiausius "
    "teisėtus argumentus, vertink rizikas ir galimybes įmonės naudai, siūlyk konkrečius žingsnius "
    "jos teisėms apginti. TAU PRIVALOMA remtis TIK pateiktomis teisės normomis (kontekste) ir "
    "cituoti jas tiksliai (įstatymas + straipsnis). Jei konteksto nepakanka, aiškiai tai pasakyk "
    "ir nurodyk, kad reikia patikrinti aktualią redakciją Teisės aktų registre (TAR) arba kreiptis "
    "į advokatą. Nekurk straipsnių numerių. Kiekvieno atsakymo gale pridėk pastabą, kad tai teisinė "
    "pagalba, o galutinius teismui skirtus dokumentus turi peržiūrėti licencijuotas advokatas."
)


def _build_context(provisions):
    lines = []
    for p in provisions:
        lines.append(f"[{p['citation']}] {p['title']}: {p['text']}")
    return "\n".join(lines)


def _model_order(cfg):
    seen = set()
    order = []
    for m in [cfg["model"], *cfg.get("fallback_models", [])]:
        if m and m not in seen:
            seen.add(m)
            order.append(m)
    return order


def _chat(cfg, key, model, messages):
    payload = {
        "model": model,
        "temperature": cfg.get("temperature", 0.2),
        "messages": messages,
    }
    req = urllib.request.Request(
        cfg["base_url"].rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.load(resp)
    return body["choices"][0]["message"]["content"]


def analyze(document_text, provisions, task="analyze"):
    cfg = config.load_config()["llm"]
    key = config.get_api_key()
    if not key:
        raise RuntimeError("Nėra API rakto. Paleiskite setup_key.py.")

    instruction = (
        "Išanalizuok žemiau pateiktą dokumentą ir parengk atsakymą, gindamas UAB „Baltic block centrum Šilalė“ interesus. "
        if task == "analyze"
        else "Remdamasis dokumentu ir normomis, parengk siunčiamą dokumentą (pretenziją/atsakymą/ieškinio projektą), gindamas UAB „Baltic block centrum Šilalė“ interesus. "
    )
    user = (
        f"{instruction}\n\n=== TAIKYTINOS NORMOS (kontekstas) ===\n{_build_context(provisions)}\n\n"
        f"=== DOKUMENTAS ===\n{document_text}\n\n"
        "Formatas: 1) Santrauka; 2) Taikytinos normos (su citatomis); 3) Analizė; "
        "4) Siunčiamo dokumento tekstas; 5) Rizikos ir žingsniai (įskaitant teismą); 6) Pastaba dėl advokato peržiūros."
    )
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]
    last_err = None
    for model in _model_order(cfg):
        for attempt in range(2):
            try:
                return _chat(cfg, key, model, messages)
            except urllib.error.HTTPError as e:
                last_err = e
                # laikinos perkrovos/kvotos klaidos — vienas pakartojimas, tada kitas modelis
                if e.code in (429, 500, 502, 503, 504) and attempt == 0:
                    time.sleep(2)
                    continue
                break
            except (urllib.error.URLError, TimeoutError, KeyError, IndexError) as e:
                # lėta arba netikėta atsakymo klaida — iškart bandom kitą modelį
                last_err = e
                break
    if last_err is not None:
        raise last_err
    raise RuntimeError("LLM neatsakė nė vienas modelis.")