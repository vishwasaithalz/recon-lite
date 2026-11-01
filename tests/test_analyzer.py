import json
import tempfile
import unittest
from pathlib import Path

from recon_lite.analyzer import analyze_headers, analyze_file, parse_headers_text


class HeaderParserTests(unittest.TestCase):
    def test_parses_raw_headers_case_insensitively(self):
        result = parse_headers_text("HTTP/2 200\nContent-Type: text/html\nX-Test: yes\n")
        self.assertEqual(result["content-type"], "text/html")
        self.assertEqual(result["x-test"], "yes")

    def test_combines_duplicate_headers(self):
        result = parse_headers_text("X-Example: one\nX-Example: two\n")
        self.assertEqual(result["x-example"], "one, two")

    def test_parses_json_mapping(self):
        result = parse_headers_text(json.dumps({"X-Test": "ok"}))
        self.assertEqual(result, {"x-test": "ok"})

    def test_rejects_empty_input(self):
        with self.assertRaises(ValueError):
            parse_headers_text("  ")

    def test_rejects_malformed_line(self):
        with self.assertRaises(ValueError):
            parse_headers_text("this is not a header")


class HeaderAnalysisTests(unittest.TestCase):
    def test_complete_baseline_does_not_flag_missing_headers(self):
        headers = {
            "content-security-policy": "default-src 'self'; frame-ancestors 'none'",
            "strict-transport-security": "max-age=31536000",
            "x-content-type-options": "nosniff",
            "referrer-policy": "strict-origin-when-cross-origin",
            "permissions-policy": "camera=(), microphone=()",
        }
        report = analyze_headers(headers)
        missing_or_review = [f for f in report["findings"] if f["status"] in {"missing", "review"}]
        self.assertEqual(missing_or_review, [])
        self.assertEqual(report["score"], 100)

    def test_missing_headers_are_reported(self):
        report = analyze_headers({})
        self.assertGreater(report["summary"]["missing"], 0)
        self.assertLess(report["score"], 100)

    def test_csp_frame_ancestors_counts_as_framing_control(self):
        report = analyze_headers({"content-security-policy": "default-src 'self'; frame-ancestors 'none'"})
        framing = [f for f in report["findings"] if f["header"] == "X-Frame-Options / CSP frame-ancestors"]
        self.assertEqual(framing[0]["status"], "present")

    def test_server_disclosure_is_informational(self):
        report = analyze_headers({"server": "example"})
        disclosure = [f for f in report["findings"] if f["header"] == "Server"]
        self.assertEqual(disclosure[0]["severity"], "info")
        self.assertEqual(disclosure[0]["status"], "disclosure")

    def test_reads_local_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "headers.txt"
            file_path.write_text("X-Content-Type-Options: nosniff\n", encoding="utf-8")
            report = analyze_file(file_path)
            self.assertEqual(report["tool"], "Recon Lite")


if __name__ == "__main__":
    unittest.main()
