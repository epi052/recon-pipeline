import os
import logging
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

import luigi
from luigi.util import inherits
from luigi.contrib.sqla import SQLAlchemyTarget

import pipeline.models.db_manager
from ...tools import tools
from ..config import defaults
from ..helpers import meets_requirements
from .targets import GatherWebTargets
from ...models.endpoint_model import Endpoint
from ..helpers import get_ip_address_version, is_ip_address


@inherits(GatherWebTargets)
class GobusterScan(luigi.Task):
    """ Use ``gobuster`` to perform forced browsing.

    Install:
        .. code-block:: console

            go get github.com/OJ/gobuster
            git clone https://github.com/epi052/recursive-gobuster.git

    Basic Example:
        .. code-block:: console

            gobuster dir -q -e -k -t 20 -u www.tesla.com -w /usr/share/seclists/Discovery/Web-Content/common.txt -p http://127.0.0.1:8080 -o gobuster.tesla.txt -x php,html

    Luigi Example:
        .. code-block:: console

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.web.gobuster GobusterScan --target-file tesla --top-ports 1000 --interface eth0 --proxy http://127.0.0.1:8080 --extensions php,html --wordlist /usr/share/seclists/Discovery/Web-Content/common.txt --threads 20

    Args:
        threads: number of threads for parallel gobuster command execution
        wordlist: wordlist used for forced browsing
        extensions: additional extensions to apply to each item in the wordlist
        recursive: whether or not to recursively gobust the target (may produce a LOT of traffic... quickly)
        proxy: protocol://ip:port proxy specification for gobuster
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *Optional by upstream Task*
        db_location: specifies the path to the database used for storing results *Required by upstream Task*
        top_ports: Scan top N most popular ports *Required by upstream Task*
        ports: specifies the port(s) to be scanned *Required by upstream Task*
        interface: use the named raw network interface, such as "eth0" *Required by upstream Task*
        rate: desired rate for transmitting packets (packets per second) *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

    recursive = luigi.BoolParameter(default=False)
    proxy = luigi.Parameter(default=defaults.get("proxy"))
    threads = luigi.Parameter(default=defaults.get("threads"))
    wordlist = luigi.Parameter(default=defaults.get("gobuster-wordlist"))
    extensions = luigi.Parameter(default=defaults.get("gobuster-extensions"))
    requirements = ["recursive-gobuster", "gobuster"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        meets_requirements(self.requirements, False)
        self.db_mgr = pipeline.models.db_manager.DBManager(db_location=self.db_location)
        self.results_subfolder = Path(self.results_dir) / "gobuster-results"

    def requires(self):
        """ GobusterScan depends on GatherWebTargets to run.

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

        If recursion is disabled, the naming convention for the output file is gobuster.TARGET_FILE.txt
        Otherwise the output file is recursive-gobuster_TARGET_FILE.log

        Results are stored in their own directory: gobuster-TARGET_FILE-results

        Returns:
            luigi.local_target.LocalTarget
        """
        return SQLAlchemyTarget(
            connection_string=self.db_mgr.connection_string, target_table="endpoint", update_id=self.task_id
        )

    def parse_results(self):
        """ Reads in each individual gobuster file and adds each line to the database as an Endpoint """
        for file in self.results_subfolder.iterdir():
            tgt = None
            for i, line in enumerate(file.read_text().splitlines()):
                url, status = line.split(maxsplit=1)  # http://somewhere/path (Status:200)

                if i == 0:
                    # parse first entry to determine ip address -> target relationship
                    parsed_url = urlparse(url)

                    tgt = self.db_mgr.get_or_create_target_by_ip_or_hostname(parsed_url.hostname)

                if tgt is not None:
                    status_code = status.split(maxsplit=1)[1]
                    ep = self.db_mgr.get_or_create(Endpoint, url=url, status_code=status_code.replace(")", ""))
                    if ep not in tgt.endpoints:
                        tgt.endpoints.append(ep)
                    self.db_mgr.add(tgt)
                    self.output().touch()

    def run(self):
        """ Defines the options/arguments sent to gobuster after processing.

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
                if self.recursive:
                    command = [
                        tools.get("recursive-gobuster").get("path"),
                        "-s",
                        "-w",
                        self.wordlist,
                        f"{url_scheme}{target}",
                    ]
                else:
                    command = [
                        tools.get("gobuster").get("path"),
                        "dir",
                        "-q",
                        "-e",
                        "-k",
                        "-u",
                        f"{url_scheme}{target}",
                        "-w",
                        self.wordlist,
                        "-o",
                        self.results_subfolder.joinpath(
                            f"gobuster.{url_scheme.replace('//', '_').replace(':', '')}{target}.txt"
                        ),
                    ]

                if self.extensions:
                    command.extend(["-x", self.extensions])

                if self.proxy:
                    command.extend(["-p", self.proxy])

                commands.append(command)

        self.results_subfolder.mkdir(parents=True, exist_ok=True)

        if self.recursive:
            # workaround for recursive gobuster not accepting output directory
            cwd = Path().cwd()
            os.chdir(self.results_subfolder)

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            executor.map(subprocess.run, commands)

        if self.recursive:
            os.chdir(str(cwd))

        self.parse_results()
