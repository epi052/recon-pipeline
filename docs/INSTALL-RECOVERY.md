# Installation recovery (October 2026)

This fork's **default `Pipfile` targets Python 3.13** and uses modern dependencies. In GitHub Actions, the current profile passed dependency installation, application import, interactive `ReconShell` initialisation and a Docker startup smoke test. The full external native scanner suite and Termux have **not** been certified. See [INSTALL-MODERN.md](INSTALL-MODERN.md) for the primary installation guide.

The historical dependencies (`cmd2==1.0.1`, `luigi==2.8.12`, `PyYAML==5.4.0`, etc.) are preserved in `Pipfile.legacy` and `Pipfile.legacy.lock`. These are not the default installation; do not select them as a remedy for current Python errors.

## 1. Diagnose network access

```bash
python3 scripts/doctor.py
git ls-remote https://github.com/jamietatebenger-lab/recon-pipeline.git HEAD
```

The diagnostic checks local Python, package state and DNS resolution for GitHub and PyPI; it does not make authenticated requests, scan hosts, or install software. If `Could not resolve host: github.com` appears, resolve device/network DNS and proxy configuration before retrying. GitHub clone/DNS connectivity depends on **the machine running the command**; passing GitHub Actions on a cloud runner does not repair the user's local network.

Never disable TLS verification or change to unauthorised mirrors to bypass network errors.

## 2. Fix virtual-environment / Pipenv errors

When `pip install --user pipenv` fails inside a virtual environment, create a separate environment for the Pipenv launcher:

```bash
python3 --version
python3 -m venv "$HOME/.pipenv-venv"
"$HOME/.pipenv-venv/bin/python" -m pip install --upgrade pip
"$HOME/.pipenv-venv/bin/python" -m pip install pipenv
git clone https://github.com/jamietatebenger-lab/recon-pipeline.git
cd recon-pipeline
export PIPENV_IGNORE_VIRTUALENVS=1
export PIPENV_VENV_IN_PROJECT=1
"$HOME/.pipenv-venv/bin/pipenv" install
"$HOME/.pipenv-venv/bin/pipenv" run python scripts/doctor.py --offline
"$HOME/.pipenv-venv/bin/pipenv" run python pipeline/recon-pipeline.py
```

The default `Pipfile` currently requires **Python 3.13**. Verify this interpreter is installed. The default `Pipfile.lock` was removed during the upgrade so Pipenv resolves a new lock for this profile. Preserve locally generated lockfiles for reproducibility if needed; do not use `Pipfile.legacy.lock` with the default `Pipfile`.

Do not use `sudo pip`, `--break-system-packages`, `--trusted-host`, or `tools install all` to troubleshoot startup.

## 3. Docker-specific notes

The Dockerfile now starts from `python:3.13-slim-bookworm`, uses `requirements-modern.txt`, and adds `PYTHONPATH=/opt/recon-pipeline`. Docker builds and startup imports have passed GitHub Actions. The container sets `RECON_PIPELINE_MASSCAN_IFACE=eth0`; outside Docker, the default remains `tun0` unless overridden. This is *not* evidence that Masscan or Nmap scans work or that any target is authorised.

## 4. Collect first error, not repeated scans

```bash
"$HOME/.pipenv-venv/bin/pipenv" install --verbose > pipenv-install.log 2>&1
tail -n 80 pipenv-install.log
```

Remove secrets and personal identifiers from logs before sharing; do not upload sensitive logs to a public repository. Native scan tools are for systems you own or are expressly authorised to assess.
