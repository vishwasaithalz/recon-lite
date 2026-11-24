"""CLI export tests for local-only Recon Lite operation."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from recon_lite.cli import main


class OfflineCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.headers = self.root / "headers.txt"
        self.headers.write_text(
            "HTTP/2 200\n"
            "content-security-policy: default-src 'self'; frame-ancestors 'none'\n"
            "strict-transport-security: max-age=31536000\n"
            "x-content-type-options: nosniff\n"
            "referrer-policy: strict-origin-when-cross-origin\n"
            "permissions-policy: camera=()\n",
            encoding="utf-8",
        )

    def run_cli(self, *args):
        out = io.StringIO()
        err = io.StringIO()
        with patch("sys.argv", ["recon-lite", str(self.headers), *args]):
            with redirect_stdout(out), redirect_stderr(err):
                status = main()
        return status, out.getvalue(), err.getvalue()

    def test_json_shorthand_is_machine_readable(self):
        status, stdout, stderr = self.run_cli("--json")
        self.assertEqual(status, 0, stderr)
        data = json.loads(stdout)
        self.assertEqual(data["tool"], "Recon Lite")
        self.assertEqual(data["score"], 100)
        self.assertIn("No network requests", data["scope"])

    def test_explicit_file_export_creates_json_only_once(self):
        path = self.root / "review.json"
        status, stdout, stderr = self.run_cli("--report", str(path))
        self.assertEqual(status, 0, stderr)
        self.assertTrue(path.exists())
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["score"], 100)
        self.assertIn("Saved JSON report", stdout)

        snapshot = path.read_bytes()
        status, stdout, stderr = self.run_cli("--report", str(path))
        self.assertEqual(status, 2)
        self.assertIn("cannot save report", stderr)
        self.assertEqual(path.read_bytes(), snapshot)

    def test_export_requires_a_valid_input(self):
        self.headers.write_text("not-a-header", encoding="utf-8")
        path = self.root / "should-not-exist.json"
        status, stdout, stderr = self.run_cli("--report", str(path))
        self.assertEqual(status, 2)
        self.assertFalse(path.exists())
        self.assertIn("Malformed header", stderr)

    def test_format_json_and_json_alias_agree(self):
        a = self.run_cli("--json")
        b = self.run_cli("--format", "json")
        self.assertEqual(json.loads(a[1]), json.loads(b[1]))


if __name__ == "__main__":
    unittest.main()
