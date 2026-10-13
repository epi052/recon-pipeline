# Installation recovery and compatibility notes (October 2026)

This repository contains a **legacy Python reconnaissance framework**. Its original CI targeted Python 3.7, the lockfile pins older packages (including `cmd2==1.0.1`, `luigi==2.8.12`, and `pyyaml==5.4.0`), and the original instructions were tested on old Kali/Ubuntu releases. **Do not assume that it installs or runs on Python 3.13 or current Ubuntu/macOS/Termux.** Never run an unreviewed `tools install all` or an active scan as an installation test.

## 1. Separate network failure from package failure

The diagnostic `git ls-remote` should succeed before attempting a clone:

```bash
getent hosts github.com || true  # Linux: inspect DNS lookup
git ls-remote https://github.com/jamietatebenger-lab/recon-pipeline.git HEAD
```

If this prints `Could not resolve host: github.com`, cloning and package downloads cannot be fixed by editing `Pipfile`. Check that the device has internet, DNS and proxy configuration are correct, and no workplace firewall/VPN is blocking GitHub. Don't disable TLS verification or install from unofficial mirrors to bypass failures. On macOS or Termux, use the system's relevant DNS diagnostics if `getent` is unavailable.

## 2. Install Pipenv outside the system Python

`python3 -m pip install --user pipenv` may fail with `Can not perform a '--user' install. User site-packages are not visible in this virtualenv.` or an externally-managed-environment error. A dedicated, isolated environment is safer:

```bash
python3 -m venv "$HOME/.pipenv-venv"
"$HOME/.pipenv-venv/bin/python" -m pip install --upgrade pip
"$HOME/.pipenv-venv/bin/python" -m pip install pipenv
"$HOME/.pipenv-venv/bin/pipenv" --version
```

This *only installs Pipenv itself*; it does not make the legacy project packages compatible with modern Python. Requires working DNS and a Python installation with `venv` support. Never use `sudo pip`, `--break-system-packages`, or `--trusted-host` as a workaround.

## 3. Check interpreter compatibility before installing legacy requirements

```bash
python3 --version
command -v python3
git clone https://github.com/jamietatebenger-lab/recon-pipeline.git
cd recon-pipeline
cat Pipfile
```

The `Pipfile` specifies only `python_version = "3"`, which is **not** evidence of compatibility with every Python 3 release. If an isolated test environment has a compatible interpreter available, explicitly select it instead of silently using Python 3.13:

```bash
export PIPENV_IGNORE_VIRTUALENVS=1
export PIPENV_VENV_IN_PROJECT=1
"$HOME/.pipenv-venv/bin/pipenv" --python /path/to/compatible/python3
"$HOME/.pipenv-venv/bin/pipenv" install
"$HOME/.pipenv-venv/bin/pipenv" run python -c "import cmd2, luigi, yaml, sqlalchemy; print('Python imports OK')"
"$HOME/.pipenv-venv/bin/pipenv" run python pipeline/recon-pipeline.py
```

Replace `/path/to/compatible/python3` with an interpreter you actually have and have tested against these pins. No Python version newer than the historical CI target has been verified here. If `Pipfile.lock` cannot resolve/install for that interpreter, preserve the error log; dependency modernization requires targeted package upgrades and the existing test suite, not automatic unpinned upgrades. Use an isolated test machine/container for obsolete runtimes; do not expose outdated runtimes to untrusted networks.

## 4. Important platform caveats

- The upstream project originally targeted Kali Linux and Ubuntu, with native tools, executable discovery and system operations that can differ on newer Linux and Android **Termux**.
- The repository's existing `Dockerfile` starts from mutable `python:latest`. It is **not** a verified compatibility fix; do not rely on it as a stable legacy build without testing and pinning a maintained base image.
- Do not run `tools install all` to check whether the CLI works. Some installers and scanners require privileges or make network requests. In the CLI start with `help` or `tools list` only.
- Only scan systems you own or are expressly authorized to assess. Do not use this framework to obtain private accommodation reservations or guest information.

## 5. Report the *first* actual installation error

If you encounter a failure, capture its full output:

```bash
"$HOME/.pipenv-venv/bin/pipenv" --version
python3 --version
"$HOME/.pipenv-venv/bin/pipenv" install --verbose > pipenv-install.log 2>&1
tail -n 80 pipenv-install.log
```

Redact access tokens, paths containing personal identifiers and other secrets before sharing. Keep `pipenv-install.log` locally; do not commit it into a public repository.

**Status:** Guidance only. No successful modern-Python installation is claimed; the environment used for the October 2026 review had Python 3.13.5 and could not resolve github.com through DNS. This document does not modify scan functionality or dependency versions.
