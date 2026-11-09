import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lex import config

print("Iklijuokite LLM API rakta ir spauskite Enter.")
print("Raktas bus issaugotas Windows Credential Manager (keyring), ne faile ir ne pokalbyje.")
raw = input("API raktas: ").strip()
if len(raw) < 8:
    print("NEIRASYTA: raktas per trumpas arba tuscias.")
    sys.exit(1)
config.set_api_key(raw)
ok = bool(config.get_api_key())
print("Irasyta i keyring:", ok)
if ok:
    print("Sekme. Dabar programa gali naudoti LLM API.")