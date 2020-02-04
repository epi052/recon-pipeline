import json
import ipaddress
from pathlib import Path

import luigi
from luigi.util import inherits
from luigi.contrib.external_program import ExternalProgramTask

from recon.targets import TargetList


@inherits(TargetList)
class AmassScan(ExternalProgramTask):
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
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

    exempt_list = luigi.Parameter(default="")

    def requires(self):
        """ AmassScan depends on TargetList to run.

        TargetList expects target_file as a parameter.

        Returns:
            luigi.ExternalTask - TargetList
        """
        args = {"target_file": self.target_file, "results_dir": self.results_dir}
        return TargetList(**args)

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output file is amass.json.

        Returns:
            luigi.local_target.LocalTarget
        """
        results_subfolder = Path(self.results_dir) / "amass-results"

        new_path = results_subfolder / "amass.json"

        return luigi.LocalTarget(new_path.resolve())

    def program_args(self):
        """ Defines the options/arguments sent to amass after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """

        Path(self.output().path).parent.mkdir(parents=True, exist_ok=True)

        if not self.input().path.endswith("domains"):
            return f"touch {self.output().path}".split()

        command = [
            "amass",
            "enum",
            "-active",
            "-ip",
            "-brute",
            "-min-for-recursive",
            "3",
            "-df",
            self.input().path,
            "-json",
            self.output().path,
        ]

        if self.exempt_list:
            command.append("-blf")  # Path to a file providing blacklisted subdomains
            command.append(self.exempt_list)

        return command


@inherits(AmassScan)
class ParseAmassOutput(luigi.Task):
    """ Read amass JSON results and create categorized entries into ip|subdomain files.

    Args:
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *Optional by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

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
        }
        return AmassScan(**args)

    def output(self):
        """ Returns the target output files for this task.

        Naming conventions for the output files are:
            TARGET_FILE.ips
            TARGET_FILE.ip6s
            TARGET_FILE.subdomains

        Returns:
            dict(str: luigi.local_target.LocalTarget)
        """
        results_subfolder = Path(self.results_dir) / "target-results"

        ips = (results_subfolder / "ipv4_addresses").resolve()
        ip6s = ips.with_name("ipv6_addresses").resolve()
        subdomains = ips.with_name("subdomains").resolve()

        return {
            "target-ips": luigi.LocalTarget(ips),
            "target-ip6s": luigi.LocalTarget(ip6s),
            "target-subdomains": luigi.LocalTarget(subdomains),
        }

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
        unique_ips = set()
        unique_ip6s = set()
        unique_subs = set()

        Path(self.output().get("target-ips").path).parent.mkdir(parents=True, exist_ok=True)

        amass_json = self.input().open()
        ip_file = self.output().get("target-ips").open("w")
        ip6_file = self.output().get("target-ip6s").open("w")
        subdomain_file = self.output().get("target-subdomains").open("w")

        with amass_json as aj, ip_file as ip_out, ip6_file as ip6_out, subdomain_file as subdomain_out:
            for line in aj:
                entry = json.loads(line)
                unique_subs.add(entry.get("name"))

                for address in entry.get("addresses"):
                    ipaddr = address.get("ip")
                    if isinstance(ipaddress.ip_address(ipaddr), ipaddress.IPv4Address):  # ipv4 addr
                        unique_ips.add(ipaddr)
                    elif isinstance(ipaddress.ip_address(ipaddr), ipaddress.IPv6Address):  # ipv6
                        unique_ip6s.add(ipaddr)

            # send gathered results to their appropriate destination
            for ip in unique_ips:
                print(ip, file=ip_out)

            for sub in unique_subs:
                print(sub, file=subdomain_out)

            for ip6 in unique_ip6s:
                print(ip6, file=ip6_out)
