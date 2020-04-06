# Automated Reconnaissance Pipeline

![version](https://img.shields.io/github/v/release/epi052/recon-pipeline?style=for-the-badge)
![Python application](https://img.shields.io/github/workflow/status/epi052/recon-pipeline/recon-pipeline%20build?style=for-the-badge)
![code coverage](https://img.shields.io/badge/coverage-97%25-blue?style=for-the-badge)
![python](https://img.shields.io/badge/python-3.7-informational?style=for-the-badge)
![luigi](https://img.shields.io/github/pipenv/locked/dependency-version/epi052/recon-pipeline/luigi?style=for-the-badge)
![cmd2](https://img.shields.io/github/pipenv/locked/dependency-version/epi052/recon-pipeline/cmd2?style=for-the-badge)
![SQLAlchemy](https://img.shields.io/github/pipenv/locked/dependency-version/epi052/recon-pipeline/SQLAlchemy?style=for-the-badge)
![python-libnmap](https://img.shields.io/github/pipenv/locked/dependency-version/epi052/recon-pipeline/python-libnmap?style=for-the-badge)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)

There are an [accompanying set of blog posts](https://epi052.gitlab.io/notes-to-self/blog/2019-09-01-how-to-build-an-automated-recon-pipeline-with-python-and-luigi/) detailing the development process and underpinnings of the pipeline.  Feel free to check them out if you're so inclined, but they're in no way required reading to use the tool.

Check out [recon-pipeline's readthedocs entry](https://recon-pipeline.readthedocs.io/) for some more in depth information than what this README provides.

## Installation

> Automatic installation tested on kali 2019.4 and Ubuntu 18.04

There are two primary phases for installation:

1. prior to the python dependencies being installed
2. everything else

First, the manual steps to get dependencies installed in a virtual environment are as follows, starting with [pipenv](https://github.com/pypa/pipenv)

### Kali
```bash
apt install pipenv
```

### Ubuntu 18.04
```bash
sudo apt install python3-pip
pip install --user pipenv
echo "PATH=${PATH}:~/.local/bin" >> ~/.bashrc
bash
```

### Both OSs after pipenv install

```bash
git clone https://github.com/epi052/recon-pipeline.git
cd recon-pipeline
pipenv install
```

After installing the python dependencies, the `recon-pipeline` shell provides its own [install](https://recon-pipeline.readthedocs.io/en/latest/api/commands.html#install) command (seen below).  A simple `install all` will handle all additional installation steps.

> Ubuntu-18.04 Note (and newer kali versions):  You may consider running `sudo -v` prior to running `./recon-pipeline.py`.  `sudo -v` will refresh your creds, and the underlying subprocess calls during installation won't prompt you for your password.  It'll work either way though.

[![asciicast](https://asciinema.org/a/294414.svg)](https://asciinema.org/a/294414)

## Example Scan

Here are the steps the video below takes to scan tesla.com.

Create a targetfile
```bash
# use virtual environment
pipenv shell

# create targetfile; a targetfile is required for all scans
mkdir /root/bugcrowd/tesla
cd /root/bugcrowd/tesla
echo tesla.com > tesla-targetfile

# create a blacklist (if necessary based on target's scope)
echo energysupport.tesla.com > tesla-blacklist
echo feedback.tesla.com >> tesla-blacklist
echo employeefeedback.tesla.com >> tesla-blacklist
echo ir.tesla.com >> tesla-blacklist

# drop into the interactive shell
/root/PycharmProjects/recon-pipeline/pipeline/recon-pipeline.py
recon-pipeline>
```

Create a new database to store scan results
```bash
recon-pipeline> database attach
recon-pipeline> database attach
   1. create new database
Your choice? 1
new database name? (recommend something unique for this target)
-> tesla-scan
[*] created database @ /home/epi/.local/recon-pipeline/databases/tesla-scan
[+] attached to sqlite database @ /home/epi/.local/recon-pipeline/databases/tesla-scan
[db-1] recon-pipeline>
```

Scan the target
```bash
[db-1] recon-pipeline> scan FullScan --exempt-list tesla-blacklist --target-file tesla-targetfile --interface eno1 --top-ports 2000 --rate 1200
[-] FullScan queued
[-] TKOSubsScan queued
[-] GatherWebTargets queued
[-] ParseAmassOutput queued
[-] AmassScan queued
[-] ParseMasscanOutput queued
[-] MasscanScan queued
[-] WebanalyzeScan queued
[-] CORScannerScan queued
[-] SearchsploitScan queued
[-] ThreadedNmapScan queued
[-] SubjackScan queued
[-] AquatoneScan queued
[-] GobusterScan queued
[db-1] recon-pipeline>
```

The same steps can be seen in realtime in the linked video below.

[![asciicast](https://asciinema.org/a/293302.svg)](https://asciinema.org/a/293302)

### Target File and Exempt List File (defining scope)

The pipeline expects a file that describes the target's scope to be provided as an argument to the `--target-file` option.  The target file can consist of domains, ip addresses, and ip ranges, one per line.

```text
tesla.com
tesla.cn
teslamotors.com
...
```

Some bug bounty scopes have expressly verboten subdomains and/or top-level domains, for that there is the `--exempt-list` option.  The exempt list follows the same rules as the target file.

```text
shop.eu.teslamotors.com
energysupport.tesla.com
feedback.tesla.com
...
```

### Using a Scheduler

The backbone of this pipeline is spotify's [luigi](https://github.com/spotify/luigi) batch process management framework.  Luigi uses the concept of a scheduler in order to manage task execution.  Two types of scheduler are available, a local scheduler and a central scheduler.  The local scheduler is useful for development and debugging while the central scheduler provides the following two benefits:

- Make sure two instances of the same task are not running simultaneously
- Provide visualization of everything that’s going on

While in the `recon-pipeline` shell, running `install luigi-service` will copy the `luigid.service` file provided in the
repo to its appropriate systemd location and start/enable the service.  The result is that the central scheduler is up
and running easily.

The other option is to add `--local-scheduler` to your `scan` command from within the `recon-pipeline` shell.

## Viewing Results



## Special Thanks

- [@aringo](https://github.com/aringo) for his help on the precursor to this tool
- [@kernelsndrs](https://github.com/kernelsndrs) for identifying a few bugs after initial launch




