#!/usr/bin/env python3
"""Offline, privacy-minimised forensic file manifest. Standard library only."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

SAFE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".pdf", ".txt", ".eml"}
EMAIL_RE = re.compile(r"(?<![\w.+-])([\w.+-]+)@([\w.-]+\.[A-Za-z]{2,})")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?61[\s-]?)?0?[2478](?:[\s-]?\d){8}(?!\d)")
BOOKING_RE = re.compile(r"(?i)\b(?:reservation|confirmation|booking)\s*(?:id|number|no\.?|#)?\s*[:#-]?\s*([A-Z0-9-]{7,})\b")

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def redact(text):
    text = EMAIL_RE.sub(lambda m: m.group(1)[0] + "***@" + m.group(2), text)
    text = PHONE_RE.sub("[REDACTED PHONE]", text)
    return BOOKING_RE.sub(lambda m: m.group(0)[:m.start(1)-m.start(0)] + "[REDACTED ID]", text)

def build_manifest(paths, notes=None):
    items = []
    for name in paths:
        path = Path(name)
        if not path.is_file() or path.is_symlink():
            raise ValueError("Input must be an existing regular, non-symlink file")
        if path.suffix.lower() not in SAFE_SUFFIXES:
            raise ValueError("Unsupported file type")
        stat = path.stat()
        items.append({"file_label": "evidence-" + str(len(items) + 1).zfill(3),
                      "extension": path.suffix.lower(), "size_bytes": stat.st_size,
                      "sha256": digest(path)})
    return {"schema": "offline-evidence-v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "source": "local_files_no_upload",
            "items": items,
            "analyst_notes_redacted": redact(notes or ""),
            "limitations": "Hashing identifies file bytes, not authenticity, occupancy, or provenance."}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="Locally stored evidence files")
    parser.add_argument("--notes", default="", help="Optional analyst notes (redacted)")
    parser.add_argument("--output", required=True, help="Local JSON report; never place in public Git")
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.is_symlink():
        parser.error("Output must not be a symbolic link")
    try:
        report = build_manifest(args.files, args.notes)
        if any(output.resolve() == Path(f).resolve() for f in args.files):
            parser.error("Output cannot overwrite an evidence input")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
    except (ValueError, FileExistsError, OSError) as exc:
        parser.error(str(exc))
    print(f"Offline manifest created: {output}; {len(report['items'])} files")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
