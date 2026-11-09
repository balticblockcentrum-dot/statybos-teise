import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

from . import config

VERSION = "0.1.0"


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
    if data.get("version") and data["version"] != VERSION:
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
    return staging / "extracted"