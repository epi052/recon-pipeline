import json
import subprocess
from pathlib import Path

import luigi
from luigi.util import inherits
from luigi.contrib.sqla import SQLAlchemyTarget

import pipeline.models.db_manager
from ..tools import tools
from .targets import TargetList
from .helpers import meets_requirements
from ..models.target_model import Target


@inherits(TargetList)
class AmassScan(luigi.Task):
    """ Run ``amass`` scan to perform subdomain enumeration of given domain(s).

    Note:
        Expects **TARGET_FILE.domains** file to be a text file with one top-level domain per line.

    Install:
        .. code-block:: console

            sudo apt-get install -y -q amass

    Basic Example:
        .. code-block:: console

            amass enum -ip -brute -active -min-for-recursive 3 -df tesla -json amass.tesla.json

    Luigi Example:
        .. code-block:: console

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.amass AmassScan --target-file tesla

    Args:
        exempt_list: Path to a file providing blacklisted subdomains, one per line.
        db_location: specifies the path to the database used for storing results *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

    exempt_list = luigi.Parameter(default="")
    requirements = ["go", "amass"]
    exception = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = pipeline.models.db_manager.DBManager(db_location=self.db_location)
        self.results_subfolder = (Path(self.results_dir) / "amass-results").expanduser().resolve()

    def requires(self):
        """ AmassScan depends on TargetList to run.

        TargetList expects target_file as a parameter.

        Returns:
            luigi.ExternalTask - TargetList
        """
        meets_requirements(self.requirements, self.exception)
        args = {"target_file": self.target_file, "results_dir": self.results_dir, "db_location": self.db_location}
        return TargetList(**args)

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output file is amass.json.

        Returns:
            luigi.local_target.LocalTarget
        """
        results_subfolder = Path(self.results_dir) / "amass-results"

        new_path = results_subfolder / "amass.json"

        return luigi.LocalTarget(new_path.expanduser().resolve())

    def run(self):
        """ Defines the options/arguments sent to amass after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        self.results_subfolder.mkdir(parents=True, exist_ok=True)

        hostnames = self.db_mgr.get_all_hostnames()

        if hostnames:
            # TargetList generated some domains for us to scan with amass
            amass_input_file = self.results_subfolder / "input-from-targetlist"
            with open(amass_input_file, "w") as f:
                for hostname in hostnames:
                    f.write(f"{hostname}\n")
        else:
            return subprocess.run(f"touch {self.output().path}".split())

        command = [
            tools.get("amass").get("path"),
            "enum",
            "-active",
            "-ip",
            "-brute",
            "-min-for-recursive",
            "3",
            "-df",
            str(amass_input_file),
            "-json",
            self.output().path,
        ]

        if self.exempt_list:
            command.append("-blf")  # Path to a file providing blacklisted subdomains
            command.append(self.exempt_list)

        subprocess.run(command)

        amass_input_file.unlink()


@inherits(AmassScan)
class ParseAmassOutput(luigi.Task):
    """ Read amass JSON results and create categorized entries into ip|subdomain files.

    Args:
        db_location: specifies the path to the database used for storing results *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *Optional by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = pipeline.models.db_manager.DBManager(db_location=self.db_location)
        self.results_subfolder = (Path(self.results_dir) / "amass-results").expanduser().resolve()

    def requires(self):
        """ ParseAmassOutput depends on AmassScan to run.

        TargetList expects target_file as a parameter.
        AmassScan accepts exempt_list as an optional parameter.

        Returns:
            luigi.ExternalTask - TargetList
        """

        args = {
            "target_file": self.target_file,
            "exempt_list": self.exempt_list,
            "results_dir": self.results_dir,
            "db_location": self.db_location,
        }
        return AmassScan(**args)

    def output(self):
        """ Returns the target output files for this task.

        Returns:
            luigi.contrib.sqla.SQLAlchemyTarget
        """
        return SQLAlchemyTarget(
            connection_string=self.db_mgr.connection_string, target_table="target", update_id=self.task_id
        )

    def run(self):
        """ Parse the json file produced by AmassScan and categorize the results into ip|subdomain files.

        An example (prettified) entry from the json file is shown below
            {
              "Timestamp": "2019-09-22T19:20:13-05:00",
              "name": "beta-partners.tesla.com",
              "domain": "tesla.com",
              "addresses": [
                {
                  "ip": "209.133.79.58",
                  "cidr": "209.133.79.0/24",
                  "asn": 394161,
                  "desc": "TESLA - Tesla"
                }
              ],
              "tag": "ext",
              "source": "Previous Enum"
            }
        """
        self.results_subfolder.mkdir(parents=True, exist_ok=True)

        if Path(self.input().path).stat().st_size == 0:
            self.output().touch()
            return

        amass_json = self.input().open()

        with amass_json as amass_json_file:
            for line in amass_json_file:
                entry = json.loads(line)

                tgt = self.db_mgr.get_or_create(Target, hostname=entry.get("name"), is_web=True)

                for address in entry.get("addresses"):
                    ipaddr = address.get("ip")

                    tgt = self.db_mgr.add_ipv4_or_v6_address_to_target(tgt, ipaddr)

                self.db_mgr.add(tgt)
                self.output().touch()

            self.db_mgr.close()
