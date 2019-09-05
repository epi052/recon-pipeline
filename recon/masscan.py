import logging

import luigi
from luigi.util import inherits
from luigi.contrib.external_program import ExternalProgramTask

from recon.targets import TargetList
from recon.config import top_tcp_ports, top_udp_ports, masscan_config


@inherits(TargetList)
class Masscan(ExternalProgramTask):
    rate = luigi.Parameter(default=masscan_config.get("rate"))
    interface = luigi.Parameter(default=masscan_config.get("iface"))
    top_ports = luigi.IntParameter(default=0)  # IntParameter -> top_ports expected as int
    ports = luigi.Parameter(default="")

    def __init__(self, *args, **kwargs):
        super(Masscan, self).__init__(*args, **kwargs)
        self.masscan_output = f"masscan.{self.target_file}.json"

    def requires(self):
        return {"target_list": TargetList(target_file=self.target_file)}

    def output(self):
        return luigi.LocalTarget(self.masscan_output)

    def program_args(self):
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
            self.masscan_output,
            "--ports",
            self.ports,
            "-iL",
            self.input().get("target_list").path,
        ]

        return command
