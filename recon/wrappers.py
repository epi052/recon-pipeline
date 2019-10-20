import luigi
from luigi.util import inherits

from recon.nmap import Searchsploit
from recon.web.aquatone import AquatoneScan
from recon.web.corscanner import CORScannerScan
from recon.web.subdomain_takeover import TKOSubsScan, SubjackScan


@inherits(Searchsploit, AquatoneScan, TKOSubsScan, SubjackScan, CORScannerScan)
class FullScan(luigi.WrapperTask):
    """ Wraps multiple scan types in order to run tasks on the same hierarchical level at the same time. """

    def requires(self):
        """ FullScan is a wrapper, as such it requires any Tasks that it wraps. """
        args = {
            "rate": self.rate,
            "target_file": self.target_file,
            "top_ports": self.top_ports,
            "interface": self.interface,
            "ports": self.ports,
            "exempt_list": self.exempt_list,
            "threads": self.threads,
            "scan_timeout": self.scan_timeout,
        }
        yield AquatoneScan(**args)

        del args["scan_timeout"]

        yield SubjackScan(**args)
        yield Searchsploit(**args)
        yield CORScannerScan(**args)

        del args["threads"]

        yield TKOSubsScan(**args)
