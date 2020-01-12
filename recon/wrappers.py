import luigi
from luigi.util import inherits

from recon.nmap import SearchsploitScan
from recon.web.aquatone import AquatoneScan
from recon.web.corscanner import CORScannerScan
from recon.web.subdomain_takeover import TKOSubsScan, SubjackScan
from recon.web.gobuster import GobusterScan
from recon.web.webanalyze import WebanalyzeScan


@inherits(
    SearchsploitScan,
    AquatoneScan,
    TKOSubsScan,
    SubjackScan,
    CORScannerScan,
    GobusterScan,
    WebanalyzeScan,
)
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
            "proxy": self.proxy,
            "wordlist": self.wordlist,
            "extensions": self.extensions,
            "recursive": self.recursive,
        }

        yield GobusterScan(**args)

        for gobuster_opt in ("proxy", "wordlist", "extensions", "recursive"):
            del args[gobuster_opt]

        args.update({"scan_timeout": self.scan_timeout})

        yield AquatoneScan(**args)

        del args["scan_timeout"]

        yield SubjackScan(**args)
        yield SearchsploitScan(**args)
        yield CORScannerScan(**args)
        yield WebanalyzeScan(**args)

        del args["threads"]

        yield TKOSubsScan(**args)
