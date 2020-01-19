import json
import pickle
import logging
import subprocess
from collections import defaultdict

import luigi
from luigi.util import inherits

from recon.targets import TargetList
from recon.amass import ParseAmassOutput
from recon.config import top_tcp_ports, top_udp_ports, defaults


@inherits(TargetList, ParseAmassOutput)
class MasscanScan(luigi.Task):
    """ Run masscan against a target specified via the TargetList Task.

    Masscan commands are structured like the example below.  When specified, --top_ports is processed and
    then ultimately passed to --ports.

    masscan -v --open-only --banners --rate 1000 -e tun0 -oJ masscan.tesla.json --ports 80,443,22,21 -iL tesla.ips

    The corresponding luigi command is shown below.

    PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.masscan Masscan --target-file tesla --ports 80,443,22,21

    Args:
        rate: desired rate for transmitting packets (packets per second)
        interface: use the named raw network interface, such as "eth0"
        top_ports: Scan top N most popular ports
        ports: specifies the port(s) to be scanned
        target_file: specifies the file on disk containing a list of ips or domains *--* Required by upstream Task
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *--* Optional for upstream Task
        results_dir: specifies the directory on disk to which all Task results are written *--* Optional for upstream Task
    """

    rate = luigi.Parameter(default=defaults.get("masscan-rate", ""))
    interface = luigi.Parameter(default=defaults.get("masscan-iface", ""))
    top_ports = luigi.IntParameter(default=0)  # IntParameter -> top_ports expected as int
    ports = luigi.Parameter(default="")

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output file is masscan.TARGET_FILE.json.

        Returns:
            luigi.local_target.LocalTarget
        """
        return luigi.LocalTarget(f"{self.results_dir}/masscan.{self.target_file}.json")

    def run(self):
        """ Defines the options/arguments sent to masscan after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        print(f"debug-epi: masscan {self.results_dir}")
        if self.ports and self.top_ports:
            # can't have both
            logging.error("Only --ports or --top-ports is permitted, not both.")
            exit(1)

        if not self.ports and not self.top_ports:
            # need at least one
            logging.error("Must specify either --top-ports or --ports.")
            exit(2)

        if self.top_ports < 0:
            # sanity check
            logging.error("--top-ports must be greater than 0")
            exit(3)

        if self.top_ports:
            # if --top-ports used, format the top_*_ports lists as strings and then into a proper masscan --ports option
            top_tcp_ports_str = ",".join(str(x) for x in top_tcp_ports[: self.top_ports])
            top_udp_ports_str = ",".join(str(x) for x in top_udp_ports[: self.top_ports])

            self.ports = f"{top_tcp_ports_str},U:{top_udp_ports_str}"
            self.top_ports = 0

        target_list = yield TargetList(target_file=self.target_file, results_dir=self.results_dir)

        if target_list.path.endswith("domains"):
            yield ParseAmassOutput(
                target_file=self.target_file,
                exempt_list=self.exempt_list,
                results_dir=self.results_dir,
            )

        command = [
            "masscan",
            "-v",
            "--open",
            "--banners",
            "--rate",
            self.rate,
            "-e",
            self.interface,
            "-oJ",
            self.output().path,
            "--ports",
            self.ports,
            "-iL",
            target_list.path.replace("domains", "ips"),
        ]

        subprocess.run(command)


@inherits(MasscanScan)
class ParseMasscanOutput(luigi.Task):
    """ Read masscan JSON results and create a pickled dictionary of pertinent information for processing.

    Args:
        top_ports: Scan top N most popular ports *--* Required by upstream Task
        ports: specifies the port(s) to be scanned *--* Required by upstream Task
        interface: use the named raw network interface, such as "eth0" *--* Required by upstream Task
        rate: desired rate for transmitting packets (packets per second) *--* Required by upstream Task
        target_file: specifies the file on disk containing a list of ips or domains *--* Required by upstream Task
        results_dir: specifes the directory on disk to which all Task results are written *--* Required by upstream Task
    """

    def requires(self):
        """ ParseMasscanOutput depends on Masscan to run.

        Masscan expects rate, target_file, interface, and either ports or top_ports as parameters.

        Returns:
            luigi.Task - Masscan
        """
        args = {
            "results_dir": self.results_dir,
            "rate": self.rate,
            "target_file": self.target_file,
            "top_ports": self.top_ports,
            "interface": self.interface,
            "ports": self.ports,
        }
        return MasscanScan(**args)

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output file is masscan.TARGET_FILE.parsed.pickle.

        Returns:
            luigi.local_target.LocalTarget
        """
        return luigi.LocalTarget(f"{self.results_dir}/masscan.{self.target_file}.parsed.pickle")

    def run(self):
        """ Reads masscan JSON results and creates a pickled dictionary of pertinent information for processing. """
        ip_dict = defaultdict(lambda: defaultdict(set))  # nested defaultdict

        try:
            entries = json.load(self.input().open())  # load masscan results from Masscan Task
        except json.decoder.JSONDecodeError as e:
            # return on exception; no output file created; pipeline should start again from
            # this task if restarted because we never hit pickle.dump
            return print(e)

        """
        build out ip_dictionary from the loaded JSON

        masscan JSON structure over which we're looping
        [
        {   "ip": "10.10.10.146",   "timestamp": "1567856130", "ports": [ {"port": 22, "proto": "tcp", "status": "open", "reason": "syn-ack", "ttl": 63} ] }
        ,
        {   "ip": "10.10.10.146",   "timestamp": "1567856130", "ports": [ {"port": 80, "proto": "tcp", "status": "open", "reason": "syn-ack", "ttl": 63} ] }
        ]

        ip_dictionary structure that is built out from each JSON entry
        {
            "IP_ADDRESS":
                {'udp': {"161", "5000", ... },
                ...
                i.e. {protocol: set(ports) }
        }
        """
        for entry in entries:
            single_target_ip = entry.get("ip")
            for port_entry in entry.get("ports"):
                protocol = port_entry.get("proto")
                ip_dict[single_target_ip][protocol].add(str(port_entry.get("port")))

        with open(self.output().path, "wb") as f:
            pickle.dump(dict(ip_dict), f)
