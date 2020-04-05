import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import pipeline.models.db_manager
from pipeline.models.port_model import Port
from pipeline.models.target_model import Target
from pipeline.models.ip_address_model import IPAddress


class TestDBManager:
    def setup_method(self, tmp_path):
        self.tmp_path = Path(tempfile.mkdtemp())
        self.db_mgr = pipeline.models.db_manager.DBManager(db_location=self.tmp_path / "testdb")

    def teardown_method(self):
        shutil.rmtree(self.tmp_path)

    def create_temp_target(self):
        tgt = Target(
            hostname="localhost",
            ip_addresses=[IPAddress(ipv4_address="127.0.0.1"), IPAddress(ipv6_address="::1")],
            open_ports=[
                Port(port_number=443, protocol="tcp"),
                Port(port_number=80, protocol="tcp"),
                Port(port_number=53, protocol="udp"),
            ],
        )
        return tgt

    def test_invalid_ip_to_add_ipv4_or_v6_address_to_target(self):
        retval = self.db_mgr.add_ipv4_or_v6_address_to_target("dummytarget", "not an ip address")
        assert retval is None

    def test_get_all_web_targets(self):
        subdomain = Target(hostname="google.com")
        ipv4 = Target(ip_addresses=[IPAddress(ipv4_address="13.56.144.135")])
        ipv6 = Target(ip_addresses=[IPAddress(ipv6_address="2606:4700:10::6814:3c33")])
        self.db_mgr.get_and_filter = MagicMock(return_value=[subdomain, ipv4, ipv6])
        expected = [
            "13.56.144.135",
            "2606:4700:10::6814:3c33",
            "google.com",
        ]
        actual = self.db_mgr.get_all_web_targets()
        assert set(actual) == set(expected)

    @pytest.mark.parametrize("test_input, expected", [("tcp", ["80", "443"]), ("udp", ["53"])])
    def test_get_ports_by_ip_or_host_and_protocol_tcp(self, test_input, expected):
        tgt = self.create_temp_target()
        self.db_mgr.get_or_create_target_by_ip_or_hostname = MagicMock(return_value=tgt)
        expectedset = set(expected)
        actual = self.db_mgr.get_ports_by_ip_or_host_and_protocol("dummy", test_input)
        assert set(actual) == expectedset
