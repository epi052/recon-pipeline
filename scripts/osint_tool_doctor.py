#!/usr/bin/env python3
"""Read-only dependency check for opt-in passive OSINT packages; does not contact targets."""
import argparse
import importlib.metadata
import json

PACKAGES = ("requests", "dnspython", "beautifulsoup4", "ExifRead")

def check():
    result = []
    for package in PACKAGES:
        try:
            version = importlib.metadata.version(package)
            result.append({"package": package, "status": "ok", "version": version})
        except importlib.metadata.PackageNotFoundError:
            result.append({"package": package, "status": "missing"})
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = check()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for entry in result:
            print(entry["package"], entry["status"], entry.get("version", ""))
    return 1 if any(x["status"] != "ok" for x in result) else 0

if __name__ == "__main__":
    raise SystemExit(main())
