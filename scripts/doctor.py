#!/usr/bin/env python3
"""Read-only preflight for recon-pipeline; uses only the Python standard library.

No scans, network probes, or installers are run. DNS lookup is optional and
used solely to diagnose package/repository retrieval problems.
"""

import argparse
import importlib.metadata
import json
from pathlib import Path
import shutil
import socket
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
# Original, unsupported pins, kept only for identifying accidental legacy installs.
LEGACY_PINS = {
    "cmd2": "1.0.1",
    "luigi": "2.8.12",
    "SQLAlchemy": "1.3.15",
    "PyYAML": "5.4.0",
    "python-libnmap": "0.7.0",
}


# Supported ranges for the smoke-tested Python 3.13 dependency profile.
# Upper bounds are exclusive; all comparisons use numeric release components.
MODERN_RANGES = {
    "cmd2": ((2, 6, 2), (3, 0, 0)),
    "luigi": ((3, 8, 1), (4, 0, 0)),
    "SQLAlchemy": ((1, 4, 54), (2, 0, 0)),
    "PyYAML": ((6, 0, 2), (7, 0, 0)),
    "python-libnmap": ((0, 7, 0), (1, 0, 0)),
}


def release_parts(version):
    """Extract up to three numeric release components without dependencies."""
    import re
    match = re.match(r"^([0-9]+)(?:[.]([0-9]+))?(?:[.]([0-9]+))?", version)
    if not match:
        return None
    return tuple(int(part or "0") for part in match.groups())


def version_of(package):
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def diagnose(offline=False, root=REPO_ROOT, dns_lookup=socket.getaddrinfo):
    """Return diagnostic records without side effects or third-party imports."""
    records = []

    def add(name, status, detail):
        records.append({"name": name, "status": status, "detail": detail})

    version = ".".join(str(v) for v in sys.version_info[:3])
    if sys.version_info < (3, 9):
        add("python", "warning", f"Python {version}; current recovery tooling needs >=3.9")
    else:
        add("python", "ok", f"Python {version}")

    for path in ("Pipfile", "pipeline/recon-pipeline.py", "docs/INSTALL-RECOVERY.md"):
        add(path, "ok" if (root / path).is_file() else "error", "present" if (root / path).is_file() else "missing")

    if sys.prefix != sys.base_prefix:
        add("virtualenv", "ok", f"isolated interpreter at {sys.prefix}")
    else:
        add("virtualenv", "warning", "not currently in a virtual environment")

    add("pipenv", "ok" if shutil.which("pipenv") else "warning", shutil.which("pipenv") or "not on PATH (optional if using a dedicated installer environment)")
    for package, historical in LEGACY_PINS.items():
        installed = version_of(package)
        if installed is None:
            add(f"package:{package}", "warning", f"not installed; historical pin {historical}")
        else:
            parsed = release_parts(installed)
            minimum, maximum = MODERN_RANGES[package]
            status = "ok" if installed != historical and parsed is not None and minimum <= parsed < maximum else "warning"
            detail = f"installed {installed}; supported range >= {'.'.join(map(str, minimum))}, < {'.'.join(map(str, maximum))}"
            if installed == historical:
                detail += " (obsolete legacy pin)"
            add(f"package:{package}", status, detail)

    if sys.version_info[:2] == (3, 13):
        add("python-profile", "ok", "Python 3.13 modern dependency profile (native scanner compatibility unverified)")
    else:
        add("python-profile", "warning", "default dependency profile targets Python 3.13; see docs/INSTALL-MODERN.md")
    if not offline:
        for domain in ("github.com", "pypi.org"):
            try:
                dns_lookup(domain, 443, type=socket.SOCK_STREAM)
            except OSError as exc:
                add(f"dns:{domain}", "error", f"DNS resolution failed: {exc}")
            else:
                add(f"dns:{domain}", "ok", "DNS resolved (does not confirm HTTPS connectivity)")
    return records


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only installation preflight, no scanning")
    parser.add_argument("--offline", action="store_true", help="do not perform DNS lookups")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    rows = diagnose(offline=args.offline)
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            print(f"{row['status'].upper():7} {row['name']}: {row['detail']}")
    return 1 if any(row["status"] == "error" for row in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
