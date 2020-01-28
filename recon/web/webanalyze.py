import os
import logging
import ipaddress
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import luigi
from luigi.util import inherits

from recon.config import tool_paths, defaults
from recon.web.targets import GatherWebTargets


@inherits(GatherWebTargets)
class WebanalyzeScan(luigi.Task):
    """ Use webanalyze to determine the technology stack on the given target(s).

    Install:
        .. code-block:: console

            go get -u github.com/rverton/webanalyze

            # loads new apps.json file from wappalyzer project
            webanalyze -update

    Basic Example:
        .. code-block:: console

            webanalyze -host www.tesla.com -output json

    Luigi Example:
        .. code-block:: console

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.web.webanalyze WebanalyzeScan --target-file tesla --top-ports 1000 --interface eth0

    Args:
        threads: number of threads for parallel webanalyze command execution
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *--* Optional for upstream Task
        top_ports: Scan top N most popular ports *--* Required by upstream Task
        ports: specifies the port(s) to be scanned *--* Required by upstream Task
        interface: use the named raw network interface, such as "eth0" *--* Required by upstream Task
        rate: desired rate for transmitting packets (packets per second) *--* Required by upstream Task
        target_file: specifies the file on disk containing a list of ips or domains *--* Required by upstream Task
        results_dir: specifes the directory on disk to which all Task results are written *--* Required by upstream Task
    """

    threads = luigi.Parameter(default=defaults.get("threads", ""))

    def requires(self):
        """ WebanalyzeScan depends on GatherWebTargets to run.

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
        }
        return GatherWebTargets(**args)

    def output(self):
        """ Returns the target output for this task.

        The naming convention for the output file is webanalyze.TARGET_FILE.txt

        Results are stored in their own directory: webanalyze-TARGET_FILE-results

        Returns:
            luigi.local_target.LocalTarget
        """
        return luigi.LocalTarget(f"{self.results_dir}/webanalyze-{self.target_file}-results")

    def _wrapped_subprocess(self, cmd):
        with open(f"webanalyze.{cmd[2].replace('//', '_').replace(':', '')}.txt", "wb") as f:
            subprocess.run(cmd, stderr=f)

    def run(self):
        """ Defines the options/arguments sent to webanalyze after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        try:
            self.threads = abs(int(self.threads))
        except TypeError:
            return logging.error("The value supplied to --threads must be a non-negative integer.")

        commands = list()

        with self.input().open() as f:
            for target in f:
                target = target.strip()

                try:
                    if isinstance(ipaddress.ip_address(target), ipaddress.IPv6Address):  # ipv6
                        target = f"[{target}]"
                except ValueError:
                    # domain names raise ValueErrors, just assume we have a domain and keep on keepin on
                    pass

                for url_scheme in ("https://", "http://"):
                    command = [
                        tool_paths.get("webanalyze"),
                        "-host",
                        f"{url_scheme}{target}",
                    ]
                    commands.append(command)

        Path(self.output().path).mkdir(parents=True, exist_ok=True)

        cwd = Path().cwd()
        os.chdir(self.output().path)

        if not Path("apps.json").exists():
            subprocess.run(f"{tool_paths.get('webanalyze')} -update".split())

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            executor.map(self._wrapped_subprocess, commands)

        os.chdir(str(cwd))
