import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lex import config, ingest, corpus, llm, draft, tar_sync, update


def main():
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
        print("Atnaujinimas:", m or "nenurodytas manifest URL (config.json)")
        return

    text = ingest.extract_text(args.file)
    provisions = corpus.retrieve(text, 6)
    print(f"Rastos normos: {len(provisions)}")
    answer = llm.analyze(text, provisions, task=args.cmd)
    out = args.out or str(Path(args.file).with_name(Path(args.file).stem + "-atsakymas"))
    txt, docx = draft.save_answer(answer, out)
    print("\n" + answer)
    print(f"\nIšsaugota: {txt}\nIšsaugota: {docx}")


if __name__ == "__main__":
    main()