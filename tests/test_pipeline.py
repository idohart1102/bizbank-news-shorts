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


class PlanRulesTest(unittest.TestCase):
    def test_owner_rules_no_image_reuse_and_sfx_each_segment(self):
        from news import checks
        assets = {"items": [{"id": i, "segment": s, "kind": "real"} for i, s in (("a", "s1"), ("b", "s2"))]}
        scene = lambda start, end, seg, asset, sfx=None: {"start": start, "end": end, "segment": seg, "asset": asset,
                                                          "motion": "zoom-in", "headline": None, "highlight_words": [], "sfx": sfx}
        segments = [{"segment": "s1", "start": 0, "end": 4}, {"segment": "s2", "start": 4, "end": 6}]
        plan = {"template": "default", "fps": 30, "duration": 6, "music": None,
                "scenes": [scene(0, 2, "s1", "a", "sting-01"), scene(2, 4, "s1", "a"), scene(4, 6, "s2", "b")]}
        errors = checks.validate_plan(plan, segments, assets, {"sting-01": {}}, 6)
        self.assertTrue(any("dùng 2 lần" in e for e in errors), errors)
        self.assertFalse(any("s2 không có tiếng động" in e for e in errors), "đoạn cuối không bắt buộc sfx")
        card = {"value": "5 triệu", "start": 1.5, "end": 4.0}
        errors = checks.validate_plan(plan, segments, assets, {"sting-01": {}}, 6, cards=[card])
        self.assertTrue(any("không được kéo sang cảnh sau" in e for e in errors), "cắt cảnh 0,5s sau khi thẻ hiện")


class AssetRelevanceTest(Base):
    def test_low_relevance_images_dropped_and_short_segments_searched_again(self):
        from news import media
        episode = self.new()
        pipeline.run(self.cfg, episode, until="voice")
        ctx = steps.Ctx(self.cfg, episode)
        calls = []

        def fake_run(cfg, ep, role, step, context, schema_name, **kwargs):
            seg = context["Các đoạn"][0]["segment"]
            calls.append(kwargs.get("label"))
            bad = {"image_url": f"https://x/{seg}-bad.jpg", "page_url": "https://x", "credit": "x", "kind": "real",
                   "why": "", "subject": "app mua sắm", "relevance": 3}
            good = dict(bad, image_url=f"https://x/{kwargs.get('label')}-good.jpg", subject="cột bơm", relevance=8)
            return {"segments": [{"segment": seg, "ai_prompt": "p", "candidates": [bad, good]}], "cutouts": []}

        with mock.patch.object(media.agents, "run", fake_run), \
                mock.patch.object(media, "download", lambda url, referer=None: url.encode()), \
                mock.patch.object(media, "probe_image", lambda path, ffprobe="ffprobe": (1920, 1440)), \
                mock.patch.object(media, "normalize", lambda raw, target, *a: (target.write_bytes(raw), (1920, 1440))[1]), \
                mock.patch.object(media, "og_image", lambda url: None), \
                mock.patch.object(media.agents, "generate_image", lambda *a, **k: b"ai-" + os.urandom(4)), \
                mock.patch.object(media, "gather_cutouts", lambda *a: None):
            media.gather(ctx)
        items = read_json(episode.file("assets.json"))["items"]
        self.assertFalse([i for i in items if "app mua sắm" in i["note"]], "ảnh liên quan thấp không được vào assets")
        self.assertTrue(all("liên quan 8/10" in i["note"] for i in items if i["kind"] == "real"))
        self.assertTrue(any(label and label.endswith("-bu") for label in calls), "đoạn thiếu ảnh phải được tìm bù")


class AiBackgroundTest(Base):
    def test_qc_background_issue_adds_ai_image_for_that_segment(self):
        from news import media
        episode = self.new()
        pipeline.run(self.cfg, episode)
        ctx = steps.Ctx(self.cfg, episode)
        scene = read_json(episode.file("edit_plan.json"))["scenes"][1]
        qc = {"pass": False, "issues": [
            {"time": scene["start"] + 0.1, "severity": "major", "kind": "background", "problem": "lạc đề", "fix": "đổi ảnh"},
            {"time": 0.5, "severity": "minor", "kind": "background", "problem": "hơi mờ", "fix": ""}]}
        before = len(read_json(episode.file("assets.json"))["items"])
        with mock.patch.object(media.agents, "generate_image", lambda *a, **k: b"img"), \
                mock.patch.object(media, "normalize", lambda raw, target, *a: (target.write_bytes(raw), (1536, 1024))[1]):
            self.assertEqual(media.add_ai_backgrounds(ctx, qc), 1)
        items = read_json(episode.file("assets.json"))["items"]
        self.assertEqual(len(items), before + 1)
        self.assertEqual((items[-1]["segment"], items[-1]["kind"]), (scene["segment"], "ai"))


class CardRulesTest(unittest.TestCase):
    def test_time_and_date_count_as_one_value(self):
        from news.checks import card_values
        for value in ("15h ngày 12/11", "Từ 15h 12/11", "1/1/2027", "15h30", "19.399 đồng/lít"):
            self.assertEqual(card_values(value), 1, value)
        self.assertEqual(card_values("40–150 triệu"), 2)
        self.assertEqual(card_values("5,7/5,08/4,45"), 3)
        self.assertEqual(card_values("19.399 và 19.845 từ 15h 12/11"), 3)

    def test_card_allows_three_values(self):
        from news.checks import MAX_CARD_VALUES
        self.assertEqual(MAX_CARD_VALUES, 3)


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

    def test_owner_feedback_replaces_wording_of_merged_rule(self):
        old = {"step": "write", "rule": "Thẻ giờ chỉ ghi giờ, bỏ ngày", "why": "gate chặn", "merge_with": None}
        lessons.merge_candidates(self.cfg, [old], ["tap-a"], "gate")
        owner = {"step": "write", "rule": "Thẻ được ghi giờ kèm ngày", "why": "chủ kênh chấp nhận", "merge_with": "write-001"}
        lessons.merge_candidates(self.cfg, [owner], ["tap-b"], "owner")
        rules = (lessons.LESSONS / "rules" / "write.md").read_text()
        self.assertIn("giờ kèm ngày", rules)
        self.assertNotIn("bỏ ngày", rules)

    def test_new_rule_does_not_rerun_finished_step(self):
        episode = self.new()
        pipeline.run(self.cfg, episode)
        before = read_json(episode.file("state.json"))["steps"]["write"]["input_hash"]
        (lessons.LESSONS / "rules").mkdir(parents=True, exist_ok=True)
        (lessons.LESSONS / "rules" / "write.md").write_text("- [write-999] luật mới\n")
        ctx = steps.Ctx(self.cfg, episode)
        self.assertEqual(pipeline.input_hash(ctx, steps.BY_NAME["write"]), before)


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


class SkipStoryTest(Base):
    """Kịch bản trượt hết vòng khi chưa tạo giọng: tự bỏ tin, làm tin kế tiếp."""

    def patch_step(self, name, attr, func):
        patcher = mock.patch.object(steps.BY_NAME[name], attr, func)
        patcher.start()
        self.addCleanup(patcher.stop)

    def setup_two_stories(self):
        def collect(ctx):
            inbox = read_json(steps.FIXTURE / "inbox.json")
            second = json.loads(json.dumps(inbox["stories"][0]))
            second.update(id="tin-thu-hai", score=7)
            for source in second["sources"]:
                source["url"] += "?2"
            inbox["stories"].append(second)
            steps.write_json(ctx.ep.file("inbox.json"), inbox)

        def pick(ctx):
            skipped = {s["story"] for s in ctx.ep.state.get("skipped_stories", [])}
            brief = read_json(steps.FIXTURE / "brief.json")
            story = next(s for s in ctx.json("inbox.json")["stories"] if s["id"] not in skipped)
            brief["story_ids"] = [story["id"]]
            brief["sources"] = [dict(s, url=story["sources"][0]["url"]) for s in brief["sources"]]
            steps.write_json(ctx.ep.file("brief.json"), brief)
            ctx.ep.rename_with_slug(story["id"])

        self.patch_step("collect", "run", collect)
        self.patch_step("pick", "run", pick)

    def test_skips_to_next_story(self):
        self.setup_two_stories()
        original = steps.BY_NAME["review"].check
        self.patch_step("review", "check", lambda ctx: ["Fact sai"] if ctx.json("brief.json")["story_ids"] == ["tin-mau-hoa-don"] else original(ctx))
        episode = self.new()
        pipeline.run(self.cfg, episode)
        self.assertEqual(episode.state["status"], "done", episode.state["blocker"])
        self.assertEqual([s["story"] for s in episode.state["skipped_stories"]], ["tin-mau-hoa-don"])
        self.assertTrue(episode.path.name.endswith("tin-thu-hai"))

    def test_stops_when_no_story_left(self):
        self.patch_step("review", "check", lambda ctx: ["Fact sai"])
        episode = self.new()
        pipeline.run(self.cfg, episode)
        self.assertEqual(episode.state["status"], "needs_human")
        self.assertIn("không còn tin", episode.state["blocker"])

    def test_owner_choice_is_not_skipped(self):
        self.setup_two_stories()
        self.patch_step("review", "check", lambda ctx: ["Fact sai"])
        episode = self.new()
        episode.state["story_choice"] = "tin-mau-hoa-don"
        pipeline.run(self.cfg, episode)
        self.assertEqual(episode.state["status"], "needs_human")
        self.assertIn("tin do Sếp chọn", episode.state["blocker"])
