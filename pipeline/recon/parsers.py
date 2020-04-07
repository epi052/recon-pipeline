import socket

import cmd2

from .config import defaults
from .helpers import get_scans
from .tool_definitions import tools

# options for ReconShell's 'install' command
install_parser = cmd2.Cmd2ArgumentParser()
install_parser.add_argument("tool", help="which tool to install", choices=list(tools.keys()) + ["all"])


# options for ReconShell's 'status' command
status_parser = cmd2.Cmd2ArgumentParser()
status_parser.add_argument(
    "--port",
    help="port on which the luigi central scheduler's visualization site is running (default: 8082)",
    default="8082",
)
status_parser.add_argument(
    "--host",
    help="host on which the luigi central scheduler's visualization site is running (default: localhost)",
    default="127.0.0.1",
)


# options for ReconShell's 'scan' command
scan_parser = cmd2.Cmd2ArgumentParser()
scan_parser.add_argument("scantype", choices_function=get_scans, help="which type of scan to run")
scan_parser.add_argument(
    "--target-file",
    completer_method=cmd2.Cmd.path_complete,
    help="file created by the user that defines the target's scope; list of ips/domains (required)",
    required=True,
)
scan_parser.add_argument(
    "--exempt-list", completer_method=cmd2.Cmd.path_complete, help="list of blacklisted ips/domains"
)
scan_parser.add_argument(
    "--results-dir",
    completer_method=cmd2.Cmd.path_complete,
    help=f"directory in which to save scan results (default: {defaults.get('results-dir')})",
)
scan_parser.add_argument(
    "--wordlist",
    completer_method=cmd2.Cmd.path_complete,
    help=f"path to wordlist used by gobuster (default: {defaults.get('gobuster-wordlist')})",
)
scan_parser.add_argument(
    "--interface",
    choices_function=lambda: [x[1] for x in socket.if_nameindex()],
    help=f"which interface masscan should use (default: {defaults.get('masscan-iface')})",
)
scan_parser.add_argument(
    "--recursive", action="store_true", help="whether or not to recursively gobust (default: False)", default=False
)
scan_parser.add_argument("--rate", help=f"rate at which masscan should scan (default: {defaults.get('masscan-rate')})")

port_group = scan_parser.add_mutually_exclusive_group()
port_group.add_argument(
    "--top-ports",
    help="ports to scan as specified by nmap's list of top-ports (only meaningful to around 5000)",
    type=int,
)
port_group.add_argument("--ports", help="port specification for masscan (all ports example: 1-65535,U:1-65535)")

scan_parser.add_argument(
    "--threads",
    help=f"number of threads for all of the threaded applications to use (default: {defaults.get('threads')})",
)
scan_parser.add_argument(
    "--scan-timeout", help=f"scan timeout for aquatone (default: {defaults.get('aquatone-scan-timeout')})"
)
scan_parser.add_argument("--proxy", help="proxy for gobuster if desired (ex. 127.0.0.1:8080)")
scan_parser.add_argument("--extensions", help="list of extensions for gobuster (ex. asp,html,aspx)")
scan_parser.add_argument(
    "--sausage",
    action="store_true",
    default=False,
    help="open a web browser to Luigi's central scheduler's visualization site (see how the sausage is made!)",
)
scan_parser.add_argument(
    "--local-scheduler",
    action="store_true",
    help="use the local scheduler instead of the central scheduler (luigid) (default: False)",
    default=False,
)
scan_parser.add_argument(
    "--verbose",
    action="store_true",
    help="shows debug messages from luigi, useful for troubleshooting (default: False)",
)

# top level and subparsers for ReconShell's database command
database_parser = cmd2.Cmd2ArgumentParser()
database_subparsers = database_parser.add_subparsers(
    title="subcommands", help="Manage database connections (list/attach/detach/delete)"
)

db_list_parser = database_subparsers.add_parser("list", help="List all known databases")
db_delete_parser = database_subparsers.add_parser("delete", help="Delete the selected database")
db_attach_parser = database_subparsers.add_parser("attach", help="Attach to the selected database")
db_detach_parser = database_subparsers.add_parser("detach", help="Detach from the currently attached database")


# ReconShell's view command
view_parser = cmd2.Cmd2ArgumentParser()
view_subparsers = view_parser.add_subparsers(title="result types")

target_results_parser = view_subparsers.add_parser(
    "targets", help="List all known targets (ipv4/6 & domain names); produced by amass", conflict_handler="resolve"
)
target_results_parser.add_argument(
    "--vuln-to-subdomain-takeover",
    action="store_true",
    default=False,
    help="show targets identified as vulnerable to subdomain takeover",
)
target_results_parser.add_argument(
    "--paged", action="store_true", default=False, help="display output page-by-page (default: False)"
)

technology_results_parser = view_subparsers.add_parser(
    "web-technologies",
    help="List all known web technologies identified; produced by webanalyze",
    conflict_handler="resolve",
)
technology_results_parser.add_argument(
    "--paged", action="store_true", default=False, help="display output page-by-page (default: False)"
)

endpoint_results_parser = view_subparsers.add_parser(
    "endpoints", help="List all known endpoints; produced by gobuster", conflict_handler="resolve"
)
endpoint_results_parser.add_argument(
    "--headers", action="store_true", default=False, help="include headers found at each endpoint (default: False)"
)
endpoint_results_parser.add_argument(
    "--paged", action="store_true", default=False, help="display output page-by-page (default: False)"
)
endpoint_results_parser.add_argument(
    "--plain", action="store_true", default=False, help="display without status-codes/color (default: False)"
)

nmap_results_parser = view_subparsers.add_parser(
    "nmap-scans", help="List all known nmap scan results; produced by nmap", conflict_handler="resolve"
)
nmap_results_parser.add_argument(
    "--paged", action="store_true", default=False, help="display output page-by-page (default: False)"
)
nmap_results_parser.add_argument(
    "--commandline", action="store_true", default=False, help="display command used to scan (default: False)"
)

searchsploit_results_parser = view_subparsers.add_parser(
    "searchsploit-results",
    help="List all known searchsploit hits; produced by searchsploit",
    conflict_handler="resolve",
)
searchsploit_results_parser.add_argument(
    "--paged", action="store_true", default=False, help="display output page-by-page (default: False)"
)
searchsploit_results_parser.add_argument(
    "--fullpath", action="store_true", default=False, help="display full path to exploit PoC (default: False)"
)

port_results_parser = view_subparsers.add_parser(
    "ports", help="List all known open ports; produced by masscan", conflict_handler="resolve"
)
port_results_parser.add_argument(
    "--paged", action="store_true", default=False, help="display output page-by-page (default: False)"
)

# all options below this line will be updated with a choices option in recon-pipeline.py's
# add_dynamic_parser_arguments function.  They're included here primarily to ease auto documentation of the commands
port_results_parser.add_argument("--host", help="filter results by host")
endpoint_results_parser.add_argument("--status-code", help="filter results by status code")
endpoint_results_parser.add_argument("--host", help="filter results by host")
nmap_results_parser.add_argument("--host", help="filter results by host")
nmap_results_parser.add_argument("--nse-script", help="filter results by nse script type ran")
nmap_results_parser.add_argument("--port", help="filter results by port scanned")
nmap_results_parser.add_argument("--product", help="filter results by reported product")
technology_results_parser.add_argument("--host", help="filter results by host")
searchsploit_results_parser.add_argument("--host", help="filter results by host")
searchsploit_results_parser.add_argument("--type", help="filter results by exploit type")
