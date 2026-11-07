"""Phụ đề/chữ nhấn (nhanh) và render Remotion thật từ dữ liệu mẫu (chậm, ~30s; bỏ qua nếu chưa npm ci)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from news import captions, checks, pipeline  # noqa: E402
from news.config import Config  # noqa: E402
from news.episode import Episode, read_json  # noqa: E402


def said(tokens, step=0.3):
    return [{"text": t, "start": i * step, "end": i * step + step * 0.9} for i, t in enumerate(tokens)]


class CaptionsTest(unittest.TestCase):
    def test_show_digits_take_time_of_spoken_words(self):
        segment = {"say": "Phạt năm triệu đồng từ ngày một tháng bảy.", "show": "Phạt 5 triệu đồng từ ngày 1/7.",
                   "highlight": ["5 triệu đồng"]}
        words = said(checks.syllables(segment["say"]))
        shown = captions.show_word_times(segment, words)
        self.assertEqual([w["text"] for w in shown], segment["show"].split())
        self.assertAlmostEqual(shown[1]["start"], words[1]["start"])          # "5" ↔ "năm"
        self.assertAlmostEqual(shown[-1]["end"], words[-1]["end"])             # "1/7." ↔ "một tháng bảy."
        script = {"segments": [dict(segment, id="s1")]}
        caps, emphasis, _ = captions.build(script, words)
        self.assertEqual(emphasis[0]["text"], "5 triệu đồng")
        self.assertTrue(all(c["end"] > c["start"] for c in caps))
        self.assertEqual(" ".join(w["text"] for c in caps for w in c["words"]).replace(" ", ""),
                         segment["show"].replace(" ", ""))


@unittest.skipUnless((ROOT / "core/remotion/node_modules/remotion").exists(), "chưa chạy npm ci trong core/remotion")
class RemotionRenderTest(unittest.TestCase):
    def test_dry_episode_renders_with_remotion(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"NEWS_DATA_DIR": tmp, "NEWS_DRY": "1",
                                                                                "NEWS_NOTIFY": "0"}):
            os.environ.pop("NEWS_DRY_RENDER", None)
            cfg = Config()
            episode = Episode.create(cfg.data_dir, "2026-01-01-1030", "manual")
            pipeline.run(cfg, episode, until="render")
            self.assertEqual(episode.state["status"], "paused", episode.state["blocker"])
            props = read_json(episode.file("render/props.json"))
            self.assertEqual(props["overlay"], "overlay.png")
            self.assertTrue(props["captions"] and props["emphasis"] and props["sfx"])
            self.assertEqual(checks.render_check(episode.file("render/final.mp4"), cfg.video), [])


if __name__ == "__main__":
    unittest.main()
