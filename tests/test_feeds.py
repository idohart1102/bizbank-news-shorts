"""Đọc RSS offline: định dạng ngày, encoding sai, lọc từ khóa nguyên từ."""
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))
from news import feeds  # noqa: E402

RSS = """<?xml version="1.0" encoding="iso-8859-1"?><rss><channel>
<item><title><![CDATA[Hộ kinh doanh phải dùng hóa đơn điện tử]]></title><link>https://example.org/a</link>
<description><![CDATA[<p>Tóm tắt</p>]]></description><pubDate>11/6/2026 5:31:00 PM</pubDate>
<enclosure url="https://example.org/a.jpg" type="image/jpeg"/></item>
<item><title>Ca sĩ ra mắt album</title><link>https://example.org/b</link><pubDate>Fri, 06 Nov 2026 10:00:00 +0700</pubDate></item>
</channel></rss>""".encode("utf-8")


class FeedsTest(unittest.TestCase):
    def test_parse_vietnamese_feed_with_wrong_encoding(self):
        items = feeds.parse_feed(RSS, {"name": "Mẫu", "tier": 1})
        self.assertEqual(items[0]["title"], "Hộ kinh doanh phải dùng hóa đơn điện tử")
        self.assertEqual(items[0]["published_at"].hour, 17)
        self.assertEqual(items[0]["image"], "https://example.org/a.jpg")
        self.assertEqual(items[1]["published_at"].isoformat(), "2026-11-06T10:00:00+07:00")

    def test_plain_and_word_boundary(self):
        self.assertEqual(feeds.plain("Hóa đơn Đỏ"), "hoa don do")
        import re
        rule = re.compile(r"\bphi\b")
        self.assertTrue(rule.search(feeds.plain("tăng phí giao hàng")))
        self.assertFalse(rule.search(feeds.plain("phiên chợ")))


if __name__ == "__main__":
    unittest.main()
