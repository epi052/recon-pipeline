import logging

import luigi
from luigi.util import inherits
from luigi.contrib.external_program import ExternalProgramTask

from recon.targets import TargetList


@inherits(TargetList)
class Masscan(ExternalProgramTask):
    rate = luigi.Parameter(default="1000")
    interface = luigi.Parameter(default="tun0")
    top_ports = luigi.Parameter(default="")
    ports = luigi.Parameter(default="")

    def __init__(self, *args, **kwargs):
        super(Masscan, self).__init__(*args, **kwargs)
        self.masscan_output = f"masscan.{self.target_file}.json"

    def requires(self):
        if self.ports and self.top_ports:
            logging.error("Only --ports or --top-ports is permitted, not both.")
            raise SystemExit
        return {"target_list": TargetList(target_file=self.target_file)}

    def output(self):
        return luigi.LocalTarget(self.masscan_output)

    def program_args(self):
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
            "--top-ports",
            self.top_ports,
            "-iL",
            self.input().get("target_list").path,
        ]

        return command
