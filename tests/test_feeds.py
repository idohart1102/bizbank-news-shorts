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

    def test_sources_config_groups(self):
        config = feeds.load_config()
        groups = set(config["groups"])
        names = [s["name"] for s in config["press"]]
        self.assertEqual(len(names), len(set(names)))
        for source in config["press"]:
            self.assertIn(source["tier"], (1, 2, 3), source["name"])
            self.assertIn(source["group"], groups, source["name"])
            self.assertTrue(all(u.startswith("https://") for u in source.get("rss", [])), source["name"])
        guide = feeds.source_guide()
        self.assertEqual(guide["Báo theo nhóm"]["CafeF"]["tier"], 3)

    def test_pillars_match_schemas_and_sources(self):
        import json
        pillars = feeds.load_pillars()
        ids = [p["id"] for p in pillars["pillars"]]
        self.assertEqual(ids, ["von", "quan-tri", "luat", "ai-marketing"])
        for p in pillars["pillars"]:
            self.assertGreater(p["weight"], 0)
            self.assertNotIn("ai", p["keywords"], "«ai» trùng từ «ai» = người nào")
        root = Path(__file__).resolve().parents[1] / "core" / "schemas"
        inbox = json.loads((root / "inbox.schema.json").read_text(encoding="utf-8"))
        brief = json.loads((root / "brief.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(inbox["properties"]["stories"]["items"]["properties"]["pillar"]["enum"], ids)
        self.assertEqual(brief["properties"]["pillar"]["enum"], ids)
        for source in feeds.load_config()["press"]:
            self.assertTrue(set(source.get("pillars", [])) <= set(ids), source["name"])

    def test_pillar_hints(self):
        rules = [(p["id"], feeds.compile_words(p["keywords"])) for p in feeds.load_pillars()["pillars"]]
        item = {"title": "Ai được vay vốn ưu đãi?", "summary": "Ngân hàng hạ lãi suất cho hộ kinh doanh"}
        self.assertEqual(feeds.pillar_hints(item, {}, rules), ["von"])
        item = {"title": "Phạt nặng quảng cáo sai trên TikTok Shop", "summary": ""}
        self.assertEqual(feeds.pillar_hints(item, {"pillars": ["luat"]}, rules), ["luat", "ai-marketing"])


if __name__ == "__main__":
    unittest.main()
