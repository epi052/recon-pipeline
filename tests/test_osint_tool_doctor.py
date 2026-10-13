"""Offline tests for the opt-in dependency diagnostic."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch
from importlib.metadata import PackageNotFoundError

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "osint_tool_doctor.py"
spec = importlib.util.spec_from_file_location("osint_tool_doctor", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ToolDoctorTests(unittest.TestCase):
    def test_all_packages_present(self):
        with patch.object(module.importlib.metadata, "version", return_value="1.0"):
            self.assertTrue(all(x["status"] == "ok" for x in module.check()))
    def test_missing_package(self):
        with patch.object(module.importlib.metadata, "version", side_effect=PackageNotFoundError):
            self.assertEqual(len(module.PACKAGES), len([x for x in module.check() if x["status"] == "missing"]))
    def test_no_network_clients_imported(self):
        self.assertEqual(module.PACKAGES, ("requests", "dnspython", "beautifulsoup4", "ExifRead"))

if __name__ == "__main__":
    unittest.main()
