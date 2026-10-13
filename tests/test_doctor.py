"""Pure standard-library tests; do not install or execute reconnaissance tools."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "doctor.py"
sys.path.insert(0, str(ROOT / "scripts"))
import doctor


class DoctorTests(unittest.TestCase):
    def test_offline_diagnostics_do_not_touch_network(self):
        def forbidden_lookup(*args, **kwargs):
            raise AssertionError("unexpected DNS request")
        result = doctor.diagnose(offline=True, root=ROOT, dns_lookup=forbidden_lookup)
        self.assertFalse(any(item["name"].startswith("dns:") for item in result))
        self.assertTrue(any(item["name"] == "python" for item in result))

    def test_missing_required_files_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = doctor.diagnose(offline=True, root=Path(tmp))
            self.assertTrue(any(r["status"] == "error" and r["name"] == "Pipfile" for r in result))

    def test_dns_errors_do_not_crash_doctor(self):
        def fail(*_a, **_kw):
            raise OSError("test offline")
        result = doctor.diagnose(offline=False, root=ROOT, dns_lookup=fail)
        dns = [r for r in result if r["name"].startswith("dns:")]
        self.assertEqual(2, len(dns))
        self.assertTrue(all(r["status"] == "error" for r in dns))

    def test_modern_release_parser(self):
        self.assertEqual((2, 7, 0), doctor.release_parts("2.7.0"))
        self.assertEqual((6, 0, 3), doctor.release_parts("6.0.3"))
        self.assertEqual((2, 6, 2), doctor.release_parts("2.6.2.post1"))
        self.assertIsNone(doctor.release_parts("unknown"))

    def test_modern_packages_are_ok_legacy_pins_warn(self):
        from unittest.mock import patch
        modern = {
            "cmd2": "2.7.0",
            "luigi": "3.8.1",
            "SQLAlchemy": "1.4.54",
            "PyYAML": "6.0.3",
            "python-libnmap": "0.7.3",
        }
        with patch.object(doctor, "version_of", side_effect=modern.get):
            rows = doctor.diagnose(offline=True, root=ROOT)
        package_rows = [r for r in rows if r["name"].startswith("package:")]
        self.assertEqual(5, len(package_rows))
        self.assertTrue(all(r["status"] == "ok" for r in package_rows), package_rows)
        with patch.object(doctor, "version_of", side_effect=doctor.LEGACY_PINS.get):
            legacy_rows = doctor.diagnose(offline=True, root=ROOT)
        package_rows = [r for r in legacy_rows if r["name"].startswith("package:")]
        self.assertTrue(all(r["status"] == "warning" for r in package_rows), package_rows)

    def test_json_output(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--offline", "--json"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, p.returncode, p.stderr + p.stdout)
        self.assertIn('"name": "python"', p.stdout)


if __name__ == "__main__":
    unittest.main()
