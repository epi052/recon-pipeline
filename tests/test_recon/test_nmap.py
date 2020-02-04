from pathlib import Path
from recon.nmap import ThreadedNmapScan, SearchsploitScan

import luigi

tfp = "../data/bitdiscovery"
tf = Path(tfp).stem
el = "../data/blacklist"
rd = "../data/recon-results"

nmap_results = Path(__file__).parent.parent / "data" / "recon-results" / "nmap-results"


def test_nmap_output_location(tmp_path):
    tns = ThreadedNmapScan(target_file=tf, exempt_list=el, results_dir=str(tmp_path), top_ports=100)

    assert tns.output().path == str(Path(tmp_path) / "nmap-results")


def test_searchsploit_output_location(tmp_path):
    sss = SearchsploitScan(target_file=tf, exempt_list=el, results_dir=str(tmp_path), top_ports=100)

    assert sss.output().path == str(Path(tmp_path) / "searchsploit-results")


def test_searchsploit_produces_results(tmp_path):
    sss = SearchsploitScan(target_file=tf, exempt_list=el, results_dir=str(tmp_path), top_ports=100)

    sss.input = lambda: luigi.LocalTarget(nmap_results)
    sss.run()

    assert len([x for x in Path(sss.output().path).glob("searchsploit*.txt")]) > 0
