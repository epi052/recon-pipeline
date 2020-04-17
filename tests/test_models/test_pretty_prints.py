from pipeline.models.technology_model import Technology
from pipeline.models.searchsploit_model import SearchsploitResult
from pipeline.models.nmap_model import NmapResult
from pipeline.models.port_model import Port
from pipeline.models.ip_address_model import IPAddress


def test_technology_pretty():
    assert Technology().pretty() == Technology().__str__()


def test_searchsploit_pretty():
    ssr = SearchsploitResult(path="stuff", type="exploit", title="super cool title")
    assert ssr.pretty() == ssr.__str__()


def test_nmap_pretty():
    nmr = NmapResult(
        ip_address=IPAddress(ipv4_address="127.0.0.1"), service="http", port=Port(port_number="80", protocol="tcp")
    )
    assert nmr.pretty() == nmr.__str__()
