import socket

import cmd2

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
    "--results-dir", completer_method=cmd2.Cmd.path_complete, help="directory in which to save scan results"
)
scan_parser.add_argument(
    "--wordlist", completer_method=cmd2.Cmd.path_complete, help="path to wordlist used by gobuster"
)
scan_parser.add_argument(
    "--interface",
    choices_function=lambda: [x[1] for x in socket.if_nameindex()],
    help="which interface masscan should use",
)
scan_parser.add_argument("--recursive", action="store_true", help="whether or not to recursively gobust")
scan_parser.add_argument("--rate", help="rate at which masscan should scan")
scan_parser.add_argument(
    "--top-ports", help="ports to scan as specified by nmap's list of top-ports (only meaningful to around 5000)"
)
scan_parser.add_argument("--ports", help="port specification for masscan (all ports example: 1-65535,U:1-65535)")
scan_parser.add_argument("--threads", help="number of threads for all of the threaded applications to use")
scan_parser.add_argument("--scan-timeout", help="scan timeout for aquatone")
scan_parser.add_argument("--proxy", help="proxy for gobuster if desired (ex. 127.0.0.1:8080)")
scan_parser.add_argument("--extensions", help="list of extensions for gobuster (ex. asp,html,aspx)")
scan_parser.add_argument(
    "--sausage",
    action="store_true",
    help="open a web browser to Luigi's central scheduler's visualization site (see how the sausage is made!)",
)
scan_parser.add_argument(
    "--local-scheduler", action="store_true", help="use the local scheduler instead of the central scheduler (luigid)"
)
scan_parser.add_argument(
    "--verbose", action="store_true", help="shows debug messages from luigi, useful for troubleshooting"
)

# top level and subparsers for ReconShell's database command
database_parser = cmd2.Cmd2ArgumentParser()
database_subparsers = database_parser.add_subparsers(title="subcommands")

db_list_parser = database_subparsers.add_parser("list", help="List all known databases")
db_delete_parser = database_subparsers.add_parser("delete", help="Delete the selected database")
db_attach_parser = database_subparsers.add_parser("attach", help="Attach to the selected database")
db_detach_parser = database_subparsers.add_parser("detach", help="Detach from the currently attached database")


# ReconShell's view-results command
view_parser = cmd2.Cmd2ArgumentParser()
view_subparsers = view_parser.add_subparsers(title="result types")

target_results_parser = view_subparsers.add_parser(
    "targets", help="List all known targets (ipv4/6 & domain names); produced by amass"
)

endpoint_results_parser = view_subparsers.add_parser("endpoints", help="List all known endpoints; produced by gobuster")
endpoint_results_parser.add_argument(
    "--headers", action="store_true", default=False, help="include headers found at each endpoint"
)
endpoint_results_parser.add_argument("--paged", action="store_true", default=False, help="display output page-by-page")
endpoint_results_parser.add_argument(
    "--plain", action="store_true", default=False, help="display without status-codes/color"
)
