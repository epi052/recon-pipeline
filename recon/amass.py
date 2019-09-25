import luigi
from luigi.util import inherits
from luigi.contrib.external_program import ExternalProgramTask

from recon.targets import TargetList


@inherits(TargetList)
class AmassScan(ExternalProgramTask):
    """ Run amass scan to perform subdomain enumeration of given domain(s).

    Expects TARGET_FILE.domains file to be a text file with one top-level domain per line.

    Commands are similar to the following

    amass enum -ip -brute -active -p WEB_PORTS -min-for-recursive 3 -df tesla -json amass.tesla.json

    Args:
        exempt_list: Path to a file providing blacklisted subdomains, one per line.
        target_file: specifies the file on disk containing a list of ips or domains *--* Required by upstream Task
    """

    exempt_list = luigi.Parameter(default="")

    def requires(self):
        """ AmassScan depends on TargetList to run.

        TargetList expects target_file as a parameter.

        Returns:
            luigi.ExternalTask - TargetList
        """
        return TargetList(self.target_file)

    def output(self):
        """ Returns the target output for this task.

        Naming convention for the output file is amass.TARGET_FILE.json.

        Returns:
            luigi.local_target.LocalTarget
        """
        return luigi.LocalTarget(f"amass.{self.target_file}.json")

    def program_args(self):
        """ Defines the options/arguments sent to amass after processing.

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
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
            f"amass.{self.target_file}.json",
        ]

        if self.exempt_list:
            command.append("-blf")  # Path to a file providing blacklisted subdomains
            command.append(self.exempt_list)

        return command
