from pathlib import Path

import luigi
from luigi.util import inherits
from luigi.contrib.external_program import ExternalProgramTask

from recon.config import tool_paths, defaults
from recon.web.targets import GatherWebTargets


@inherits(GatherWebTargets)
class CORScannerScan(ExternalProgramTask):
    """ Use ``CORScanner`` to scan for potential CORS misconfigurations.

    Install:
        .. code-block:: console

            git clone https://github.com/chenjj/CORScanner.git
            cd CORScanner
            pip install -r requirements.txt
            pip install future

    Basic Example:
        .. code-block:: console

            python cors_scan.py -i webtargets.tesla.txt -t 100

    Luigi Example:
        .. code-block:: console

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.web.corscanner CORScannerScan --target-file tesla --top-ports 1000 --interface eth0

    Args:
        threads: number of threads for parallel subjack command execution
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
        """ CORScannerScan depends on GatherWebTargets to run.

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
        }
        return GatherWebTargets(**args)

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output file is corscanner.TARGET_FILE.json.

        Returns:
            luigi.local_target.LocalTarget
        """
        results_subfolder = Path(self.results_dir) / "corscanner-results"

        new_path = results_subfolder / "corscanner.json"

        return luigi.LocalTarget(new_path.resolve())

    def program_args(self):
        """ Defines the options/arguments sent to tko-subs after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        Path(self.output().path).parent.mkdir(parents=True, exist_ok=True)

        command = [
            "python3",
            tool_paths.get("CORScanner"),
            "-i",
            self.input().path,
            "-t",
            self.threads,
            "-o",
            self.output().path,
        ]

        return command
