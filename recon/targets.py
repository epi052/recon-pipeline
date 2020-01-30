import shutil
import logging
import ipaddress
from pathlib import Path

import luigi

from recon.config import defaults


class TargetList(luigi.ExternalTask):
    """ External task.  ``TARGET_FILE`` is generated manually by the user from target's scope.

    Args:
        results_dir: specifies the directory on disk to which all Task results are written
    """

    target_file = luigi.Parameter()
    results_dir = luigi.Parameter(default=defaults.get("results-dir", ""))

    def output(self):
        """ Returns the target output for this task. target_file.ips || target_file.domains

        In this case, it expects a file to be present in the local filesystem.
        By convention, TARGET_NAME should be something like tesla or some other
        target identifier.  The returned target output will either be target_file.ips
        or target_file.domains, depending on what is found on the first line of the file.

        Example:  Given a TARGET_FILE of tesla where the first line is tesla.com; tesla.domains
        is written to disk.

        Returns:
            luigi.local_target.LocalTarget
        """
        self.results_dir = Path(self.results_dir)
        self.target_file = Path(self.target_file)

        try:
            with open(self.target_file) as f:
                first_line = f.readline()
                ipaddress.ip_interface(first_line.strip())  # is it a valid ip/network?
        except OSError as e:
            # can't open file; log error / return nothing
            return logging.error(f"opening {self.target_file}: {e.strerror}")
        except ValueError as e:
            # exception thrown by ip_interface; domain name assumed
            logging.debug(e)
            new_target = "domains"
        else:
            # no exception thrown; ip address found
            new_target = "ip_addresses"

        results_subfolder = self.results_dir / "target-results"

        results_subfolder.mkdir(parents=True, exist_ok=True)

        new_path = results_subfolder / new_target

        shutil.copy(self.target_file, new_path.resolve())

        return luigi.LocalTarget(new_path.resolve())
