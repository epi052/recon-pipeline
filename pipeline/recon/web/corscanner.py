import subprocess
from pathlib import Path

import luigi
from luigi.util import inherits

from .targets import GatherWebTargets
from ..config import tool_paths, defaults
from ...models.db_manager import DBManager


@inherits(GatherWebTargets)
class CORScannerScan(luigi.Task):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = DBManager(db_location=self.db_location)
        self.results_subfolder = (Path(self.results_dir) / "corscanner-results").resolve()

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
            "db_location": self.db_location,
        }
        return GatherWebTargets(**args)

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output file is corscanner.TARGET_FILE.json.

        Returns:
            luigi.local_target.LocalTarget
        """
        # TODO:  cut over to the database once actual CORScanner results come up during a scan
        #        https://github.com/epi052/recon-pipeline/projects/1#card-32050846
        # return SQLAlchemyTarget(
        #     connection_string=self.db_mgr.connection_string, target_table="target", update_id=self.task_id
        # )
        return luigi.LocalTarget((self.results_subfolder / "corscanner.json").resolve())

    def run(self):
        """ Defines the options/arguments sent to tko-subs after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        self.results_subfolder.mkdir(parents=True, exist_ok=True)

        targets = self.db_mgr.get_all_web_targets()

        if not targets:
            return

        corscanner_input_file = self.results_subfolder / "input-from-webtargets"
        with open(corscanner_input_file, "w") as f:
            for target in targets:
                f.write(f"{targets}\n")

        command = [
            "python3",
            tool_paths.get("CORScanner"),
            "-i",
            str(corscanner_input_file),
            "-t",
            self.threads,
            "-o",
            self.output().path,
        ]

        subprocess.run(command)

        corscanner_input_file.unlink()
