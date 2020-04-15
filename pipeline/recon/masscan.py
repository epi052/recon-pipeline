import json
import logging
import subprocess
from pathlib import Path

import luigi
from luigi.util import inherits
from luigi.contrib.sqla import SQLAlchemyTarget

import pipeline.models.db_manager
from .targets import TargetList
from .amass import ParseAmassOutput
from ..models.port_model import Port
from ..models.ip_address_model import IPAddress

from .config import top_tcp_ports, top_udp_ports, defaults, tool_paths, web_ports


@inherits(TargetList, ParseAmassOutput)
class MasscanScan(luigi.Task):
    """ Run ``masscan`` against a target specified via the TargetList Task.

    Note:
        When specified, ``--top_ports`` is processed and then ultimately passed to ``--ports``.

    Install:
        .. code-block:: console

            git clone https://github.com/robertdavidgraham/masscan /tmp/masscan
            make -s -j -C /tmp/masscan
            sudo mv /tmp/masscan/bin/masscan /usr/local/bin/masscan
            rm -rf /tmp/masscan

    Basic Example:
        .. code-block:: console

            masscan -v --open-only --banners --rate 1000 -e tun0 -oJ masscan.tesla.json --ports 80,443,22,21 -iL tesla.ips

    Luigi Example:
        .. code-block:: console

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.masscan Masscan --target-file tesla --ports 80,443,22,21

    Args:
        rate: desired rate for transmitting packets (packets per second)
        interface: use the named raw network interface, such as "eth0"
        top_ports: Scan top N most popular ports
        ports: specifies the port(s) to be scanned
        db_location: specifies the path to the database used for storing results *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *Optional by upstream Task*
    """

    rate = luigi.Parameter(default=defaults.get("masscan-rate"))
    interface = luigi.Parameter(default=defaults.get("masscan-iface"))
    top_ports = luigi.IntParameter(default=0)  # IntParameter -> top_ports expected as int
    ports = luigi.Parameter(default="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = pipeline.models.db_manager.DBManager(db_location=self.db_location)
        self.results_subfolder = (Path(self.results_dir) / "masscan-results").expanduser().resolve()

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output file is masscan.TARGET_FILE.json.

        Returns:
            luigi.local_target.LocalTarget
        """
        new_path = self.results_subfolder / "masscan.json"

        return luigi.LocalTarget(new_path.expanduser().resolve())

    def run(self):
        """ Defines the options/arguments sent to masscan after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        if not self.ports and not self.top_ports:
            # need at least one, can't be put into argparse scanner because things like amass don't require ports option
            logging.error("Must specify either --top-ports or --ports.")
            exit(2)

        if self.top_ports:
            # if --top-ports used, format the top_*_ports lists as strings and then into a proper masscan --ports option
            top_tcp_ports_str = ",".join(str(x) for x in top_tcp_ports[: self.top_ports])
            top_udp_ports_str = ",".join(str(x) for x in top_udp_ports[: self.top_ports])

            self.ports = f"{top_tcp_ports_str},U:{top_udp_ports_str}"
            self.top_ports = 0

        self.results_subfolder.mkdir(parents=True, exist_ok=True)

        yield TargetList(target_file=self.target_file, results_dir=self.results_dir, db_location=self.db_location)

        if self.db_mgr.get_all_hostnames():
            # TargetList generated some domains for us to scan with amass

            yield ParseAmassOutput(
                target_file=self.target_file,
                exempt_list=self.exempt_list,
                results_dir=self.results_dir,
                db_location=self.db_location,
            )

        command = [
            tool_paths.get("masscan"),
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
        ]

        # masscan only understands how to scan ipv4
        ip_addresses = self.db_mgr.get_all_ipv4_addresses()
        masscan_input_file = None

        if ip_addresses:
            # TargetList generated ip addresses for us to scan with masscan
            masscan_input_file = self.results_subfolder / "input-from-amass"

            with open(masscan_input_file, "w") as f:
                for ip_address in ip_addresses:
                    f.write(f"{ip_address}\n")

            command.append(str(masscan_input_file))

        subprocess.run(command)  # will fail if no ipv4 addresses were found

        if masscan_input_file is not None:
            masscan_input_file.unlink()


@inherits(MasscanScan)
class ParseMasscanOutput(luigi.Task):
    """ Read masscan JSON results and create a pickled dictionary of pertinent information for processing.

    Args:
        top_ports: Scan top N most popular ports *Required by upstream Task*
        ports: specifies the port(s) to be scanned *Required by upstream Task*
        interface: use the named raw network interface, such as "eth0" *Required by upstream Task*
        rate: desired rate for transmitting packets (packets per second) *Required by upstream Task*
        db_location: specifies the path to the database used for storing results *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = pipeline.models.db_manager.DBManager(db_location=self.db_location)
        self.results_subfolder = (Path(self.results_dir) / "masscan-results").expanduser().resolve()

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
            "db_location": self.db_location,
        }
        return MasscanScan(**args)

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output file is masscan.TARGET_FILE.parsed.pickle.

        Returns:
            luigi.local_target.LocalTarget
        """
        return SQLAlchemyTarget(
            connection_string=self.db_mgr.connection_string, target_table="port", update_id=self.task_id
        )

    def run(self):
        """ Reads masscan JSON results and creates a pickled dictionary of pertinent information for processing. """
        try:
            # load masscan results from Masscan Task
            entries = json.load(self.input().open())
        except json.decoder.JSONDecodeError as e:
            # return on exception; no output file created; pipeline should start again from
            # this task if restarted because we never hit pickle.dump
            return print(e)

        self.results_subfolder.mkdir(parents=True, exist_ok=True)

        """
        populate database from the loaded JSON

        masscan JSON structure over which we're looping
        [
        {   "ip": "10.10.10.146",   "timestamp": "1567856130", "ports": [ {"port": 22, "proto": "tcp", "status": "open", "reason": "syn-ack", "ttl": 63} ] }
        ,
        {   "ip": "10.10.10.146",   "timestamp": "1567856130", "ports": [ {"port": 80, "proto": "tcp", "status": "open", "reason": "syn-ack", "ttl": 63} ] }
        ]
        """

        for entry in entries:
            single_target_ip = entry.get("ip")

            tgt = self.db_mgr.get_or_create_target_by_ip_or_hostname(single_target_ip)

            if single_target_ip not in tgt.ip_addresses:
                tgt.ip_addresses.append(self.db_mgr.get_or_create(IPAddress, ipv4_address=single_target_ip))

            for port_entry in entry.get("ports"):
                protocol = port_entry.get("proto")

                port = self.db_mgr.get_or_create(Port, protocol=protocol, port_number=port_entry.get("port"))

                if str(port.port_number) in web_ports:
                    tgt.is_web = True

                tgt.open_ports.append(port)

            self.db_mgr.add(tgt)
            self.output().touch()

        self.db_mgr.close()
