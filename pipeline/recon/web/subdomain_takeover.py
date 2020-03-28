import re
import csv
import subprocess
from pathlib import Path

import luigi
from luigi.util import inherits
from luigi.contrib.sqla import SQLAlchemyTarget

from ...models import DBManager
from .targets import GatherWebTargets
from ..config import tool_paths, defaults


@inherits(GatherWebTargets)
class TKOSubsScan(luigi.Task):
    """ Use ``tko-subs`` to scan for potential subdomain takeovers.

    Install:
        .. code-block:: console

            go get github.com/anshumanbh/tko-subs
            cd ~/go/src/github.com/anshumanbh/tko-subs
            go build
            go install

    Basic Example:
        .. code-block:: console

            tko-subs -domains=tesla.subdomains -data=/root/go/src/github.com/anshumanbh/tko-subs/providers-data.csv -output=tkosubs.tesla.csv

    Luigi Example:
        .. code-block:: console

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.web.subdomain_takeover TKOSubsScan --target-file tesla --top-ports 1000 --interface eth0

    Args:
        db_location: specifies the path to the database used for storing results *Required by upstream Task*
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *Optional by upstream Task*
        top_ports: Scan top N most popular ports *Required by upstream Task*
        ports: specifies the port(s) to be scanned *Required by upstream Task*
        interface: use the named raw network interface, such as "eth0" *Required by upstream Task*
        rate: desired rate for transmitting packets (packets per second) *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = DBManager(db_location=self.db_location)
        self.results_subfolder = (Path(self.results_dir) / "tkosubs-results").resolve()
        self.output_file = self.results_subfolder / "tkosubs.csv"

    def requires(self):
        """ TKOSubsScan depends on GatherWebTargets to run.

        GatherWebTargets accepts exempt_list and expects rate, target_file, interface,
                         and either ports or top_ports as parameters

        Returns:
            luigi.Task - GatherWebTargets
        """
        args = {
            "results_dir": self.results_dir,
            "rate": self.rate,
            "target_file": self.target_file,
            "top_ports": self.top_ports,
            "interface": self.interface,
            "ports": self.ports,
            "exempt_list": self.exempt_list,
            "db_location": self.db_location,
        }
        return GatherWebTargets(**args)

    def output(self):
        """ Returns the target output for this task.

        Returns:
            luigi.contrib.sqla.SQLAlchemyTarget
        """
        return SQLAlchemyTarget(
            connection_string=self.db_mgr.connection_string, target_table="target", update_id=self.task_id
        )

    def parse_results(self):
        """ Reads in the tkosubs .csv file and updates the associated Target record. """
        with open(self.output_file, newline="") as f:
            reader = csv.reader(f)

            next(reader, None)  # skip the headers

            for row in reader:
                domain = row[0]
                is_vulnerable = row[3]

                if "true" in is_vulnerable.lower():
                    tgt = self.db_mgr.get_target_by_ip_or_hostname(domain)
                    tgt.vuln_to_sub_takeover = True

                    self.db_mgr.add(tgt)
                    self.output().touch()

            self.db_mgr.close()

        # make sure task doesn't fail due to no results, it's the last in its chain, so doesn't
        # affect any downstream tasks
        self.output().touch()

    def run(self):
        """ Defines the options/arguments sent to tko-subs after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        self.results_subfolder.mkdir(parents=True, exist_ok=True)

        domains = self.db_mgr.get_all_hostnames()

        if not domains:
            return

        command = [
            tool_paths.get("tko-subs"),
            f"-domain={','.join(domains)}",
            f"-data={tool_paths.get('tko-subs-dir')}/providers-data.csv",
            f"-output={self.output_file}",
        ]

        subprocess.run(command)

        self.parse_results()


@inherits(GatherWebTargets)
class SubjackScan(luigi.Task):
    """ Use ``subjack`` to scan for potential subdomain takeovers.

    Install:
        .. code-block:: console

            go get github.com/haccer/subjack
            cd ~/go/src/github.com/haccer/subjack
            go build
            go install

    Basic Example:
        .. code-block:: console

            subjack -w webtargets.tesla.txt -t 100 -timeout 30 -o subjack.tesla.txt -ssl

    Luigi Example:
        .. code-block:: console

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.web.subdomain_takeover SubjackScan --target-file tesla --top-ports 1000 --interface eth0

    Args:
        threads: number of threads for parallel subjack command execution
        db_location: specifies the path to the database used for storing results *Required by upstream Task*
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *Optional by upstream Task*
        top_ports: Scan top N most popular ports *Required by upstream Task*
        ports: specifies the port(s) to be scanned *Required by upstream Task*
        interface: use the named raw network interface, such as "eth0" *Required by upstream Task*
        rate: desired rate for transmitting packets (packets per second) *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

    threads = luigi.Parameter(default=defaults.get("threads"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = DBManager(db_location=self.db_location)
        self.results_subfolder = (Path(self.results_dir) / "subjack-results").resolve()
        self.output_file = self.results_subfolder / "subjack.txt"

    def requires(self):
        """ SubjackScan depends on GatherWebTargets to run.

        GatherWebTargets accepts exempt_list and expects rate, target_file, interface,
                         and either ports or top_ports as parameters

        Returns:
            luigi.Task - GatherWebTargets
        """
        args = {
            "results_dir": self.results_dir,
            "rate": self.rate,
            "target_file": self.target_file,
            "top_ports": self.top_ports,
            "interface": self.interface,
            "ports": self.ports,
            "exempt_list": self.exempt_list,
            "db_location": self.db_location,
        }
        return GatherWebTargets(**args)

    def output(self):
        """ Returns the target output for this task.

        Returns:
            luigi.contrib.sqla.SQLAlchemyTarget
        """
        return SQLAlchemyTarget(
            connection_string=self.db_mgr.connection_string, target_table="target", update_id=self.task_id
        )

    def parse_results(self):
        """ Reads in the subjack's subjack.txt file and updates the associated Target record. """

        with open(self.output_file) as f:
            """ example data

                [Not Vulnerable] 52.53.92.161:443
                [Not Vulnerable] 13.57.162.100
                [Not Vulnerable] 2606:4700:10::6814:3d33
                [Not Vulnerable] assetinventory.bugcrowd.com
            """
            for line in f:
                match = re.match(r"\[(?P<vuln_status>.+)] (?P<ip_or_hostname>.*)", line)

                if not match:
                    continue

                if match.group("vuln_status") == "Not Vulnerable":
                    continue

                ip_or_host = match.group("ip_or_hostname")

                if ip_or_host.count(":") == 1:  # ip or host/port
                    ip_or_host, port = ip_or_host.split(":", maxsplit=1)

                tgt = self.db_mgr.get_target_by_ip_or_hostname(ip_or_host)

                tgt.vuln_to_sub_takeover = True

                self.db_mgr.add(tgt)
                self.output().touch()

            self.db_mgr.close()

        # make sure task doesn't fail due to no results, it's the last in its chain, so doesn't
        # affect any downstream tasks
        self.output().touch()

    def run(self):
        """ Defines the options/arguments sent to subjack after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        self.results_subfolder.mkdir(parents=True, exist_ok=True)

        hostnames = self.db_mgr.get_all_hostnames()

        if not hostnames:
            return

        subjack_input_file = self.results_subfolder / "input-from-webtargets"
        with open(subjack_input_file, "w") as f:
            for hostname in hostnames:
                f.write(f"{hostname}\n")

        command = [
            tool_paths.get("subjack"),
            "-w",
            str(subjack_input_file),
            "-t",
            self.threads,
            "-a",
            "-timeout",
            "30",
            "-o",
            str(self.output_file),
            "-v",
            "-ssl",
            "-c",
            tool_paths.get("subjack-fingerprints"),
        ]

        subprocess.run(command)

        self.parse_results()

        subjack_input_file.unlink()
