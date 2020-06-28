import subprocess
from pathlib import Path
from urllib.parse import urlparse

import luigi
from luigi.util import inherits
from luigi.contrib.sqla import SQLAlchemyTarget

from .targets import GatherWebTargets
from ...tools import tools
from ..helpers import get_tool_state
from ...models.endpoint_model import Endpoint

import pipeline.models.db_manager


@inherits(GatherWebTargets)
class WaybackurlsScan(luigi.Task):
    """ Fetch known URLs from the Wayback Machine, Common Crawl, and Virus Total for historic data about the target.

    Install:
        .. code-block:: console

            go get github.com/tomnomnom/waybackurls

    Basic Example:
        ``waybackurls`` commands are structured like the example below.

        ``cat domains.txt | waybackurls > urls``

    Luigi Example:
        .. code-block:: python

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.web.waybackurls WaybackurlsScan --target-file tesla --top-ports 1000

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
        self.db_mgr = pipeline.models.db_manager.DBManager(db_location=self.db_location)
        self.results_subfolder = Path(self.results_dir) / "waybackurls-results"

    @staticmethod
    def meets_requirements():
        """ Reports whether or not this scan's needed tool(s) are installed or not """
        needs = ["waybackurls"]
        tools = get_tool_state()

        if tools:
            return all([tools.get(x).get("installed") is True for x in needs])

    def requires(self):
        """ WaybackurlsScan depends on GatherWebTargets to run.

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
            connection_string=self.db_mgr.connection_string, target_table="endpoint", update_id=self.task_id
        )

    def run(self):
        """ Defines the options/arguments sent to waybackurls after processing. """
        self.results_subfolder.mkdir(parents=True, exist_ok=True)

        command = [tools.get("waybackurls").get("path")]

        waybackurls_input_file = self.results_subfolder / "input-from-webtargets"

        with open(waybackurls_input_file, "w") as f:
            for target in self.db_mgr.get_all_hostnames():
                f.write(f"{target}\n")

        with open(waybackurls_input_file) as target_list:
            proc = subprocess.run(command, stdin=target_list, stdout=subprocess.PIPE)

        for url in proc.stdout.decode().splitlines():
            if not url:
                continue

            parsed_url = urlparse(url)

            # get Target, may exist already or not
            ip_or_hostname = parsed_url.hostname
            tgt = self.db_mgr.get_or_create_target_by_ip_or_hostname(ip_or_hostname)

            endpoint = self.db_mgr.get_or_create(Endpoint, url=url, target=tgt)

            if endpoint not in tgt.endpoints:
                tgt.endpoints.append(endpoint)

            self.db_mgr.add(tgt)
            self.db_mgr.add(endpoint)

            self.output().touch()

        waybackurls_input_file.unlink()
