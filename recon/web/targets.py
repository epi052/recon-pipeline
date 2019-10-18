import pickle

import luigi
from luigi.util import inherits

from recon.config import web_ports
from recon.amass import ParseAmassOutput
from recon.masscan import ParseMasscanOutput


@inherits(ParseMasscanOutput, ParseAmassOutput)
class GatherWebTargets(luigi.Task):
    """ Gather all subdomains as well as any ip addresses known to have a configured web port open.

    Args:
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *--* Optional for upstream Task
        top_ports: Scan top N most popular ports *--* Required by upstream Task
        ports: specifies the port(s) to be scanned *--* Required by upstream Task
        interface: use the named raw network interface, such as "eth0" *--* Required by upstream Task
        rate: desired rate for transmitting packets (packets per second) *--* Required by upstream Task
        target_file: specifies the file on disk containing a list of ips or domains *--* Required by upstream Task
    """

    def requires(self):
        """ GatherWebTargets depends on ParseMasscanOutput and ParseAmassOutput to run.

        ParseMasscanOutput expects rate, target_file, interface, and either ports or top_ports as parameters.
        ParseAmassOutput accepts exempt_list and expects target_file

        Returns:
            dict(str: ParseMasscanOutput, str: ParseAmassOutput)
        """
        args = {
            "rate": self.rate,
            "target_file": self.target_file,
            "top_ports": self.top_ports,
            "interface": self.interface,
            "ports": self.ports,
        }
        return {
            "masscan-output": ParseMasscanOutput(**args),
            "amass-output": ParseAmassOutput(
                exempt_list=self.exempt_list, target_file=self.target_file
            ),
        }

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output file is webtargets.TARGET_FILE.txt.

        Returns:
            luigi.local_target.LocalTarget
        """
        return luigi.LocalTarget(f"webtargets.{self.target_file}.txt")

    def run(self):
        """ Gather all potential web targets into a single file to pass farther down the pipeline. """
        targets = set()

        ip_dict = pickle.load(open(self.input().get("masscan-output").path, "rb"))

        for target, protocol_dict in ip_dict.items():
            for protocol, ports in protocol_dict.items():
                if ports.intersection(web_ports):  # found a web port from masscan's results
                    targets.add(target)

        for amass_result in self.input().get("amass-output").values():
            with amass_result.open() as f:
                for target in f:
                    # we care about all results returned from amass
                    targets.add(target.strip())

        with self.output().open("w") as f:
            for target in targets:
                f.write(f"{target}\n")
