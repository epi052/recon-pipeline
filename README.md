# Automated Reconnaissance Pipeline

![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

There are an [accompanying set of blog posts](https://epi052.gitlab.io/notes-to-self/blog/2019-09-01-how-to-build-an-automated-recon-pipeline-with-python-and-luigi/) detailing the development process and underpinnings of the pipeline.  Feel free to check them out if you're so inclined, but they're in no way required reading to use the tool.

## Installation

> Automatic installation only tested on kali 2019.4

There are two primary phases for installation: 

1. prior to [cmd2](https://github.com/python-cmd2/cmd2) being installed
2. everything else

First, the manual steps to get cmd2 installed in a virtual environment are as follows (and shown below)

```bash
apt install pipenv
git clone https://github.com/epi052/recon-pipeline.git
cd recon-pipeline
pipenv install cmd2
```

[![asciicast](https://asciinema.org/a/AxFd1SaLVx7mQdxqQBLfh6aqj.svg)](https://asciinema.org/a/AxFd1SaLVx7mQdxqQBLfh6aqj)

Once manual installation of [cmd2](https://github.com/python-cmd2/cmd2) is complete, the `recon-pipeline` shell provides its own `install` command (seen below).  A simple `install all` will handle all installation steps (as long as you're running a newer version of kali; all other OS's are untested, good luck!)

[![asciicast](https://asciinema.org/a/294414.svg)](https://asciinema.org/a/294414)

## Command Execution

Command execution is handled through the `recon-pipeline` shell (seen below).    

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




