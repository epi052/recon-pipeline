import sys
import shlex
import pickle
import socket
import inspect
import pkgutil
import subprocess
from pathlib import Path
from collections import defaultdict

import cmd2
from cmd2.ansi import style

import recon


def get_scans():
    """ Iterates over the recon package and its modules to find all of the *Scan classes.

    * A contract exists here that says any scans need to end with the word scan in order to be found by this function.

    Returns:
        dict() containing mapping of {modulename: classname} for all potential recon-pipeline commands
    """
    scans = defaultdict(list)

    # recursively walk packages; import each module in each package
    for loader, module_name, is_pkg in pkgutil.walk_packages(recon.__path__, prefix="recon."):
        _module = loader.find_module(module_name).load_module(module_name)
        globals()[module_name] = _module

    # walk all modules, grabbing classes that we've written and add them to the classlist set
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.ismodule(obj) and not name.startswith("_"):
            for subname, subobj in inspect.getmembers(obj):
                if inspect.isclass(subobj) and subname.lower().endswith("scan"):
                    scans[subname].append(name)

    return scans


# tool definitions for the auto-installer
tools = {
    "go": {"installed": False, "dependencies": None, "commands": ["apt-get install -y -q golang"]},
    "luigi": {
        "installed": False,
        "dependencies": ["pipenv", "luigi-service"],
        "commands": ["pipenv install luigi"],
    },
    "luigi-service": {
        "installed": False,
        "dependencies": None,
        "commands": [
            f"cp {str(Path(__file__).parent / 'luigid.service')} /lib/systemd/system/luigid.service",
            "systemctl start luigid.service",
            "systemctl enable luigid.service",
        ],
    },
    "pipenv": {
        "installed": False,
        "dependencies": None,
        "commands": ["apt-get install -y -q pipenv"],
    },
    "masscan": {
        "installed": False,
        "dependencies": None,
        "commands": [
            "git clone https://github.com/robertdavidgraham/masscan /tmp/masscan",
            "make -s -j -C /tmp/masscan",
            "mv /tmp/bin/masscan /usr/bin/masscan",
            "rm -rf /tmp/masscan",
        ],
    },
    "amass": {"installed": False, "dependencies": None, "commands": "apt-get install -y -q amass"},
    "aquatone": {
        "installed": False,
        "dependencies": None,
        "commands": [
            "mkdir /tmp/aquatone",
            "wget -q https://github.com/michenriksen/aquatone/releases/download/v1.7.0/aquatone_linux_amd64_1.7.0.zip -O /tmp/aquatone/aquatone.zip",
            "unzip /tmp/aquatone/aquatone.zip -d /tmp/aquatone",
            "mv /tmp/aquatone/aquatone /usr/bin/aquatone",
            "rm -rf /tmp/aquatone",
        ],
    },
    "corscanner": {
        "installed": False,
        "dependencies": None,
        "commands": [
            "git clone https://github.com/chenjj/CORScanner.git /opt/CORScanner",
            "pip install -r /opt/CORScanner/requirements.txt",
            "pip install future",
        ],
    },
    "gobuster": {
        "installed": False,
        "dependencies": ["go"],
        "commands": [
            "go get github.com/OJ/gobuster",
            "(cd ~/go/src/github.com/OJ/gobuster && go build && go install)",
        ],
        "shell": True,
    },
    "tko-subs": {
        "installed": False,
        "dependencies": ["go"],
        "commands": [
            "go get github.com/anshumanbh/tko-subs",
            "(cd ~/go/src/github.com/anshumanbh/tko-subs && go build && go install)",
        ],
        "shell": True,
    },
    "subjack": {
        "installed": False,
        "dependencies": ["go"],
        "commands": [
            "go get github.com/haccer/subjack",
            "(cd ~/go/src/github.com/haccer/subjack && go build && go install)",
        ],
        "shell": True,
    },
    "webanalyze": {
        "installed": False,
        "dependencies": ["go"],
        "commands": [
            "go get github.com/rverton/webanalyze",
            "(cd ~/go/src/github.com/rverton/webanalyze && go build && go install)",
        ],
        "shell": True,
    },
    "recursive-gobuster": {
        "installed": False,
        "dependencies": None,
        "commands": [
            "git clone https://github.com/epi052/recursive-gobuster.git /opt/recursive-gobuster",
            "ln -s /opt/recursive-gobuster/recursive-gobuster.pyz /usr/local/bin",
        ],
    },
}

# options for ReconShell's 'scan' command
scan_parser = cmd2.Cmd2ArgumentParser()
scan_parser.add_argument("scantype", choices_function=get_scans)
scan_parser.add_argument(
    "--target-file",
    completer_method=cmd2.Cmd.path_complete,
    help="file created by the user that defines the target's scope; list of ips/domains",
)
scan_parser.add_argument(
    "--exempt-list", completer_method=cmd2.Cmd.path_complete, help="list of blacklisted ips/domains"
)
scan_parser.add_argument(
    "--wordlist", completer_method=cmd2.Cmd.path_complete, help="path to wordlist used by gobuster"
)
scan_parser.add_argument(
    "--interface",
    choices_function=lambda: [x[1] for x in socket.if_nameindex()],
    help="which interface masscan should use",
)
scan_parser.add_argument(
    "--recursive", action="store_true", help="whether or not to recursively gobust"
)
scan_parser.add_argument("--rate", help="rate at which masscan should scan")
scan_parser.add_argument(
    "--top-ports",
    help="ports to scan as specified by nmap's list of top-ports (only meaningful to around 5000)",
)
scan_parser.add_argument(
    "--ports", help="port specification for masscan (all ports example: 1-65535,U:1-65535)"
)
scan_parser.add_argument(
    "--threads", help="number of threads for all of the threaded applications to use"
)
scan_parser.add_argument("--scan-timeout", help="scan timeout for aquatone")
scan_parser.add_argument("--proxy", help="proxy for gobuster if desired (ex. 127.0.0.1:8080)")
scan_parser.add_argument("--extensions", help="list of extensions for gobuster (ex. asp,html,aspx)")
scan_parser.add_argument(
    "--local-scheduler",
    action="store_true",
    help="use the local scheduler instead of the central scheduler (luigid)",
)
scan_parser.add_argument(
    "--verbose",
    action="store_true",
    help="shows debug messages from luigi, useful for troubleshooting",
)

# options for ReconShell's 'install' command
install_parser = cmd2.Cmd2ArgumentParser()
install_parser.add_argument(
    "tool", help="which tool to install", choices=list(tools.keys()) + ["all"]
)


class ReconShell(cmd2.Cmd):
    prompt = "recon-pipeline> "

    @cmd2.with_argparser(scan_parser)
    def do_scan(self, args):
        """ Scan something. 
        
        Possible scans include 
            AmassScan           CORScannerScan      GobusterScan        SearchsploitScan
            ThreadedNmapScan    WebanalyzeScan      AquatoneScan        FullScan
            MasscanScan         SubjackScan         TKOSubsScan
        """
        scans = get_scans()
        command = ["luigi", "--module", scans.get(args.scantype)[0]]

        command.extend(args.__statement__.arg_list)

        sentry = False
        if args.verbose:
            command.pop(
                command.index("--verbose")
            )  # verbose is not a luigi option, need to remove it
            subprocess.run(command)
        else:
            # suppress luigi messages in favor of less verbose/cleaner output
            proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

            while True:
                output = proc.stderr.readline()
                if not output and proc.poll() is not None:
                    break
                if not output:
                    continue

                output = output.decode()
                if "===== Luigi Execution Summary =====" in output:
                    self.poutput()
                    sentry = True

                # block below used for printing status messages
                if sentry:
                    self.poutput(style(output.strip(), fg="bright_blue"))
                elif output.startswith("INFO") and output.split()[-1] == "PENDING":
                    words = output.split()
                    self.poutput(style(f"[-] {words[5].split('_')[0]} queued", fg="bright_white"))
                elif output.startswith("INFO") and "running" in output:
                    words = output.split()
                    # output looks similar to , pid=3938074) running   MasscanScan(
                    # want to grab the index of the luigi task running
                    scantypeidx = words.index("running") + 1
                    scantype = words[scantypeidx].split("(", 1)[0]
                    self.poutput(style(f"[*] {scantype} running...", fg="bright_yellow"))
                elif output.startswith("INFO") and output.split()[-1] == "DONE":
                    words = output.split()
                    self.poutput(
                        style(f"[+] {words[5].split('_')[0]} complete!", fg="bright_green")
                    )
        self.async_alert(
            style(
                "If anything went wrong, rerun your command with --verbose to enable debug statements.",
                fg="cyan",
                dim=True,
            )
        )

    @cmd2.with_argparser(install_parser)
    def do_install(self, args):
        """ Install any/all of the libraries/tools necessary to make the recon-pipeline function. """
        global tools

        cachedir = Path.home() / ".cache/"

        cachedir.mkdir(parents=True, exist_ok=True)

        persistent_tool_dict = cachedir / ".tool-dict.pkl"

        if args.tool == "all":
            for tool in tools.keys():
                self.do_install(tool)
            return

        if persistent_tool_dict.exists():
            tools = pickle.loads(persistent_tool_dict.read_bytes())

        if tools.get(args.tool).get("dependencies"):
            for dependency in tools.get(args.tool).get("dependencies"):
                if tools.get(dependency).get("installed"):
                    continue

                self.poutput(
                    style(
                        f"{args.tool} has an unmet dependency; installing {dependency}",
                        fg="blue",
                        bold=True,
                    )
                )
                self.do_install(dependency)

        if tools.get(args.tool).get("installed"):
            return self.poutput(style(f"{args.tool} is already installed.", fg="yellow"))
        else:
            self.poutput(style(f"Installing {args.tool}...", fg="blue", bold=True))

            for command in tools.get(args.tool).get("commands"):
                if tools.get(args.tool).get("shell") and command.startswith(
                    "("
                ):  # go installs use subshells (...)
                    subprocess.run(command, shell=True)
                else:
                    subprocess.run(shlex.split(command))
            tools[args.tool]["installed"] = True

        self.poutput(style(f"{args.tool} installed!", fg="green", bold=True))
        pickle.dump(tools, persistent_tool_dict.open("wb"))


if __name__ == "__main__":
    rs = ReconShell(persistent_history_file="~/.reconshell_history")
    sys.exit(rs.cmdloop())
