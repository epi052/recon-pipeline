from pathlib import Path

import luigi
from luigi.util import inherits
from luigi.contrib.external_program import ExternalProgramTask

from .targets import GatherWebTargets
from ..config import tool_paths, defaults


@inherits(GatherWebTargets)
class TKOSubsScan(ExternalProgramTask):
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

        Naming convention for the output file is tkosubs.TARGET_FILE.csv.

        Returns:
            luigi.local_target.LocalTarget
        """
        results_subfolder = Path(self.results_dir) / "tkosubs-results"

        new_path = results_subfolder / "tkosubs.csv"

        return luigi.LocalTarget(new_path.resolve())

    def program_args(self):
        """ Defines the options/arguments sent to tko-subs after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        Path(self.output().path).parent.mkdir(parents=True, exist_ok=True)

        subdomains = Path(self.results_dir) / "target-results" / "subdomains"

        if not subdomains.exists():
            return

        command = [
            tool_paths.get("tko-subs"),
            f"-domains={str(subdomains.resolve())}",
            f"-data={tool_paths.get('tko-subs-dir')}/providers-data.csv",
            f"-output={self.output().path}",
        ]

        return command


@inherits(GatherWebTargets)
class SubjackScan(ExternalProgramTask):
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

    threads = luigi.Parameter(default=defaults.get("threads", ""))

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

        Naming convention for the output file is subjack.TARGET_FILE.txt.

        Returns:
            luigi.local_target.LocalTarget
        """
        results_subfolder = Path(self.results_dir) / "subjack-results"

        new_path = results_subfolder / "subjack.txt"

        return luigi.LocalTarget(new_path.resolve())

    def program_args(self):
        """ Defines the options/arguments sent to subjack after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        Path(self.output().path).parent.mkdir(parents=True, exist_ok=True)

        command = [
            tool_paths.get("subjack"),
            "-w",
            self.input().path,
            "-t",
            self.threads,
            "-a",
            "-timeout",
            "30",
            "-o",
            self.output().path,
            "-v",
            "-ssl",
            "-c",
            tool_paths.get("subjack-fingerprints"),
        ]

        return command
