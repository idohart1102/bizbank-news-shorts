"""Duyệt nguồn ngoài danh sách ưu tiên."""
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))
from news import sources  # noqa: E402


class SourcesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original = sources.APPROVED
        sources.APPROVED = Path(self.tmp.name) / "approved.yaml"
        self.cfg = SimpleNamespace(data_dir=Path(self.tmp.name) / "episodes")

    def tearDown(self):
        sources.APPROVED = self.original
        self.tmp.cleanup()

    def test_listed_domain_passes(self):
        self.assertEqual(sources.status("https://www.tinnhanhchungkhoan.vn/bai-a.html"), "listed")
        self.assertEqual(sources.status("https://vnexpress.net/thoi-su/x.html"), "listed")

    def test_unknown_domain_waits_then_approved(self):
        url = "https://vietnamplus.vn/bai-b.html"
        errors, pending = sources.review(self.cfg, "tap-1", [{"url": url, "publisher": "VietnamPlus"}])
        self.assertEqual((errors, pending), ([], ["vietnamplus.vn"]))
        sources.review(self.cfg, "tap-1", [{"url": url, "publisher": "VietnamPlus"}])
        self.assertEqual(len(sources.read_requests(self.cfg)), 1)
        sources.decide("vietnamplus.vn", "approved")
        self.assertEqual(sources.status(url), "approved")
        self.assertEqual(sources.read_requests(self.cfg), [])

    def test_rejected_domain_is_error(self):
        sources.decide("https://www.blog-la.vn/x", "rejected")
        errors, pending = sources.review(self.cfg, "tap-1", [{"url": "https://blog-la.vn/y"}])
        self.assertEqual(pending, [])
        self.assertEqual(len(errors), 1)


if __name__ == "__main__":
    unittest.main()
