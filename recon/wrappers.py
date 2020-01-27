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
    """ Wraps multiple scan types in order to run tasks on the same hierarchical level at the same time.

    Args:
        threads: number of threads for parallel gobuster command execution
        wordlist: wordlist used for forced browsing
        extensions: additional extensions to apply to each item in the wordlist
        recursive: whether or not to recursively gobust the target (may produce a LOT of traffic... quickly)
        proxy: protocol://ip:port proxy specification for gobuster
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *--* Optional for upstream Task
        top_ports: Scan top N most popular ports *--* Required by upstream Task
        ports: specifies the port(s) to be scanned *--* Required by upstream Task
        interface: use the named raw network interface, such as "eth0" *--* Required by upstream Task
        rate: desired rate for transmitting packets (packets per second) *--* Required by upstream Task
        target_file: specifies the file on disk containing a list of ips or domains *--* Required by upstream Task
        results_dir: specifes the directory on disk to which all Task results are written *--* Required by upstream Task
    """

    def requires(self):
        """ FullScan is a wrapper, as such it requires any Tasks that it wraps. """
        args = {
            "results_dir": self.results_dir,
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

        # remove options that are gobuster specific; if left dictionary unpacking to other scans throws an exception
        for gobuster_opt in ("proxy", "wordlist", "extensions", "recursive"):
            del args[gobuster_opt]

        # add aquatone scan specific option
        args.update({"scan_timeout": self.scan_timeout})

        yield AquatoneScan(**args)

        del args["scan_timeout"]

        yield SubjackScan(**args)
        yield SearchsploitScan(**args)
        yield CORScannerScan(**args)
        yield WebanalyzeScan(**args)

        del args["threads"]

        yield TKOSubsScan(**args)


@inherits(SearchsploitScan, AquatoneScan, GobusterScan, WebanalyzeScan)
class HTBScan(luigi.WrapperTask):
    """ Wraps multiple scan types in order to run tasks on the same hierarchical level at the same time.

    Args:
        threads: number of threads for parallel gobuster command execution
        wordlist: wordlist used for forced browsing
        extensions: additional extensions to apply to each item in the wordlist
        recursive: whether or not to recursively gobust the target (may produce a LOT of traffic... quickly)
        proxy: protocol://ip:port proxy specification for gobuster
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *--* Optional for upstream Task
        top_ports: Scan top N most popular ports *--* Required by upstream Task
        ports: specifies the port(s) to be scanned *--* Required by upstream Task
        interface: use the named raw network interface, such as "eth0" *--* Required by upstream Task
        rate: desired rate for transmitting packets (packets per second) *--* Required by upstream Task
        target_file: specifies the file on disk containing a list of ips or domains *--* Required by upstream Task
        results_dir: specifes the directory on disk to which all Task results are written *--* Required by upstream Task
    """

    def requires(self):
        """ HTBScan is a wrapper, as such it requires any Tasks that it wraps. """
        args = {
            "results_dir": self.results_dir,
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

        # remove options that are gobuster specific; if left dictionary unpacking to other scans throws an exception
        for gobuster_opt in ("proxy", "wordlist", "extensions", "recursive"):
            del args[gobuster_opt]

        # add aquatone scan specific option
        args.update({"scan_timeout": self.scan_timeout})

        yield AquatoneScan(**args)

        del args["scan_timeout"]

        yield SearchsploitScan(**args)
        yield WebanalyzeScan(**args)
