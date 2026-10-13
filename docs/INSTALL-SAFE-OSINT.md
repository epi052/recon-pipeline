# Opt-in passive OSINT and forensic dependencies

This profile adds `requests` (HTTP client), `dnspython` (DNS parsing and queries), `beautifulsoup4` (HTML parsing), and `ExifRead` (local image metadata parsing). These libraries do not execute scans simply by being installed; any code that uses them should be scoped to owned or expressly authorised targets. No credentials, case files, images, or private booking details should be committed.

## Desktop / GitHub Codespaces / Linux

```sh
python3 -m venv .venv-osint
. .venv-osint/bin/activate
python -m pip install -r requirements-osint-safe.txt
python -m pip check
python scripts/osint_tool_doctor.py --json
python -m unittest discover -s tests -p test_osint_tool_doctor.py -v
```

## Android Termux

```sh
pkg update && pkg upgrade
pkg install python git
cd "$HOME/recon-pipeline"
git fetch origin feature/safe-osint-dependencies-20261014
git switch feature/safe-osint-dependencies-20261014
python -m venv .venv-osint
. .venv-osint/bin/activate
python -m pip install -r requirements-osint-safe.txt
python -m pip check
python scripts/osint_tool_doctor.py --json
```

Termux support is provisional until tested on-device. Use a separate environment: the legacy application targets Python 3.13 and may not work on Termux. GitHub Actions installs packages on ephemeral Ubuntu runners, not your phone or production servers. This configuration installs libraries, not system tools such as Nmap, and it does not perform live target scans.

Versions are bounded for compatibility, **not pinned or supply-chain attested**. For a reproducible production build, generate and review a hash-locked requirements file after confirming compatibility.
