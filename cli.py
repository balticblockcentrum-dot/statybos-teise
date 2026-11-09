import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lex import config, corpus, draft, ingest, llm, tar_sync, update


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="statybos-teise", description="Lietuvos statybos teisės asistentas")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("analyze", help="Analizuoti dokumentą (PDF/DOCX/TXT)")
    p.add_argument("file")
    p.add_argument("-o", "--out", default=None)

    p = sub.add_parser("draft", help="Parengti siunčiamą dokumentą")
    p.add_argument("file")
    p.add_argument("-o", "--out", default=None)

    p = sub.add_parser("retrieve", help="Paieška teisės bazėje (be LLM, nemokama)")
    p.add_argument("query")
    p.add_argument("-k", type=int, default=5)

    sub.add_parser("setup", help="Įvesti LLM API raktą (saugiai)")
    p = sub.add_parser("sync", help="Atnaujinti teisės bazę iš TAR eksporto")
    p.add_argument("export")
    sub.add_parser("check-update", help="Patikrinti programos atnaujinimą")
    sub.add_parser("update", help="Atsiųsti ir įdiegti naujausią versiją (auto-update)")

    args = ap.parse_args()

    if args.cmd == "setup":
        import setup_key  # noqa: F401
        return
    if args.cmd == "retrieve":
        for prov in corpus.retrieve(args.query, args.k):
            print(f"- {prov['citation']} | {prov['title']}")
        return
    if args.cmd == "sync":
        added, total = tar_sync.sync_from_export(args.export)
        print(f"Pridėta: {added}, iš viso normų: {total}")
        return
    if args.cmd == "check-update":
        m = update.check_update()
        if m:
            print(f"Nauja versija: {m['version']} (dabartinė {update.VERSION})")
        else:
            print(f"Versija {update.VERSION} — naujinimų nėra (manifest: GitHub).")
        return
    if args.cmd == "update":
        m = update.check_update()
        if not m:
            print(f"Versija {update.VERSION} — naujinimų nėra.")
            return
        print(f"Nauja versija {m['version']} — atsiunčiama, tikrinama SHA256...")
        update.apply_update(m)
        print(f"Įdiegta į: {config.ROOT}")
        print("Nauja versija galios kitą kartą paleidus programą.")
        return

    text = ingest.extract_text(args.file)
    provisions = corpus.retrieve(text, 6)
    print(f"Rastos normos: {len(provisions)}")
    answer = llm.analyze(text, provisions, task=args.cmd)
    out = args.out or str(Path(args.file).with_name(Path(args.file).stem + "-atsakymas"))
    txt, docx, pdf = draft.save_answer(answer, out)
    print("\n" + answer)
    print(f"\nIšsaugota: {txt}\nIšsaugota: {docx}\nIšsaugota: {pdf}")


if __name__ == "__main__":
    main()