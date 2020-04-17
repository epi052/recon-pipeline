import os
import csv
import logging
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

import luigi
from luigi.util import inherits
from luigi.contrib.sqla import SQLAlchemyTarget

import pipeline.models.db_manager
from .targets import GatherWebTargets
from ..config import tool_paths, defaults
from ...models.technology_model import Technology
from ..helpers import get_ip_address_version, is_ip_address


@inherits(GatherWebTargets)
class WebanalyzeScan(luigi.Task):
    """ Use webanalyze to determine the technology stack on the given target(s).

    Install:
        .. code-block:: console

            go get -u github.com/rverton/webanalyze

            # loads new apps.json file from wappalyzer project
            webanalyze -update

    Basic Example:
        .. code-block:: console

            webanalyze -host www.tesla.com -output json

    Luigi Example:
        .. code-block:: console

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.web.webanalyze WebanalyzeScan --target-file tesla --top-ports 1000 --interface eth0

    Args:
        threads: number of threads for parallel webanalyze command execution
        db_location: specifies the path to the database used for storing results *Required by upstream Task*
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *Optional for upstream Task*
        top_ports: Scan top N most popular ports *Required by upstream Task*
        ports: specifies the port(s) to be scanned  *Required by upstream Task*
        interface: use the named raw network interface, such as "eth0" *Required by upstream Task*
        rate: desired rate for transmitting packets (packets per second) *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

    threads = luigi.Parameter(default=defaults.get("threads"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = pipeline.models.db_manager.DBManager(db_location=self.db_location)
        self.results_subfolder = Path(self.results_dir) / "webanalyze-results"

    def requires(self):
        """ WebanalyzeScan depends on GatherWebTargets to run.

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
            connection_string=self.db_mgr.connection_string, target_table="technology", update_id=self.task_id
        )

    def parse_results(self):
        """ Reads in the webanalyze's .csv files and updates the associated Target record. """

        for entry in self.results_subfolder.glob("webanalyze*.csv"):
            """ example data

                http://13.57.162.100,Font scripts,Google Font API,
                http://13.57.162.100,"Web servers,Reverse proxies",Nginx,1.16.1
                http://13.57.162.100,Font scripts,Font Awesome,
            """
            with open(entry, newline="") as f:
                reader = csv.reader(f)

                # skip the empty line at the start; webanalyze places an empty line at the top of the file
                # need to skip that.  remove this line if the files have no empty lines at the top
                next(reader, None)
                next(reader, None)  # skip the headers; keep this one forever and always

                tgt = None

                for row in reader:
                    # each row in a file is a technology specific to that target
                    host, category, app, version = row

                    parsed_url = urlparse(host)

                    text = f"{app}-{version}" if version else app

                    technology = self.db_mgr.get_or_create(Technology, type=category, text=text)

                    if tgt is None:
                        # should only hit the first line of each file
                        tgt = self.db_mgr.get_or_create_target_by_ip_or_hostname(parsed_url.hostname)

                    tgt.technologies.append(technology)

                if tgt is not None:
                    self.db_mgr.add(tgt)
                    self.output().touch()

        self.db_mgr.close()

    def _wrapped_subprocess(self, cmd):
        with open(f"webanalyze-{cmd[2].replace('//', '_').replace(':', '')}.csv", "wb") as f:
            subprocess.run(cmd, stdout=f)

    def run(self):
        """ Defines the options/arguments sent to webanalyze after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        try:
            self.threads = abs(int(self.threads))
        except (TypeError, ValueError):
            return logging.error("The value supplied to --threads must be a non-negative integer.")

        commands = list()

        for target in self.db_mgr.get_all_web_targets():
            if is_ip_address(target) and get_ip_address_version(target) == "6":
                target = f"[{target}]"

            for url_scheme in ("https://", "http://"):
                command = [tool_paths.get("webanalyze"), "-host", f"{url_scheme}{target}", "-output", "csv"]
                commands.append(command)

        self.results_subfolder.mkdir(parents=True, exist_ok=True)

        cwd = Path().cwd()
        os.chdir(self.results_subfolder)

        if not Path("apps.json").exists():
            subprocess.run(f"{tool_paths.get('webanalyze')} -update".split())

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            executor.map(self._wrapped_subprocess, commands)

        os.chdir(str(cwd))

        self.parse_results()
