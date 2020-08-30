import json
import logging
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import luigi
from luigi.util import inherits
from luigi.contrib.sqla import SQLAlchemyTarget

from ...tools import tools
from ..config import defaults
from .targets import GatherWebTargets
from ..helpers import meets_requirements
from ...models.technology_model import Technology

import pipeline.models.db_manager


@inherits(GatherWebTargets)
class NucleiScan(luigi.Task):
    """ Scan a given target using Nuclei's scanning templates

    Install:
        .. code-block:: console

            go get -u github.com/projectdiscovery/nuclei/v2/cmd/nuclei

    Basic Example:
        ``nuclei`` commands are structured like the example below.

        ``nuclei -t /PATH/TO/nuclei-templates/cves -l TARGETS -silent -json``

    Luigi Example:
        .. code-block:: python

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.web.nuclei NucleiScan --target-file tesla --top-ports 1000

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

    requirements = ["go", "nuclei", "masscan"]
    exception = True
    threads = luigi.Parameter(default=defaults.get("threads"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = pipeline.models.db_manager.DBManager(db_location=self.db_location)
        self.results_subfolder = Path(self.results_dir) / "nuclei-results"

    def requires(self):
        """ NucleiScan depends on GatherWebTargets to run.

        GatherWebTargets accepts exempt_list and expects rate, target_file, interface,
                         and either ports or top_ports as parameters

        Returns:
            luigi.Task - GatherWebTargets
        """
        meets_requirements(self.requirements, self.exception)
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
        return {
            "sqltarget": SQLAlchemyTarget(
                connection_string=self.db_mgr.connection_string, target_table="technology", update_id=self.task_id
            ),
            "localtarget": luigi.LocalTarget(str(self.results_subfolder / "nuclei-results.json")),
        }

    def run(self):
        """ Defines the options/arguments sent to nuclei after processing. """
        self.results_subfolder.mkdir(parents=True, exist_ok=True)

        try:
            self.threads = abs(int(self.threads))
        except (TypeError, ValueError):
            return logging.error("The value supplied to --threads must be a non-negative integer.")

        scans = [
            "panels",
            # "subdomain-takeover",
            # "tokens",
            # "security-misconfiguration",
            # "default-credentials",
            # "dns",
            # "cves",
            # "vulnerabilities",
            "technologies",
            # "files",
            # "workflows",
            # "generic-detections",
        ]

        input_file = self.results_subfolder / "input-from-webtargets"

        with open(input_file, "w") as f:
            for target in self.db_mgr.get_all_hostnames():
                for url_scheme in ("https://", "http://"):
                    f.write(f"{url_scheme}{target}\n")

        command = [
            tools.get("nuclei").get("path"),
            "-silent",
            "-json",
            "-c",
            str(self.threads),
            "-l",
            str(input_file),
            "-o",
            self.output().get("localtarget").path,
        ]

        for scan in scans:
            path = Path(defaults.get("tools-dir")) / "nuclei-templates" / scan
            command.append("-t")
            command.append(path)

        subprocess.run(command)

        input_file.unlink()

        self.parse_output()

    def parse_output(self):
        """ Read nuclei .json results and add entries into specified database """
        """ example data
        
        {"template":"tech-detect","type":"http","matched":"https://staging.bitdiscovery.com/","matcher_name":"jsdelivr","severity":"info","author":"hakluke","description":""}
        {"template":"swagger-panel","type":"http","matched":"https://staging.bitdiscovery.com/api/swagger.yaml","severity":"info","author":"Ice3man","description":""}
        """
        tgt = None

        with self.output().get("localtarget").open() as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue

                parsed_url = urlparse(entry.get("matched"))

                if tgt is None:
                    # should only hit the first line of each file
                    tgt = self.db_mgr.get_or_create_target_by_ip_or_hostname(parsed_url.hostname)

                if entry.get("template") == "tech-detect":
                    technology = self.db_mgr.get_or_create(
                        Technology, type=entry.get("type"), text=entry.get("matcher_name")
                    )
                    if technology not in tgt.technologies:
                        tgt.technologies.append(technology)

            # if tgt is not None:
            #     self.db_mgr.add(tgt)
            #     self.output().get("sqltarget").touch()
        #
        # self.db_mgr.close()
