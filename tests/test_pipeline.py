"""Kiểm máy trạng thái, cổng, bài học và chốt chặn repo ở chế độ dry (không tốn tiền, không gọi AI).

Chạy: .venv/bin/python -m unittest discover -s tests
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT / "core" / "scripts"))

from news import lessons, pipeline, steps  # noqa: E402
from news.config import Config  # noqa: E402
from news.episode import Episode, read_json  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = mock.patch.dict(os.environ, {"NEWS_DATA_DIR": self.tmp.name, "NEWS_DRY": "1", "NEWS_NOTIFY": "0", "NEWS_DRY_RENDER": "ffmpeg", "NEWS_OFFLINE": "1"})
        self.env.start()
        self.addCleanup(self.env.stop)
        lessons_dir = Path(self.tmp.name) / "repo-lessons"
        patcher = mock.patch.object(lessons, "LESSONS", lessons_dir)  # không ghi vào lessons/ thật
        patcher.start()
        self.addCleanup(patcher.stop)
        self.cfg = Config()

    def new(self, stamp="2026-01-01-1030"):
        return Episode.create(self.cfg.data_dir, stamp, "manual")


class PipelineTest(Base):
    def test_full_dry_run(self):
        episode = self.new()
        pipeline.run(self.cfg, episode)
        self.assertEqual(episode.state["status"], "done", episode.state["blocker"])
        self.assertTrue(episode.path.name.endswith("tin-mau-hoa-don"))
        self.assertTrue(episode.file("render/final.mp4").exists())
        outbox = sorted(p.name.rsplit(".", 2)[1] for p in (self.cfg.data_dir / "outbox").iterdir())
        self.assertEqual(outbox, ["facebook_reels", "tiktok", "youtube_shorts"])
        self.assertEqual(read_json(next((self.cfg.data_dir / "outbox").iterdir()))["status"], "pending_connection")

    def test_resume_does_not_redo_paid_step(self):
        episode = self.new()
        pipeline.run(self.cfg, episode, until="voice")
        self.assertEqual(episode.state["status"], "paused")
        pipeline.run(self.cfg, Episode(episode.path))
        ledger = (self.cfg.data_dir / "_ledger.jsonl").read_text().splitlines()
        self.assertEqual(len(ledger), 1, "bước giọng (tốn tiền) chỉ được chạy một lần")
        self.assertEqual(Episode(episode.path).state["status"], "done")

    def test_same_story_is_not_repeated(self):
        pipeline.run(self.cfg, self.new("2026-01-01-1030"))
        second = self.new("2026-01-01-1900")
        pipeline.run(self.cfg, second)
        self.assertEqual(second.state["status"], "needs_human")
        self.assertIn("Tin đã làm", second.state["blocker"])

    def test_failed_review_goes_back_to_writer_with_feedback(self):
        calls = {"n": 0}
        original = steps.check_review

        def flaky(ctx):
            calls["n"] += 1
            return ["Fact sai ở s2: mẫu"] if calls["n"] == 1 else original(ctx)

        with mock.patch.object(steps.BY_NAME["review"], "check", flaky):
            episode = self.new()
            pipeline.run(self.cfg, episode)
        self.assertEqual(episode.state["status"], "done")
        self.assertEqual(episode.state["steps"]["write"]["attempts"], 2)
        self.assertEqual(read_json(episode.file("qa/feedback_write.json")), ["Fact sai ở s2: mẫu"])
        events = lessons.load_events(self.cfg)
        self.assertEqual([e["step"] for e in events], ["review"])

    def test_budget_stops_paid_step(self):
        self.cfg.enforce_budget = True
        self.cfg.channel["budget"]["vbee_chars_per_day"] = 10
        episode = self.new()
        pipeline.run(self.cfg, episode)
        self.assertEqual(episode.state["status"], "needs_human")
        self.assertIn("ngân sách", episode.state["blocker"])
        self.assertFalse(episode.file("audio/voice.mp3").exists())

    def test_not_ready_step_stops_cleanly(self):
        def not_ready(ctx):
            raise steps.NotReady("assets: chưa xây (thử)")

        with mock.patch.object(steps.BY_NAME["assets"], "run", not_ready):
            episode = self.new()
            pipeline.run(self.cfg, episode)
        self.assertEqual(episode.state["status"], "needs_human")
        self.assertIn("chưa xây", episode.state["blocker"])

    def test_offline_blocks_real_services(self):
        """Lưới an toàn: test không bao giờ được gọi AI/Vbee thật."""
        cfg = Config()
        cfg.dry = False
        cfg.enforce_budget = False
        episode = self.new()
        pipeline.run(cfg, episode)
        self.assertEqual(episode.state["status"], "failed")
        self.assertIn("NEWS_OFFLINE", episode.state["blocker"])
        self.assertFalse((self.cfg.data_dir / "_ledger.jsonl").exists())


class LessonsTest(Base):
    def test_promotion_and_privacy(self):
        item = {"step": "write", "rule": "Giải thích viết tắt BHXH ở lần đầu", "why": "chủ shop không hiểu", "merge_with": None}
        self.assertEqual(lessons.merge_candidates(self.cfg, [item], ["tap-a"], "gate"), [])
        promoted = lessons.merge_candidates(self.cfg, [dict(item, merge_with="write-001")], ["tap-b"], "gate")
        self.assertEqual(promoted, ["write-001"])
        rules = (lessons.LESSONS / "rules" / "write.md").read_text()
        self.assertIn("BHXH", rules)
        public = (lessons.LESSONS / "candidates.yaml").read_text()
        self.assertNotIn("tap-a", public, "bản vào Git không được chứa mã tập")
        self.assertIn("evidence: 2", public)

    def test_owner_feedback_promotes_immediately_and_links_are_dropped(self):
        leaky = {"step": "pick", "rule": "Xem https://example.org", "why": "x", "merge_with": None}
        owner = {"step": "pick", "rule": "Ưu tiên tin có ngày hiệu lực trong 30 ngày", "why": "chủ kênh yêu cầu", "merge_with": None}
        promoted = lessons.merge_candidates(self.cfg, [leaky, owner], ["tap-a"], "owner")
        self.assertEqual(len(promoted), 1)
        self.assertNotIn("example.org", (lessons.LESSONS / "rules" / "pick.md").read_text())


class GuardTest(unittest.TestCase):
    def test_blocks_product_data_and_secrets(self):
        import guard_repo
        self.assertTrue(guard_repo.problems("episodes/2026-01-01-1030/script.json"))
        self.assertTrue(guard_repo.problems("assets/sfx/whoosh-01.mp3"))
        self.assertTrue(guard_repo.problems("config/machine.yaml"))
        self.assertEqual(guard_repo.problems("episodes/.gitkeep"), [])
        self.assertEqual(guard_repo.problems("core/news/pipeline.py"), [])
        fake = "ey" + "J" + "a" * 12 + ".ey" + "J" + "b" * 12 + ".sig"  # ghép lúc chạy để chính file test không bị chặn
        self.assertTrue(guard_repo.SECRET.search(f"token: {fake}"))


if __name__ == "__main__":
    unittest.main()
