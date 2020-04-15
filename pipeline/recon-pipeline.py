#!/usr/bin/env python
# stdlib imports
import os
import sys
import shlex
import shutil
import pickle
import selectors
import tempfile
import threading
import subprocess
import webbrowser
from pathlib import Path

DEFAULT_PROMPT = "recon-pipeline> "

# fix up the PYTHONPATH so we can simply execute the shell from wherever in the filesystem
os.environ["PYTHONPATH"] = f"{os.environ.get('PYTHONPATH')}:{str(Path(__file__).expanduser().resolve().parents[1])}"

# suppress "You should consider upgrading via the 'pip install --upgrade pip' command." warning
os.environ["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"

# in case we need pipenv, add its default --user installed directory to the PATH
sys.path.append(str(Path.home() / ".local" / "bin"))

# third party imports
import cmd2  # noqa: E402
from cmd2.ansi import style  # noqa: E402


def cluge_package_imports(name, package):
    """ project's module imports; need to cluge the package to handle relative imports at this level

        putting into a function for testability
    """
    if name == "__main__" and package is None:
        file = Path(__file__).expanduser().resolve()
        parent, top = file.parent, file.parents[1]

        sys.path.append(str(top))
        try:
            sys.path.remove(str(parent))
        except ValueError:  # already gone
            pass

        import pipeline  # noqa: F401

        sys.modules[name].__package__ = "pipeline"


cluge_package_imports(name=__name__, package=__package__)

from .recon.config import defaults  # noqa: F401,E402
from .models.nse_model import NSEResult  # noqa: F401,E402
from .models.db_manager import DBManager  # noqa: F401,E402
from .models.nmap_model import NmapResult  # noqa: F401,E402
from .models.technology_model import Technology  # noqa: F401,E402
from .models.searchsploit_model import SearchsploitResult  # noqa: F401,E402

from .recon import (  # noqa: F401,E402
    get_scans,
    tools,
    scan_parser,
    install_parser,
    status_parser,
    database_parser,
    db_detach_parser,
    db_list_parser,
    db_attach_parser,
    db_delete_parser,
    view_parser,
    target_results_parser,
    endpoint_results_parser,
    nmap_results_parser,
    technology_results_parser,
    searchsploit_results_parser,
    port_results_parser,
)

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
        self.db_mgr = None
        self.sentry = False
        self.self_in_py = True
        self.selectorloop = None
        self.continue_install = True
        self.prompt = DEFAULT_PROMPT

        self._initialize_parsers()

        Path(defaults.get("tools-dir")).mkdir(parents=True, exist_ok=True)
        Path(defaults.get("database-dir")).mkdir(parents=True, exist_ok=True)

        # register hooks to handle selector loop start and cleanup
        self.register_preloop_hook(self._preloop_hook)
        self.register_postloop_hook(self._postloop_hook)

    def _initialize_parsers(self):
        """ Internal helper to associate methods with the subparsers that use them """
        db_list_parser.set_defaults(func=self.database_list)
        db_attach_parser.set_defaults(func=self.database_attach)
        db_detach_parser.set_defaults(func=self.database_detach)
        db_delete_parser.set_defaults(func=self.database_delete)
        endpoint_results_parser.set_defaults(func=self.print_endpoint_results)
        target_results_parser.set_defaults(func=self.print_target_results)
        nmap_results_parser.set_defaults(func=self.print_nmap_results)
        technology_results_parser.set_defaults(func=self.print_webanalyze_results)
        searchsploit_results_parser.set_defaults(func=self.print_searchsploit_results)
        port_results_parser.set_defaults(func=self.print_port_results)

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

            self.async_alert(style(f"[-] {words[5].split('_')[0]} queued", fg="bright_white"))
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

            self.async_alert(style(f"[+] {words[5].split('_')[0]} complete!", fg="bright_green"))

    @cmd2.with_argparser(scan_parser)
    def do_scan(self, args):
        """ Scan something.

        Possible scans include
            AmassScan           GobusterScan        SearchsploitScan
            ThreadedNmapScan    WebanalyzeScan      AquatoneScan        FullScan
            MasscanScan         SubjackScan         TKOSubsScan         HTBScan
        """
        if self.db_mgr is None:
            return self.poutput(
                style(f"[!] You are not connected to a database; run database attach before scanning", fg="bright_red")
            )

        self.poutput(
            style(
                "If anything goes wrong, rerun your command with --verbose to enable debug statements.",
                fg="cyan",
                dim=True,
            )
        )

        # get_scans() returns mapping of {classname: [modulename, ...]} in the recon module
        # each classname corresponds to a potential recon-pipeline command, i.e. AmassScan, GobusterScan ...
        scans = get_scans()

        # command is a list that will end up looking something like what's below
        # luigi --module pipeline.recon.web.webanalyze WebanalyzeScan --target-file tesla --top-ports 1000 --interface eth0
        command = ["luigi", "--module", scans.get(args.scantype)[0]]

        tgt_file_path = None
        if args.target:
            tgt_file_fd, tgt_file_path = tempfile.mkstemp()  # temp file to hold target for later parsing

            tgt_file_path = Path(tgt_file_path)
            tgt_idx = args.__statement__.arg_list.index("--target")

            tgt_file_path.write_text(args.target)

            args.__statement__.arg_list[tgt_idx + 1] = str(tgt_file_path)
            args.__statement__.arg_list[tgt_idx] = "--target-file"

        command.extend(args.__statement__.arg_list)

        command.extend(["--db-location", str(self.db_mgr.location)])

        if args.sausage:
            # sausage is not a luigi option, need to remove it
            # name for the option came from @AlphaRingo
            command.pop(command.index("--sausage"))

            webbrowser.open("http://127.0.0.1:8082")  # hard-coded here, can specify different with the status command

        if args.verbose:
            # verbose is not a luigi option, need to remove it
            command.pop(command.index("--verbose"))

            subprocess.run(command)
        else:
            # suppress luigi messages in favor of less verbose/cleaner output
            proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

            # add stderr to the selector loop for processing when there's something to read from the fd
            selector.register(proc.stderr, selectors.EVENT_READ, self._luigi_pretty_printer)

        self.add_dynamic_parser_arguments()
        if tgt_file_path:
            Path(tgt_file_path).unlink()

    @cmd2.with_argparser(install_parser)
    def do_install(self, args):
        """ Install any/all of the libraries/tools necessary to make the recon-pipeline function. """

        # imported tools variable is in global scope, and we reassign over it later
        global tools

        # create .cache dir in the home directory, on the off chance it doesn't exist
        cachedir = Path.home() / ".cache"
        cachedir.mkdir(parents=True, exist_ok=True)

        persistent_tool_dict = cachedir / ".tool-dict.pkl"

        if args.tool == "all":
            # show all tools have been queued for installation
            [
                self.poutput(style(f"[-] {x} queued", fg="bright_white"))
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

                self.poutput(
                    style(f"[!] {args.tool} has an unmet dependency; installing {dependency}", fg="yellow", bold=True)
                )

                # install the dependency before continuing with installation
                self.do_install(dependency)

        if tools.get(args.tool).get("installed"):
            return self.poutput(style(f"[!] {args.tool} is already installed.", fg="yellow"))
        else:
            # list of return values from commands run during each tool installation
            # used to determine whether the tool installed correctly or not
            retvals = list()

            self.poutput(style(f"[*] Installing {args.tool}...", fg="bright_yellow"))

            addl_env_vars = tools.get(args.tool).get("environ")

            if addl_env_vars is not None:
                addl_env_vars.update(dict(os.environ))

            for command in tools.get(args.tool).get("commands"):
                # run all commands required to install the tool

                # print each command being run
                self.poutput(style(f"[=] {command}", fg="cyan"))

                if tools.get(args.tool).get("shell"):

                    # go tools use subshells (cmd1 && cmd2 && cmd3 ...) during install, so need shell=True
                    proc = subprocess.Popen(
                        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=addl_env_vars
                    )
                else:

                    # "normal" command, split up the string as usual and run it
                    proc = subprocess.Popen(
                        shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=addl_env_vars
                    )

                out, err = proc.communicate()

                if err:
                    self.poutput(style(f"[!] {err.decode().strip()}", fg="bright_red"))

                retvals.append(proc.returncode)

        if all(x == 0 for x in retvals):
            # all return values in retvals are 0, i.e. all exec'd successfully; tool has been installed

            self.poutput(style(f"[+] {args.tool} installed!", fg="bright_green"))

            tools[args.tool]["installed"] = True
        else:
            # unsuccessful tool install

            tools[args.tool]["installed"] = False

            self.poutput(
                style(
                    f"[!!] one (or more) of {args.tool}'s commands failed and may have not installed properly; check output from the offending command above...",
                    fg="bright_red",
                    bold=True,
                )
            )

        # store any tool installs/failures (back) to disk
        pickle.dump(tools, persistent_tool_dict.open("wb"))

    @cmd2.with_argparser(status_parser)
    def do_status(self, args):
        """ Open a web browser to Luigi's central scheduler's visualization site """
        webbrowser.open(f"http://{args.host}:{args.port}")

    @staticmethod
    def get_databases():
        """ Simple helper to list all known databases from default directory """
        dbdir = defaults.get("database-dir")

        for db in sorted(Path(dbdir).iterdir()):
            yield db

    def database_list(self, args):
        """ List all known databases """
        try:
            next(self.get_databases())
        except StopIteration:
            return self.poutput(style(f"[-] There are no databases.", fg="bright_white"))

        for i, location in enumerate(self.get_databases(), start=1):
            self.poutput(style(f"   {i}. {location}"))

    def database_attach(self, args):
        """ Attach to the selected database """
        locations = [str(x) for x in self.get_databases()] + ["create new database"]

        location = self.select(locations)

        if location == "create new database":
            location = self.read_input(
                style("new database name? (recommend something unique for this target)\n-> ", fg="bright_white")
            )

            new_location = str(Path(defaults.get("database-dir")) / location)
            index = sorted([new_location] + locations[:-1]).index(new_location) + 1

            self.db_mgr = DBManager(db_location=new_location)

            self.poutput(style(f"[*] created database @ {new_location}", fg="bright_yellow"))

            location = new_location

        else:
            index = locations.index(location) + 1
            self.db_mgr = DBManager(db_location=location)

        self.add_dynamic_parser_arguments()

        self.poutput(
            style(f"[+] attached to sqlite database @ {Path(location).expanduser().resolve()}", fg="bright_green")
        )
        self.prompt = f"[db-{index}] {DEFAULT_PROMPT}"

    def add_dynamic_parser_arguments(self):
        """ Populate command parsers with information from the currently attached database """
        port_results_parser.add_argument("--host", choices=self.db_mgr.get_all_targets(), help="filter results by host")
        port_results_parser.add_argument(
            "--port-number", choices=self.db_mgr.get_all_port_numbers(), help="filter results by port number"
        )
        endpoint_results_parser.add_argument(
            "--status-code", choices=self.db_mgr.get_status_codes(), help="filter results by status code"
        )
        endpoint_results_parser.add_argument(
            "--host", choices=self.db_mgr.get_all_targets(), help="filter results by host"
        )
        nmap_results_parser.add_argument("--host", choices=self.db_mgr.get_all_targets(), help="filter results by host")
        nmap_results_parser.add_argument(
            "--nse-script", choices=self.db_mgr.get_all_nse_script_types(), help="filter results by nse script type ran"
        )
        nmap_results_parser.add_argument(
            "--port", choices=self.db_mgr.get_all_port_numbers(), help="filter results by port scanned"
        )
        nmap_results_parser.add_argument(
            "--product", help="filter results by reported product", choices=self.db_mgr.get_all_nmap_reported_products()
        )
        technology_results_parser.add_argument(
            "--host", choices=self.db_mgr.get_all_targets(), help="filter results by host"
        )
        technology_results_parser.add_argument(
            "--type", choices=self.db_mgr.get_all_web_technology_types(), help="filter results by type"
        )
        technology_results_parser.add_argument(
            "--product", choices=self.db_mgr.get_all_web_technology_products(), help="filter results by product"
        )
        searchsploit_results_parser.add_argument(
            "--host", choices=self.db_mgr.get_all_targets(), help="filter results by host"
        )
        searchsploit_results_parser.add_argument(
            "--type", choices=self.db_mgr.get_all_exploit_types(), help="filter results by exploit type"
        )

    def database_detach(self, args):
        """ Detach from the currently attached database """
        if self.db_mgr is None:
            return self.poutput(style(f"[!] you are not connected to a database", fg="magenta"))

        self.db_mgr.close()
        self.poutput(style(f"[*] detached from sqlite database @ {self.db_mgr.location}", fg="bright_yellow"))
        self.db_mgr = None
        self.prompt = DEFAULT_PROMPT

    def database_delete(self, args):
        """ Delete the selected database """
        locations = [str(x) for x in self.get_databases()]

        to_delete = self.select(locations)
        index = locations.index(to_delete) + 1

        Path(to_delete).unlink()

        if f"[db-{index}]" in self.prompt:
            self.poutput(style(f"[*] detached from sqlite database at {self.db_mgr.location}", fg="bright_yellow"))
            self.prompt = DEFAULT_PROMPT
            self.db_mgr.close()
            self.db_mgr = None

        self.poutput(
            style(f"[+] deleted sqlite database @ {Path(to_delete).expanduser().resolve()}", fg="bright_green")
        )

    @cmd2.with_argparser(database_parser)
    def do_database(self, args):
        """ Manage database connections (list/attach/detach/delete) """
        func = getattr(args, "func", None)
        if func is not None:
            func(args)
        else:
            self.do_help("database")

    def print_target_results(self, args):
        """ Display all Targets from the database, ipv4/6 and hostname """
        results = list()
        printer = self.ppaged if args.paged else self.poutput

        if args.type == "ipv4":
            targets = self.db_mgr.get_all_ipv4_addresses()
        elif args.type == "ipv6":
            targets = self.db_mgr.get_all_ipv6_addresses()
        elif args.type == "domain-name":
            targets = self.db_mgr.get_all_hostnames()
        else:
            targets = self.db_mgr.get_all_targets()

        for target in targets:
            if args.vuln_to_subdomain_takeover:
                tgt = self.db_mgr.get_or_create_target_by_ip_or_hostname(target)
                if not tgt.vuln_to_sub_takeover:
                    # skip targets that aren't vulnerable
                    continue
                vulnstring = style("vulnerable", fg="green")
                vulnstring = f"[{vulnstring}] {target}"
                results.append(vulnstring)
            else:
                results.append(target)

        if results:
            printer("\n".join(results))

    def print_endpoint_results(self, args):
        """ Display all Endpoints from the database """
        host_endpoints = status_endpoints = None
        printer = self.ppaged if args.paged else self.poutput

        color_map = {"2": "green", "3": "blue", "4": "bright_red", "5": "bright_magenta"}

        if args.status_code is not None:
            status_endpoints = self.db_mgr.get_endpoint_by_status_code(args.status_code)

        if args.host is not None:
            host_endpoints = self.db_mgr.get_endpoints_by_ip_or_hostname(args.host)

        endpoints = self.db_mgr.get_all_endpoints()

        for subset in [status_endpoints, host_endpoints]:
            if subset is not None:
                endpoints = set(endpoints).intersection(set(subset))

        results = list()

        for endpoint in endpoints:
            color = color_map.get(str(endpoint.status_code)[0])
            if args.plain:
                results.append(endpoint.url)
            else:
                results.append(f"[{style(endpoint.status_code, fg=color)}] {endpoint.url}")

            if not args.headers:
                continue

            for header in endpoint.headers:
                if args.plain:
                    results.append(f"  {header.name}: {header.value}")
                else:
                    results.append(style(f"  {header.name}:", fg="cyan") + f" {header.value}")

        if results:
            printer("\n".join(results))

    def print_nmap_results(self, args):
        """ Display all NmapResults from the database """
        results = list()
        printer = self.ppaged if args.paged else self.poutput

        if args.host is not None:
            # limit by host, if necessary
            scans = self.db_mgr.get_nmap_scans_by_ip_or_hostname(args.host)
        else:
            scans = self.db_mgr.get_and_filter(NmapResult)

        if args.port is not None or args.product is not None:
            # limit by port, if necessary
            tmpscans = scans[:]
            for scan in scans:
                if args.port is not None and scan.port.port_number != int(args.port) and scan in tmpscans:
                    del tmpscans[tmpscans.index(scan)]
                if args.product is not None and scan.product != args.product and scan in tmpscans:
                    del tmpscans[tmpscans.index(scan)]
            scans = tmpscans

        if args.nse_script:
            # grab the specific nse-script, check that the corresponding nmap result is one we care about, and print
            for nse_scan in self.db_mgr.get_and_filter(NSEResult, script_id=args.nse_script):
                for nmap_result in nse_scan.nmap_results:
                    if nmap_result not in scans:
                        continue

                    results.append(nmap_result.pretty(nse_results=[nse_scan], commandline=args.commandline))
        else:
            # done filtering, grab w/e is left
            for scan in scans:
                results.append(scan.pretty(commandline=args.commandline))

        if results:
            printer("\n".join(results))

    def print_webanalyze_results(self, args):
        """ Display all NmapResults from the database """
        results = list()
        printer = self.ppaged if args.paged else self.poutput

        filters = dict()
        if args.type is not None:
            filters["type"] = args.type
        if args.product is not None:
            filters["text"] = args.product

        if args.host:
            tgt = self.db_mgr.get_or_create_target_by_ip_or_hostname(args.host)
            printer(args.host)
            printer("=" * len(args.host))
            for tech in tgt.technologies:
                if args.product is not None and args.product != tech.text:
                    continue
                if args.type is not None and args.type != tech.type:
                    continue
                printer(f"   - {tech.text} ({tech.type})")
        else:
            for scan in self.db_mgr.get_and_filter(Technology, **filters):
                results.append(scan.pretty(padlen=1))

        if results:
            printer("\n".join(results))

    def print_searchsploit_results(self, args):
        """ Display all NmapResults from the database """
        results = list()
        targets = self.db_mgr.get_all_targets()
        printer = self.ppaged if args.paged else self.poutput

        for ss_scan in self.db_mgr.get_and_filter(SearchsploitResult):
            tmp_targets = set()

            if (
                args.host is not None
                and self.db_mgr.get_or_create_target_by_ip_or_hostname(args.host) != ss_scan.target
            ):
                continue

            if ss_scan.target.hostname in targets:
                # hostname is in targets, so hasn't been reported yet
                tmp_targets.add(ss_scan.target.hostname)  # add to this report
                targets.remove(ss_scan.target.hostname)  # remove from targets list, having been reported

            for ipaddr in ss_scan.target.ip_addresses:
                address = ipaddr.ipv4_address or ipaddr.ipv6_address
                if address is not None and address in targets:
                    tmp_targets.add(ipaddr.ipv4_address)
                    targets.remove(ipaddr.ipv4_address)

            if tmp_targets:
                header = ", ".join(tmp_targets)
                results.append(header)
                results.append("=" * len(header))

                for scan in ss_scan.target.searchsploit_results:
                    if args.type is not None and scan.type != args.type:
                        continue

                    results.append(scan.pretty(fullpath=args.fullpath))

        if results:
            printer("\n".join(results))

    def print_port_results(self, args):
        """ Display all Ports from the database """
        results = list()
        targets = self.db_mgr.get_all_targets()
        printer = self.ppaged if args.paged else self.poutput

        for target in targets:
            if args.host is not None and target != args.host:
                # host specified, but it's not this particular target
                continue

            ports = [
                str(port.port_number) for port in self.db_mgr.get_or_create_target_by_ip_or_hostname(target).open_ports
            ]

            if args.port_number and args.port_number not in ports:
                continue

            if ports:
                results.append(f"{target}: {','.join(ports)}")

        if results:
            printer("\n".join(results))

    @cmd2.with_argparser(view_parser)
    def do_view(self, args):
        """ View results of completed scans """
        if self.db_mgr is None:
            return self.poutput(style(f"[!] you are not connected to a database", fg="magenta"))

        func = getattr(args, "func", None)

        if func is not None:
            func(args)
        else:
            self.do_help("view")


def main(
    name,
    old_tools_dir=Path().home() / ".recon-tools",
    old_tools_dict=Path().home() / ".cache" / ".tool-dict.pkl",
    old_searchsploit_rc=Path().home() / ".searchsploit_rc",
):
    """ Functionified for testability """
    if name == "__main__":

        if old_tools_dir.exists() and old_tools_dir.is_dir():
            # want to try and ensure a smooth transition for folks who have used the pipeline before from
            # v0.8.4 and below to v0.9.0+
            print(style(f"[*] Found remnants of an older version of recon-pipeline.", fg="bright_yellow"))
            print(
                style(
                    f"[*] It's {style('strongly', fg='red')} advised that you allow us to remove them.",
                    fg="bright_white",
                )
            )
            print(
                style(
                    f"[*] Do you want to remove {old_tools_dir}/*, {old_searchsploit_rc}, and {old_tools_dict}?",
                    fg="bright_white",
                )
            )

            answer = cmd2.Cmd().select(["Yes", "No"])
            print(style(f"[+] You chose {answer}", fg="bright_green"))

            if answer == "Yes":
                shutil.rmtree(old_tools_dir)
                print(style(f"[+] {old_tools_dir} removed", fg="bright_green"))

                if old_tools_dict.exists():
                    old_tools_dict.unlink()
                    print(style(f"[+] {old_tools_dict} removed", fg="bright_green"))

                if old_searchsploit_rc.exists():
                    old_searchsploit_rc.unlink()
                    print(style(f"[+] {old_searchsploit_rc} removed", fg="bright_green"))

                print(style(f"[=] Please run the install all command to complete setup", fg="bright_blue"))

        rs = ReconShell(persistent_history_file="~/.reconshell_history", persistent_history_length=10000)
        sys.exit(rs.cmdloop())


main(name=__name__)
