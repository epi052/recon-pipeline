#!/usr/bin/env python
# stdlib imports
import os
import sys
import shlex
import pickle
import selectors
import threading
import subprocess
from pathlib import Path

__version__ = "0.7.3"

# fix up the PYTHONPATH so we can simply execute the shell from wherever in the filesystem
os.environ[
    "PYTHONPATH"
] = f"{os.environ.get('PYTHONPATH')}:{str(Path(__file__).parent.resolve())}"

# suppress "You should consider upgrading via the 'pip install --upgrade pip' command." warning
os.environ["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"

# third party imports
import cmd2  # noqa: E402
from cmd2.ansi import style  # noqa: E402

# project's module imports
from recon import get_scans, tools, scan_parser, install_parser  # noqa: F401,E402

# select loop, handles async stdout/stderr processing of subprocesses
selector = selectors.DefaultSelector()


class SelectorThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        """ Helper to set the SelectorThread's Event and cleanup the selector's fds """
        self._stop_event.set()

        # close any fds that were registered and still haven't been unregistered
        for key in selector.get_map():
            selector.get_key(key).fileobj.close()

    def stopped(self):
        """ Helper to determine whether the SelectorThread's Event is set or not. """
        return self._stop_event.is_set()

    def run(self):
        """ Run thread that executes a select loop; handles async stdout/stderr processing of subprocesses. """
        while not self.stopped():
            for k, mask in selector.select():
                callback = k.data
                callback(k.fileobj)


class ReconShell(cmd2.Cmd):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sentry = False
        self.prompt = "recon-pipeline> "
        self.selectorloop = None

        # register hooks to handle selector loop start and cleanup
        self.register_preloop_hook(self._preloop_hook)
        self.register_postloop_hook(self._postloop_hook)

    def _preloop_hook(self) -> None:
        """ Hook function that runs prior to the cmdloop function starting; starts the selector loop. """
        self.selectorloop = SelectorThread(daemon=True)
        self.selectorloop.start()

    def _postloop_hook(self) -> None:
        """ Hook function that runs after the cmdloop function stops; stops the selector loop. """
        if self.selectorloop.is_alive():
            self.selectorloop.stop()

        selector.close()

    def _install_error_reporter(self, stderr):
        """ Helper to print errors that crop up during any tool installation commands. """

        output = stderr.readline()

        if not output:
            return

        output = output.decode().strip()

        self.async_alert(style(f"[!] {output}", fg="bright_red"))

    def _luigi_pretty_printer(self, stderr):
        """ Helper to clean up the VERY verbose luigi log messages that are normally spewed to the terminal. """

        output = stderr.readline()

        if not output:
            return

        output = output.decode()

        if "===== Luigi Execution Summary =====" in output:
            # header that begins the summary of all luigi tasks that have executed/failed
            self.async_alert("")
            self.sentry = True

        # block below used for printing status messages
        if self.sentry:

            # only set once the Luigi Execution Summary is seen
            self.async_alert(style(output.strip(), fg="bright_blue"))
        elif output.startswith("INFO: Informed") and output.strip().endswith("PENDING"):
            # luigi Task has been queued for execution

            words = output.split()

            self.async_alert(
                style(f"[-] {words[5].split('_')[0]} queued", fg="bright_white")
            )
        elif output.startswith("INFO: ") and "running" in output:
            # luigi Task is currently running

            words = output.split()

            # output looks similar to , pid=3938074) running   MasscanScan(
            # want to grab the index of the luigi task running and use it to find the name of the scan (i.e. MassScan)
            scantypeidx = words.index("running") + 1
            scantype = words[scantypeidx].split("(", 1)[0]

            self.async_alert(style(f"[*] {scantype} running...", fg="bright_yellow"))
        elif output.startswith("INFO: Informed") and output.strip().endswith("DONE"):
            # luigi Task has completed

            words = output.split()

            self.async_alert(
                style(f"[+] {words[5].split('_')[0]} complete!", fg="bright_green")
            )

    @cmd2.with_argparser(scan_parser)
    def do_scan(self, args):
        """ Scan something.

        Possible scans include
            AmassScan           CORScannerScan      GobusterScan        SearchsploitScan
            ThreadedNmapScan    WebanalyzeScan      AquatoneScan        FullScan
            MasscanScan         SubjackScan         TKOSubsScan         HTBScan
        """
        self.async_alert(
            style(
                "If anything goes wrong, rerun your command with --verbose to enable debug statements.",
                fg="cyan",
                dim=True,
            )
        )

        # get_scans() returns mapping of {classname: [modulename, ...]} in the recon module
        # each classname corresponds to a potential recon-pipeline command, i.e. AmassScan, CORScannerScan ...
        scans = get_scans()

        # command is a list that will end up looking something like what's below
        # luigi --module recon.web.webanalyze WebanalyzeScan --target-file tesla --top-ports 1000 --interface eth0
        command = ["luigi", "--module", scans.get(args.scantype)[0]]

        command.extend(args.__statement__.arg_list)

        if args.verbose:
            # verbose is not a luigi option, need to remove it
            command.pop(command.index("--verbose"))

            subprocess.run(command)
        else:
            # suppress luigi messages in favor of less verbose/cleaner output
            proc = subprocess.Popen(
                command, stderr=subprocess.PIPE, stdout=subprocess.PIPE
            )

            # add stderr to the selector loop for processing when there's something to read from the fd
            selector.register(
                proc.stderr, selectors.EVENT_READ, self._luigi_pretty_printer
            )

    @cmd2.with_argparser(install_parser)
    def do_install(self, args):
        """ Install any/all of the libraries/tools necessary to make the recon-pipeline function. """

        # imported tools variable is in global scope, and we reassign over it later
        global tools

        # create .cache dir in the home directory, on the off chance it doesn't exist
        cachedir = Path.home() / ".cache/"
        cachedir.mkdir(parents=True, exist_ok=True)

        persistent_tool_dict = cachedir / ".tool-dict.pkl"

        if args.tool == "all":
            # show all tools have been queued for installation
            [
                self.async_alert(style(f"[-] {x} queued", fg="bright_white"))
                for x in tools.keys()
                if not tools.get(x).get("installed")
            ]

            for tool in tools.keys():
                self.do_install(tool)

            return

        if persistent_tool_dict.exists():
            tools = pickle.loads(persistent_tool_dict.read_bytes())

        if tools.get(args.tool).get("dependencies"):
            # get all of the requested tools dependencies

            for dependency in tools.get(args.tool).get("dependencies"):
                if tools.get(dependency).get("installed"):
                    # already installed, skip it
                    continue

                self.async_alert(
                    style(
                        f"[!] {args.tool} has an unmet dependency; installing {dependency}",
                        fg="yellow",
                        bold=True,
                    )
                )

                # install the dependency before continuing with installation
                self.do_install(dependency)

        if tools.get(args.tool).get("installed"):
            return self.async_alert(
                style(f"[!] {args.tool} is already installed.", fg="yellow")
            )
        else:

            # list of return values from commands run during each tool installation
            # used to determine whether the tool installed correctly or not
            retvals = list()

            self.async_alert(
                style(f"[*] Installing {args.tool}...", fg="bright_yellow")
            )

            for command in tools.get(args.tool).get("commands"):
                # run all commands required to install the tool

                # print each command being run
                self.async_alert(style(f"[=] {command}", fg="cyan"))

                if tools.get(args.tool).get("shell"):

                    # go tools use subshells (cmd1 && cmd2 && cmd3 ...) during install, so need shell=True
                    proc = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                else:

                    # "normal" command, split up the string as usual and run it
                    proc = subprocess.Popen(
                        shlex.split(command),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )

                out, err = proc.communicate()

                if err:
                    self.poutput(style(f"[!] {err.decode().strip()}", fg="bright_red"))

                retvals.append(proc.returncode)

        if all(x == 0 for x in retvals):
            # all return values in retvals are 0, i.e. all exec'd successfully; tool has been installed

            self.async_alert(style(f"[+] {args.tool} installed!", fg="bright_green"))

            tools[args.tool]["installed"] = True
        else:
            # unsuccessful tool install

            tools[args.tool]["installed"] = False

            self.async_alert(
                style(
                    f"[!!] one (or more) of {args.tool}'s commands failed and may have not installed properly; check output from the offending command above...",
                    fg="bright_red",
                    bold=True,
                )
            )

        # store any tool installs/failures (back) to disk
        pickle.dump(tools, persistent_tool_dict.open("wb"))


if __name__ == "__main__":
    rs = ReconShell(
        persistent_history_file="~/.reconshell_history", persistent_history_length=10000
    )
    sys.exit(rs.cmdloop())
