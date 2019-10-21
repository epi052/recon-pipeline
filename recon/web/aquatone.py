import subprocess
from pathlib import Path

import luigi
from luigi.util import inherits

from recon.config import tool_paths, defaults
from recon.web.targets import GatherWebTargets


@inherits(GatherWebTargets)
class AquatoneScan(luigi.Task):
    """ Screenshot all web targets and generate HTML report.

    aquatone commands are structured like the example below.

    aquatone --open -sT -sC -T 4 -sV -Pn -p 43,25,21,53,22 -oA htb-targets-nmap-results/nmap.10.10.10.155-tcp 10.10.10.155

    An example of the corresponding luigi command is shown below.

    PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.web.aquatone AquatoneScan --target-file tesla --top-ports 1000

    Args:
        threads: number of threads for parallel aquatone command execution
        scan_timeout: timeout in miliseconds for aquatone port scans
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *--* Optional for upstream Task
        top_ports: Scan top N most popular ports *--* Required by upstream Task
        ports: specifies the port(s) to be scanned *--* Required by upstream Task
        interface: use the named raw network interface, such as "eth0" *--* Required by upstream Task
        rate: desired rate for transmitting packets (packets per second) *--* Required by upstream Task
        target_file: specifies the file on disk containing a list of ips or domains *--* Required by upstream Task
    """

    threads = luigi.Parameter(default=defaults.get("threads", ""))
    scan_timeout = luigi.Parameter(default=defaults.get("aquatone-scan-timeout", ""))

    def requires(self):
        """ AquatoneScan depends on GatherWebTargets to run.

        GatherWebTargets accepts exempt_list and expects rate, target_file, interface,
                         and either ports or top_ports as parameters

        Returns:
            luigi.Task - GatherWebTargets
        """
        args = {
            "rate": self.rate,
            "target_file": self.target_file,
            "top_ports": self.top_ports,
            "interface": self.interface,
            "ports": self.ports,
            "exempt_list": self.exempt_list,
        }
        return GatherWebTargets(**args)

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output file is amass.TARGET_FILE.json.

        Returns:
            luigi.local_target.LocalTarget
        """
        return luigi.LocalTarget(f"aquatone-{self.target_file}-results")

    def run(self):
        """ Defines the options/arguments sent to aquatone after processing.

        /opt/aquatone -scan-timeout 900 -threads 20

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        Path(self.output().path).mkdir(parents=True, exist_ok=True)

        command = [
            tool_paths.get("aquatone"),
            "-scan-timeout",
            self.scan_timeout,
            "-threads",
            self.threads,
            "-silent",
            "-out",
            self.output().path,
        ]

        with self.input().open() as target_list:
            subprocess.run(command, stdin=target_list)
