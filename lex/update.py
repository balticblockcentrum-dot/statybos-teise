import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

from . import config

VERSION = "0.3.3"


def _ver_tuple(v):
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0,)


def _get_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "statybos-teise"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def check_update():
    url = config.load_config()["update"].get("app_manifest_url")
    if not url:
        return None
    data = _get_json(url)
    if "assets" in data:  # GitHub Releases/latest
        manifest_asset = next((a for a in data["assets"] if a["name"] == "manifest.json"), None)
        if not manifest_asset:
            return None
        data = _get_json(manifest_asset["browser_download_url"])
    if data.get("version") and _ver_tuple(data["version"]) > _ver_tuple(VERSION):
        return data
    return None


def apply_update(manifest, staging=None):
    staging = Path(staging or config.ROOT.parent / "statybos-teise-update")
    req = urllib.request.Request(manifest["url"], headers={"User-Agent": "statybos-teise"})
    data = urllib.request.urlopen(req, timeout=120).read()
    if manifest.get("sha256") and hashlib.sha256(data).hexdigest() != manifest["sha256"]:
        raise RuntimeError("Atnaujinimo checksum nesutampa — atmetama.")
    staging.mkdir(parents=True, exist_ok=True)
    zip_path = staging / "update.zip"
    zip_path.write_bytes(data)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(staging / "extracted")
    extracted = staging / "extracted"
    _install(extracted)
    return extracted


def _install(extracted):
    # config.json ir data/ yra vartotojo duomenys — jų neperrašome
    preserved = {"config.json", "data"}
    root = config.ROOT
    for src in extracted.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(extracted)
        if rel.parts[0] in preserved:
            continue
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())