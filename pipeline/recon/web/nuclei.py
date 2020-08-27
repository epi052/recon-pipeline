import subprocess
from pathlib import Path
from urllib.parse import urlparse

import luigi
from luigi.util import inherits
from luigi.contrib.sqla import SQLAlchemyTarget

from .targets import GatherWebTargets
from ...tools import tools
from ..helpers import meets_requirements
from ...models.endpoint_model import Endpoint

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
        raise NotImplementedError

    def run(self):
        """ Defines the options/arguments sent to nuclei after processing. """
        self.results_subfolder.mkdir(parents=True, exist_ok=True)
        raise NotImplementedError

    def parse_output(self):
        """ Read nuclei .json results and add entries into specified database """
        raise NotImplementedError
