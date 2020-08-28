# Automated Reconnaissance Pipeline

![version](https://img.shields.io/github/v/release/epi052/recon-pipeline?style=for-the-badge)
![Python application](https://img.shields.io/github/workflow/status/epi052/recon-pipeline/recon-pipeline%20build?style=for-the-badge)
![code coverage](https://img.shields.io/badge/coverage-97%25-blue?style=for-the-badge)
![python](https://img.shields.io/badge/python-3.7-informational?style=for-the-badge)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)

There are an [accompanying set of blog posts](https://epi052.gitlab.io/notes-to-self/blog/2019-09-01-how-to-build-an-automated-recon-pipeline-with-python-and-luigi/) detailing the development process and underpinnings of the pipeline.  Feel free to check them out if you're so inclined, but they're in no way required reading to use the tool.

Check out [recon-pipeline's readthedocs entry](https://recon-pipeline.readthedocs.io/) for some more in depth information than what this README provides.

Table of Contents
-----------------

- [Installation](#installation)
- [Defining Scope](#defining-a-scans-scope)
- [Example Scan](#example-scan)
    - [Existing Results Directories](#existing-results-directories)
- [Viewing Results](#viewing-results)
- [Chaining Results w/ Commands](#chaining-results-w-commands)
- [Choosing a Scheduler](#choosing-a-scheduler)
- [Found a Bug?](#found-a-bug)
- [Special Thanks](#special-thanks)

## Installation

> Automatic installation tested on kali 2019.4 and Ubuntu 18.04/20.04

There are two primary phases for installation:

1. prior to the python dependencies being installed
2. everything else

First, the manual steps to get dependencies installed in a virtual environment are as follows, starting with [pipenv](https://github.com/pypa/pipenv)

### Kali
```bash
sudo apt update
sudo apt install pipenv
```

### Ubuntu 18.04/20.04
```bash
sudo apt update
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
pipenv shell
```

### Docker

If you have Docker installed, you can run the recon-pipeline in a container with the following commands:

```bash
git clone https://github.com/epi052/recon-pipeline.git
cd recon-pipeline
docker build -t recon-pipeline .
docker run -d \
    -v ~/docker/recon-pipeline:/root/.local/recon-pipeline \
    -p 8082:8082 \
    --name recon-pipeline \
    recon-pipeline
docker start recon-pipeline
docker exec -it recon-pipeline pipeline
```

The `recon-pipeline` should start in the background automatically after the `docker run` command, however, you will have to start it after a reboot. For more information, please see the [Docker](https://recon-pipeline.readthedocs.io/en/latest/overview/installation.html#docker) docs.

[![asciicast](https://asciinema.org/a/318395.svg)](https://asciinema.org/a/318395)

After installing the python dependencies, the `recon-pipeline` shell provides its own [tools](https://recon-pipeline.readthedocs.io/en/latest/api/commands.html#tools) command (seen below).  A simple `tools install all` will handle all additional installation steps.

> Ubuntu Note (and newer kali versions):  You may consider running `sudo -v` prior to running `./recon-pipeline.py`.  `sudo -v` will refresh your creds, and the underlying subprocess calls during installation won't prompt you for your password.  It'll work either way though.

Individual tools may be installed by running `tools install TOOLNAME` where `TOOLNAME` is one of the known tools that make
up the pipeline.

The installer does not maintain state.  In order to determine whether a tool is installed or not, it checks the `path` variable defined in the tool's .yaml file.  The installer in no way attempts to be a package manager.  It knows how to execute the steps necessary to install and remove its tools.  Beyond that, it's
like Jon Snow, **it knows nothing**.

[![asciicast](https://asciinema.org/a/343745.svg)](https://asciinema.org/a/343745)

## Defining a Scan's Scope

**New as of v0.9.0**: In the event you're scanning a single ip address or host, simply use `--target`.  It accepts a single target and works in conjunction with `--exempt-list` if specified.

```text
scan HTBScan --target 10.10.10.183 --top-ports 1000
```

In order to scan more than one host at a time, the pipeline needs a file that describes the target's scope to be provided as an argument to the `--target-file` option.  The target file can consist of domains, ip addresses, and ip ranges, one per line.

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
[-] SearchsploitScan queued
[-] ThreadedNmapScan queued
[-] SubjackScan queued
[-] WaybackurlsScan queued
[-] AquatoneScan queued
[-] GobusterScan queued
[db-1] recon-pipeline>
```

The same steps can be seen in realtime in the linked video below.

[![asciicast](https://asciinema.org/a/318397.svg)](https://asciinema.org/a/318397)

### Existing Results Directories

When running additional scans against the same target, you have a few options.  You can either

- use a new directory
- reuse the same directory

If you use a new directory, the scan will start from the beginning.

If you choose to reuse the same directory, `recon-pipeline` will resume the scan from its last successful point.  For instance, say your last scan failed while running nmap.  This means that the pipeline executed all upstream tasks (amass and masscan) successfully.  When you use the same results directory for another scan, the amass and masscan scans will be skipped, because they've already run successfully.

**Note**: There is a gotcha that can occur when you scan a target but get no results.  For some scans, the pipeline may still mark the Task as complete (masscan does this).  In masscan's case, it's because it outputs a file to `results-dir/masscan-results/` whether it gets results or not.  Luigi interprets the file's presence to mean the scan is complete.

In order to reduce confusion, as of version 0.9.3, the pipeline will prompt you when reusing results directory.

```
[db-2] recon-pipeline> scan FullScan --results-dir testing-results --top-ports 1000 --rate 500 --target tesla.com
[*] Your results-dir (testing-results) already exists. Subfolders/files may tell the pipeline that the associated Task is complete. This means that your scan may start from a point you don't expect. Your options are as follows:
   1. Resume existing scan (use any existing scan data & only attempt to scan what isn't already done)
   2. Remove existing directory (scan starts from the beginning & all existing results are removed)
   3. Save existing directory (your existing folder is renamed and your scan proceeds)
Your choice?
```

## Viewing Results

As of version 0.9.0, scan results are stored in a database located (by default) at `~/.local/recon-pipeline/databases`.  Databases themselves are managed through the [database command](https://recon-pipeline.readthedocs.io/en/latest/api/commands.html#database) while viewing their contents is done via [view command](https://recon-pipeline.readthedocs.io/en/latest/api/commands.html#view-command).

The view command allows one to inspect different pieces of scan information via the following sub-commands

- endpoints (gobuster results)
- nmap-scans
- ports
- searchsploit-results
- targets
- web-technologies (webanalyze results)

Each of the sub-commands has a list of tab-completable options and values that can help drilling down to the data you care about.

All of the subcommands offer a `--paged` option for dealing with large amounts of output. `--paged` will show you one page of output at a time (using `less` under the hood).

A few examples of different view commands are shown below.

[![asciicast](https://asciinema.org/a/KtiV1ihl16DLyYpapyrmjIplk.svg)](https://asciinema.org/a/KtiV1ihl16DLyYpapyrmjIplk)

## Chaining Results w/ Commands

All of the results can be **piped out to other commands**. Let’s say you want to feed some results from recon-pipeline into another tool that isn’t part of the pipeline. Simply using a normal unix pipe `|` followed by the next command will get that done for you. Below is an example of piping targets into [gau](https://github.com/lc/gau)

```text
[db-2] recon-pipeline> view targets --paged
3.tesla.cn
3.tesla.com
api-internal.sn.tesla.services
api-toolbox.tesla.com
api.mp.tesla.services
api.sn.tesla.services
api.tesla.cn
api.toolbox.tb.tesla.services
...

[db-2] recon-pipeline> view targets | gau
https://3.tesla.com/pt_PT/model3/design
https://3.tesla.com/pt_PT/model3/design?redirect=no
https://3.tesla.com/robots.txt
https://3.tesla.com/sites/all/themes/custom/tesla_theme/assets/img/icons/favicon-160x160.png?2
https://3.tesla.com/sites/all/themes/custom/tesla_theme/assets/img/icons/favicon-16x16.png?2
https://3.tesla.com/sites/all/themes/custom/tesla_theme/assets/img/icons/favicon-196x196.png?2
https://3.tesla.com/sites/all/themes/custom/tesla_theme/assets/img/icons/favicon-32x32.png?2
https://3.tesla.com/sites/all/themes/custom/tesla_theme/assets/img/icons/favicon-96x96.png?2
https://3.tesla.com/sv_SE/model3/design
...
```

For more examples of view, please see the [documentation](https://recon-pipeline.readthedocs.io/en/latest/overview/viewing_results.html#).

## Choosing a Scheduler

The backbone of this pipeline is spotify's [luigi](https://github.com/spotify/luigi) batch process management framework.  Luigi uses the concept of a scheduler in order to manage task execution.  Two types of scheduler are available, a local scheduler and a central scheduler.  The local scheduler is useful for development and debugging while the central scheduler provides the following two benefits:

- Make sure two instances of the same task are not running simultaneously
- Provide visualization of everything that’s going on

While in the `recon-pipeline` shell, running `tools install luigi-service` will copy the `luigid.service` file provided in the
repo to its appropriate systemd location and start/enable the service.  The result is that the central scheduler is up
and running easily.

The other option is to add `--local-scheduler` to your `scan` command from within the `recon-pipeline` shell.

## Found a bug?

<!-- this section is a modified version of what's used by the awesome guys that wrote cmd2 -->

If you think you've found a bug, please first read through the open [Issues](https://github.com/epi052/recon-pipeline/issues). If you're confident it's a new bug, go ahead and create a new GitHub issue. Be sure to include as much information as possible so we can reproduce the bug.  At a minimum, please state the following:

* ``recon-pipeline`` version
* Python version
* OS name and version
* How to reproduce the bug
* Include any traceback or error message associated with the bug

## Special Thanks

- [@aringo](https://github.com/aringo) for his help on the precursor to this tool
- [@kernelsndrs](https://github.com/kernelsndrs) for identifying a few bugs after initial launch
- [@GreaterGoodest](https://github.com/GreaterGoodest) for identifying bugs and the project's first PR!
- The [cmd2](https://github.com/python-cmd2/cmd2) team for a lot of inspiration for project layout and documentation




