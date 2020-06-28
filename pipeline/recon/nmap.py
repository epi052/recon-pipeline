import ast
import logging
import subprocess
import concurrent.futures
from pathlib import Path

import luigi
import sqlalchemy
from luigi.util import inherits
from libnmap.parser import NmapParser
from luigi.contrib.sqla import SQLAlchemyTarget

import pipeline.models.db_manager
from .masscan import ParseMasscanOutput
from .config import defaults
from .helpers import get_ip_address_version, is_ip_address

from ..tools import tools
from .helpers import get_tool_state
from ..models.port_model import Port
from ..models.nse_model import NSEResult
from ..models.target_model import Target
from ..models.nmap_model import NmapResult
from ..models.ip_address_model import IPAddress
from ..models.searchsploit_model import SearchsploitResult


@inherits(ParseMasscanOutput)
class ThreadedNmapScan(luigi.Task):
    """ Run ``nmap`` against specific targets and ports gained from the ParseMasscanOutput Task.

    Install:
        ``nmap`` is already on your system if you're using kali.  If you're not using kali, refer to your own
        distributions instructions for installing ``nmap``.

    Basic Example:
        .. code-block:: console

            nmap --open -sT -sC -T 4 -sV -Pn -p 43,25,21,53,22 -oA htb-targets-nmap-results/nmap.10.10.10.155-tcp 10.10.10.155

    Luigi Example:
        .. code-block:: console

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.nmap ThreadedNmap --target-file htb-targets --top-ports 5000

    Args:
        threads: number of threads for parallel nmap command execution
        db_location: specifies the path to the database used for storing results *Required by upstream Task*
        rate: desired rate for transmitting packets (packets per second) *Required by upstream Task*
        interface: use the named raw network interface, such as "eth0" *Required by upstream Task*
        top_ports: Scan top N most popular ports *Required by upstream Task*
        ports: specifies the port(s) to be scanned *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

    threads = luigi.Parameter(default=defaults.get("threads"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = pipeline.models.db_manager.DBManager(db_location=self.db_location)
        self.results_subfolder = (Path(self.results_dir) / "nmap-results").expanduser().resolve()

    def requires(self):
        """ ThreadedNmap depends on ParseMasscanOutput to run.

        TargetList expects target_file, results_dir, and db_location as parameters.
        Masscan expects rate, target_file, interface, and either ports or top_ports as parameters.

        Returns:
            luigi.Task - ParseMasscanOutput
        """
        args = {
            "results_dir": self.results_dir,
            "rate": self.rate,
            "target_file": self.target_file,
            "top_ports": self.top_ports,
            "interface": self.interface,
            "ports": self.ports,
            "db_location": self.db_location,
        }
        return ParseMasscanOutput(**args)

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output folder is TARGET_FILE-nmap-results.

        The output folder will be populated with all of the output files generated by
        any nmap commands run.  Because the nmap command uses -oA, there will be three
        files per target scanned: .xml, .nmap, .gnmap.

        Returns:
            luigi.local_target.LocalTarget
        """
        return {
            "sqltarget": SQLAlchemyTarget(
                connection_string=self.db_mgr.connection_string, target_table="nmap_result", update_id=self.task_id
            ),
            "localtarget": luigi.LocalTarget(str(self.results_subfolder)),
        }

    def parse_nmap_output(self):
        """ Read nmap .xml results and add entries into specified database """

        for entry in self.results_subfolder.glob("nmap*.xml"):
            # relying on python-libnmap here
            report = NmapParser.parse_fromfile(entry)

            for host in report.hosts:
                for service in host.services:
                    port = self.db_mgr.get_or_create(Port, protocol=service.protocol, port_number=service.port)

                    if is_ip_address(host.address) and get_ip_address_version(host.address) == "4":
                        ip_address = self.db_mgr.get_or_create(IPAddress, ipv4_address=host.address)
                    else:
                        ip_address = self.db_mgr.get_or_create(IPAddress, ipv6_address=host.address)

                    if ip_address.target is None:
                        # account for ip addresses identified that aren't already tied to a target
                        # almost certainly ipv6 addresses
                        tgt = self.db_mgr.get_or_create(Target)
                        tgt.ip_addresses.append(ip_address)
                    else:
                        tgt = ip_address.target

                    try:
                        nmap_result = self.db_mgr.get_or_create(
                            NmapResult, port=port, ip_address=ip_address, target=tgt
                        )
                    except sqlalchemy.exc.StatementError:
                        # one of the three (port/ip/tgt) didn't exist and we're querying on ids that the db doesn't know
                        self.db_mgr.add(port)
                        self.db_mgr.add(ip_address)
                        self.db_mgr.add(tgt)
                        nmap_result = self.db_mgr.get_or_create(
                            NmapResult, port=port, ip_address=ip_address, target=tgt
                        )

                    for nse_result in service.scripts_results:
                        script_id = nse_result.get("id")
                        script_output = nse_result.get("output")
                        nse_obj = self.db_mgr.get_or_create(NSEResult, script_id=script_id, script_output=script_output)
                        nmap_result.nse_results.append(nse_obj)

                    nmap_result.open = service.open()
                    nmap_result.reason = service.reason
                    nmap_result.service = service.service
                    nmap_result.commandline = report.commandline
                    nmap_result.product = service.service_dict.get("product")
                    nmap_result.product_version = service.service_dict.get("version")
                    nmap_result.target.nmap_results.append(nmap_result)

                    self.db_mgr.add(nmap_result)
                    self.output().get("sqltarget").touch()

        self.db_mgr.close()

    def run(self):
        """ Parses pickled target info dictionary and runs targeted nmap scans against only open ports. """
        try:
            self.threads = abs(int(self.threads))
        except (TypeError, ValueError):
            return logging.error("The value supplied to --threads must be a non-negative integer.")

        nmap_command = [  # placeholders will be overwritten with appropriate info in loop below
            "nmap",
            "--open",
            "PLACEHOLDER-IDX-2",
            "-n",
            "-sC",
            "-T",
            "4",
            "-sV",
            "-Pn",
            "-p",
            "PLACEHOLDER-IDX-10",
            "-oA",
        ]

        commands = list()

        for target in self.db_mgr.get_all_targets():
            for protocol in ("tcp", "udp"):
                ports = self.db_mgr.get_ports_by_ip_or_host_and_protocol(target, protocol)
                if ports:
                    tmp_cmd = nmap_command[:]
                    tmp_cmd[2] = "-sT" if protocol == "tcp" else "-sU"

                    # arg to -oA, will drop into subdir off curdir
                    tmp_cmd[10] = ",".join(ports)
                    tmp_cmd.append(str(Path(self.output().get("localtarget").path) / f"nmap.{target}-{protocol}"))

                    if is_ip_address(target) and get_ip_address_version(target) == "6":
                        # got an ipv6 address
                        tmp_cmd.insert(-2, "-6")

                    tmp_cmd.append(target)  # target as final arg to nmap

                    commands.append(tmp_cmd)

        # basically mkdir -p, won't error out if already there
        self.results_subfolder.mkdir(parents=True, exist_ok=True)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:

            executor.map(subprocess.run, commands)

        self.parse_nmap_output()


@inherits(ThreadedNmapScan)
class SearchsploitScan(luigi.Task):
    """ Run ``searchcploit`` against each ``nmap*.xml`` file in the **TARGET-nmap-results** directory and write results to disk.

    Install:
        ``searchcploit`` is already on your system if you're using kali.  If you're not using kali, refer to your own
        distributions instructions for installing ``searchcploit``.

    Basic Example:
        .. code-block:: console

            searchsploit --nmap htb-targets-nmap-results/nmap.10.10.10.155-tcp.xml

    Luigi Example:
        .. code-block:: console

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.nmap Searchsploit --target-file htb-targets --top-ports 5000

    Args:
        threads: number of threads for parallel nmap command execution *Required by upstream Task*
        db_location: specifies the path to the database used for storing results *Required by upstream Task*
        rate: desired rate for transmitting packets (packets per second) *Required by upstream Task*
        interface: use the named raw network interface, such as "eth0" *Required by upstream Task*
        top_ports: Scan top N most popular ports *Required by upstream Task*
        ports: specifies the port(s) to be scanned *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifies the directory on disk to which all Task results are written *Required by upstream Task*
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = pipeline.models.db_manager.DBManager(db_location=self.db_location)

    @staticmethod
    def meets_requirements():
        """ Reports whether or not this scan's needed tool(s) are installed or not """
        needs = ["searchsploit"]
        tools = get_tool_state()

        if tools:
            return all([tools.get(x).get("installed") is True for x in needs])

    def requires(self):
        """ Searchsploit depends on ThreadedNmap to run.

        TargetList expects target_file, results_dir, and db_location as parameters.
        Masscan expects rate, target_file, interface, and either ports or top_ports as parameters.
        ThreadedNmap expects threads

        Returns:
            luigi.Task - ThreadedNmap
        """
        args = {
            "rate": self.rate,
            "ports": self.ports,
            "threads": self.threads,
            "top_ports": self.top_ports,
            "interface": self.interface,
            "target_file": self.target_file,
            "results_dir": self.results_dir,
            "db_location": self.db_location,
        }
        return ThreadedNmapScan(**args)

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output folder is TARGET_FILE-searchsploit-results.

        The output folder will be populated with all of the output files generated by
        any searchsploit commands run.

        Returns:
            luigi.local_target.LocalTarget
        """
        return SQLAlchemyTarget(
            connection_string=self.db_mgr.connection_string, target_table="searchsploit_result", update_id=self.task_id
        )

    def run(self):
        """ Grabs the xml files created by ThreadedNmap and runs searchsploit --nmap on each one, saving the output. """
        for entry in Path(self.input().get("localtarget").path).glob("nmap*.xml"):
            proc = subprocess.run(
                [tools.get("searchsploit").get("path"), "-j", "-v", "--nmap", str(entry)], stdout=subprocess.PIPE
            )
            if proc.stdout:
                # change  wall-searchsploit-results/nmap.10.10.10.157-tcp to 10.10.10.157
                ipaddr = entry.stem.replace("nmap.", "").replace("-tcp", "").replace("-udp", "")

                contents = proc.stdout.decode()
                for line in contents.splitlines():
                    if "Title" in line:
                        # {'Title': "Nginx (Debian Based Distros + Gentoo) ... }

                        # oddity introduced on 15 Apr 2020 from an exploitdb update
                        #   entries have two double quotes in a row for no apparent reason
                        #   {"Title":"PHP-FPM + Nginx - Remote Code Execution"", ...
                        #   seems to affect all entries at the moment. will remove this line if it
                        #   ever returns to normal
                        line = line.replace('""', '"')

                        if line.endswith(","):
                            # result would be a tuple if the comma is left on the line; remove it
                            tmp_result = ast.literal_eval(line.strip()[:-1])
                        else:
                            # normal dict
                            tmp_result = ast.literal_eval(line.strip())

                        tgt = self.db_mgr.get_or_create_target_by_ip_or_hostname(ipaddr)

                        ssr_type = tmp_result.get("Type")
                        ssr_title = tmp_result.get("Title")
                        ssr_path = tmp_result.get("Path")

                        ssr = self.db_mgr.get_or_create(
                            SearchsploitResult, type=ssr_type, title=ssr_title, path=ssr_path
                        )

                        tgt.searchsploit_results.append(ssr)

                        self.db_mgr.add(tgt)
                        self.output().touch()

        self.db_mgr.close()
