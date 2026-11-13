"""Inventariseert de bronafbeeldingen in tekeningen/ naar docs/bladen/index.json."""
import json
import os
import sys

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
TEK = os.path.join(ROOT, "tekeningen")
OUT = os.path.join(ROOT, "docs", "bladen", "index.json")
EXTS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".pdf")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    entries = []
    for name in sorted(os.listdir(TEK)):
        if not name.lower().endswith(EXTS):
            continue
        path = os.path.join(TEK, name)
        entry = {"bestand": name, "bytes": os.path.getsize(path), "bladtype": None,
                 "schaal": None, "maten": [], "opmerkingen": None}
        if name.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")):
            try:
                with Image.open(path) as im:
                    entry["breedte_px"], entry["hoogte_px"] = im.size
            except Exception as exc:
                entry["fout"] = str(exc)
        entries.append(entry)
    with open(OUT, "w") as fh:
        json.dump({"aantal": len(entries), "bladen": entries}, fh, ensure_ascii=False, indent=1)
    print("aantal tekeningen:", len(entries))
    for e in entries:
        print(" -", e["bestand"], e.get("breedte_px", ""), "x", e.get("hoogte_px", ""))
    print("index geschreven naar", os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
