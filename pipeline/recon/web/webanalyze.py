import os
import csv
import logging
import ipaddress
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

import luigi
from luigi.util import inherits

from .targets import GatherWebTargets
from ..config import tool_paths, defaults
from ...luigi_targets import SQLiteTarget
from ...models import DBManager, Technology


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

    threads = luigi.Parameter(default=defaults.get("threads", ""))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = DBManager(db_location=self.db_location)
        self.highest_id = self.db_mgr.get_highest_id(table=Technology)
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

        The naming convention for the output file is webanalyze.TARGET_FILE.txt

        Results are stored in their own directory: webanalyze-TARGET_FILE-results

        Returns:
            luigi.local_target.LocalTarget
        """
        return SQLiteTarget(table=Technology, db_location=self.db_location, index=self.highest_id)

    def parse_results(self):
        """ Reads in the webanalyze's .csv files and updates the associated Target record. """

        for entry in Path(self.results_subfolder).glob("webanalyze*.csv"):
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
                    to_query = parsed_url.netloc

                    if parsed_url.port is not None:
                        # need to query database by ip/hostname only, port throws it off
                        to_query = parsed_url.netloc.rstrip(f":{parsed_url.port}")

                    if to_query.startswith("[") and to_query.endswith("]"):
                        # ipv6 address structed for web urls, need to remove the brackets
                        to_query = to_query.lstrip("[").rstrip("]")

                    text = f"{app}-{version}" if version else app

                    technology = self.db_mgr.get_or_create(Technology, type=category, text=text)

                    if tgt is None:
                        # should only hit the first line of each file
                        try:
                            ipaddress.ip_interface(to_query)
                            tgt = self.db_mgr.get_target_by_ip(to_query)
                        except ValueError:
                            tgt = self.db_mgr.get_target_by_hostname(to_query)

                    tgt.technologies.append(technology)

                if tgt is not None:
                    self.db_mgr.add(tgt)

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
        except TypeError:
            return logging.error("The value supplied to --threads must be a non-negative integer.")

        commands = list()

        with self.input().open() as f:
            for target in f:
                target = target.strip()

                try:
                    if isinstance(ipaddress.ip_address(target), ipaddress.IPv6Address):  # ipv6
                        target = f"[{target}]"
                except ValueError:
                    # domain names raise ValueErrors, just assume we have a domain and keep on keepin on
                    pass

                for url_scheme in ("https://", "http://"):
                    command = [tool_paths.get("webanalyze"), "-host", f"{url_scheme}{target}", "-output", "csv"]
                    commands.append(command)

        Path(self.results_subfolder).mkdir(parents=True, exist_ok=True)

        cwd = Path().cwd()
        os.chdir(self.results_subfolder)

        if not Path("apps.json").exists():
            subprocess.run(f"{tool_paths.get('webanalyze')} -update".split())

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            executor.map(self._wrapped_subprocess, commands)

        os.chdir(str(cwd))

        self.parse_results()
