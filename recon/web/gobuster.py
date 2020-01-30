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
class GobusterScan(luigi.Task):
    """ Use ``gobuster`` to perform forced browsing.

    Install:
        .. code-block:: console

            go get github.com/OJ/gobuster
            git clone https://github.com/epi052/recursive-gobuster.git

    Basic Example:
        .. code-block:: console

            gobuster dir -q -e -k -t 20 -u www.tesla.com -w /usr/share/seclists/Discovery/Web-Content/common.txt -p http://127.0.0.1:8080 -o gobuster.tesla.txt -x php,html

    Luigi Example:
        .. code-block:: console

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.web.gobuster GobusterScan --target-file tesla --top-ports 1000 --interface eth0 --proxy http://127.0.0.1:8080 --extensions php,html --wordlist /usr/share/seclists/Discovery/Web-Content/common.txt --threads 20

    Args:
        threads: number of threads for parallel gobuster command execution
        wordlist: wordlist used for forced browsing
        extensions: additional extensions to apply to each item in the wordlist
        recursive: whether or not to recursively gobust the target (may produce a LOT of traffic... quickly)
        proxy: protocol://ip:port proxy specification for gobuster
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *Optional by upstream Task*
        top_ports: Scan top N most popular ports *Required by upstream Task*
        ports: specifies the port(s) to be scanned *Required by upstream Task*
        interface: use the named raw network interface, such as "eth0" *Required by upstream Task*
        rate: desired rate for transmitting packets (packets per second) *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

    proxy = luigi.Parameter(default=defaults.get("proxy", ""))
    threads = luigi.Parameter(default=defaults.get("threads", ""))
    wordlist = luigi.Parameter(default=defaults.get("gobuster-wordlist", ""))
    extensions = luigi.Parameter(default=defaults.get("gobuster-extensions", ""))
    recursive = luigi.BoolParameter(default=False)

    def requires(self):
        """ GobusterScan depends on GatherWebTargets to run.

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

        If recursion is disabled, the naming convention for the output file is gobuster.TARGET_FILE.txt
        Otherwise the output file is recursive-gobuster_TARGET_FILE.log

        Results are stored in their own directory: gobuster-TARGET_FILE-results

        Returns:
            luigi.local_target.LocalTarget
        """
        results_subfolder = Path(self.results_dir) / "gobuster-results"

        return luigi.LocalTarget(results_subfolder.resolve())

    def run(self):
        """ Defines the options/arguments sent to gobuster after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        try:
            self.threads = abs(int(self.threads))
        except TypeError:
            return logging.error(
                "The value supplied to --threads must be a non-negative integer."
            )

        commands = list()

        with self.input().open() as f:
            for target in f:
                target = target.strip()

                try:
                    if isinstance(
                        ipaddress.ip_address(target), ipaddress.IPv6Address
                    ):  # ipv6
                        target = f"[{target}]"
                except ValueError:
                    # domain names raise ValueErrors, just assume we have a domain and keep on keepin on
                    pass

                for url_scheme in ("https://", "http://"):
                    if self.recursive:
                        command = [
                            tool_paths.get("recursive-gobuster"),
                            "-w",
                            self.wordlist,
                            f"{url_scheme}{target}",
                        ]
                    else:
                        command = [
                            tool_paths.get("gobuster"),
                            "dir",
                            "-q",
                            "-e",
                            "-k",
                            "-u",
                            f"{url_scheme}{target}",
                            "-w",
                            self.wordlist,
                            "-o",
                            Path(self.output().path).joinpath(
                                f"gobuster.{url_scheme.replace('//', '_').replace(':', '')}{target}.txt"
                            ),
                        ]

                    if self.extensions:
                        command.extend(["-x", self.extensions])

                    if self.proxy:
                        command.extend(["-p", self.proxy])

                    commands.append(command)

        Path(self.output().path).mkdir(parents=True, exist_ok=True)

        if self.recursive:
            # workaround for recursive gobuster not accepting output directory
            cwd = Path().cwd()
            os.chdir(self.output().path)

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            executor.map(subprocess.run, commands)

        if self.recursive:
            os.chdir(str(cwd))
