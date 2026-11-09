import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = "balticblockcentrum-dot/statybos-teise"


def build(version):
    files = ["cli.py", "gui.py", "setup_key.py", "config.json", "data/corpus.json", "build_release.py"]
    files += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "lex").glob("*.py"))]
    zip_name = f"statybos-teise-v{version}.zip"
    zip_path = ROOT / zip_name
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(ROOT / f, f)
    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    manifest = {
        "version": version,
        "url": f"https://raw.githubusercontent.com/{REPO}/main/{zip_name}",
        "sha256": sha,
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Zip: {zip_name} ({zip_path.stat().st_size} bytes)")
    print(f"SHA256: {sha}")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "0.2.0")