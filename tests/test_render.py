"""Phụ đề/chữ nhấn (nhanh) và render Remotion thật từ dữ liệu mẫu (chậm, ~30s; bỏ qua nếu chưa npm ci)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from news import checks, pipeline, timeline  # noqa: E402
from news.config import Config  # noqa: E402
from news.episode import Episode, read_json  # noqa: E402


def said(tokens, step=0.3):
    return [{"text": t, "start": i * step, "end": i * step + step * 0.9} for i, t in enumerate(tokens)]


class TimelineTest(unittest.TestCase):
    def test_cards_and_cutouts_follow_spoken_trigger(self):
        segment = {"id": "s1", "say": "Phạt năm triệu đồng từ ngày một tháng bảy.", "show": "Phạt 5 triệu đồng từ ngày 1/7.",
                   "cards": [{"value": "5 triệu", "label": "Mức phạt", "trigger": "5 triệu đồng"},
                             {"value": "1/7", "label": "Ngày áp dụng", "trigger": "1/7"}],
                   "cutouts": [{"name": "tờ tiền", "kind": "object", "trigger": "Phạt", "search": "banknote"}]}
        words = said(checks.syllables(segment["say"]))
        shown = timeline.show_word_times(segment, words)
        self.assertEqual([w["text"] for w in shown], segment["show"].split())
        self.assertAlmostEqual(shown[1]["start"], words[1]["start"])          # "5" ↔ "năm"
        cards, cutouts = timeline.events({"segments": [segment]}, words, 10.0)
        self.assertAlmostEqual(cards[0]["start"], words[1]["start"])
        self.assertLessEqual(cards[0]["end"], cards[1]["start"], "thẻ sau hiện thì thẻ trước tắt")
        self.assertEqual(cutouts[0]["start"], 0.0)


@unittest.skipUnless((ROOT / "core/remotion/node_modules/remotion").exists(), "chưa chạy npm ci trong core/remotion")
class RemotionRenderTest(unittest.TestCase):
    def test_dry_episode_renders_with_remotion(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"NEWS_DATA_DIR": tmp, "NEWS_DRY": "1",
                                                                                "NEWS_NOTIFY": "0", "NEWS_OFFLINE": "1"}):
            os.environ.pop("NEWS_DRY_RENDER", None)
            cfg = Config()
            episode = Episode.create(cfg.data_dir, "2026-01-01-1030", "manual")
            pipeline.run(cfg, episode, until="render")
            self.assertEqual(episode.state["status"], "paused", episode.state["blocker"])
            props = read_json(episode.file("render/props.json"))
            self.assertEqual(props["overlay"], "overlay.png")
            self.assertTrue(props["cards"] and props["cutouts"] and props["sfx"])
            self.assertNotIn("captions", props, "không làm phụ đề")
            self.assertTrue(all(c["sfx"] for c in props["cards"] + props["cutouts"]), "thẻ/cutout có tiếng động")
            self.assertTrue(props["music"] and props["music"]["volume"] < 0.5, "nhạc nền nhỏ xuyên suốt")
            self.assertEqual(len({s["src"] for s in props["scenes"]}), len(props["scenes"]), "không dùng lại ảnh")
            self.assertEqual(checks.render_check(episode.file("render/final.mp4"), cfg.video), [])


if __name__ == "__main__":
    unittest.main()
