import luigi
from luigi.util import inherits
from luigi.contrib.sqla import SQLAlchemyTarget

from ..config import web_ports
from ..amass import ParseAmassOutput
from ..masscan import ParseMasscanOutput
from ...models.db_manager import DBManager


@inherits(ParseMasscanOutput)
class GatherWebTargets(luigi.Task):
    """ Gather all subdomains as well as any ip addresses known to have a configured web port open.

    Args:
        db_location: specifies the path to the database used for storing results *Required by upstream Task*
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *Optional by upstream Task*
        top_ports: Scan top N most popular ports *Required by upstream Task*
        ports: specifies the port(s) to be scanned *Required by upstream Task*
        interface: use the named raw network interface, such as "eth0" *Required by upstream Task*
        rate: desired rate for transmitting packets (packets per second) *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = DBManager(db_location=self.db_location)

    def requires(self):
        """ GatherWebTargets depends on ParseMasscanOutput and ParseAmassOutput to run.

        ParseMasscanOutput expects rate, target_file, interface, and either ports or top_ports as parameters.
        ParseAmassOutput accepts exempt_list and expects target_file

        Returns:
            dict(str: ParseMasscanOutput, str: ParseAmassOutput)
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
        return {
            "masscan-output": ParseMasscanOutput(**args),
            "amass-output": ParseAmassOutput(
                exempt_list=self.exempt_list,
                target_file=self.target_file,
                results_dir=self.results_dir,
                db_location=self.db_location,
            ),
        }

    def output(self):
        """ Returns the target output for this task.

        Returns:
            luigi.contrib.sqla.SQLAlchemyTarget
        """
        return SQLAlchemyTarget(
            connection_string=self.db_mgr.connection_string, target_table="target", update_id=self.task_id
        )

    def run(self):
        """ Gather all potential web targets and tag them as web in the database. """

        for target in self.db_mgr.get_all_targets():
            ports = self.db_mgr.get_ports_by_ip_or_host_and_protocol(target, "tcp")
            if any(port in web_ports for port in ports):
                tgt = self.db_mgr.get_target_by_ip_or_hostname(target)
                tgt.is_web = True
                self.db_mgr.add(tgt)
                self.output().touch()

        # in the event that there are no web ports for any target, we still want to be able to mark the
        # task complete successfully.  we accomplish this by calling .touch() even though a database entry
        # may not have happened
        self.output().touch()

        self.db_mgr.close()
