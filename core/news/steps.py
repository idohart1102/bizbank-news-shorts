"""Các bước của luồng. Mỗi bước khai: input, output, cách chạy, cổng kiểm, trượt thì quay về đâu.

Bản thật của từng bước được bổ sung theo giai đoạn (docs/roadmap.md). Chế độ NEWS_DRY=1 dùng dữ liệu
mẫu trong tests/fixtures/sample để chạy trọn luồng không tốn tiền, dùng cho test và kiểm máy mới.
"""
import json
import os
import shutil
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from . import agents, checks
from .config import ROOT, ensure_online
from .episode import read_json, write_json, write_text

FIXTURE = ROOT / "tests" / "fixtures" / "sample"


class NotReady(Exception):
    """Bước chưa được xây ở bản thật."""


@dataclass
class Step:
    name: str
    inputs: list
    outputs: list
    run: object
    check: object
    retry_to: str = None      # trượt cổng thì làm lại bước này (mặc định chính nó)
    max_rounds: int = 3
    paid: bool = False
    tags: list = field(default_factory=list)


class Ctx:
    def __init__(self, cfg, episode):
        self.cfg, self.ep = cfg, episode

    def json(self, relative):
        return read_json(self.ep.file(relative))

    def feedback(self, step):
        path = self.ep.file(f"qa/feedback_{step}.json")
        return read_json(path) if path.exists() else []

    def history(self):
        path = self.cfg.data_dir / "index.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def sh(self, *command, timeout=600):
        out = subprocess.run([str(c) for c in command], capture_output=True, text=True, timeout=timeout)
        if out.returncode != 0:
            raise RuntimeError(f"{Path(str(command[0])).name} lỗi: {out.stderr.strip()[-400:]}")
        return out.stdout


def fixture(ctx, *names):
    for name in names:
        target = ctx.ep.file(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(FIXTURE / name, target)


def latest(ctx, pattern):
    files = sorted(ctx.ep.path.glob(pattern), key=lambda p: int(p.stem.rsplit("_v", 1)[1]))
    return files[-1] if files else None


def next_version(ctx, prefix):
    return len(list(ctx.ep.path.glob(f"qa/{prefix}_v*.json"))) + 1


# --- 1. Gom tin -------------------------------------------------------------

def run_collect(ctx):
    if ctx.cfg.dry:
        return fixture(ctx, "inbox.json")
    from . import feeds
    raw = feeds.collect()
    write_json(ctx.ep.file("raw_feed.json"), raw)
    if not raw["items"]:
        raise RuntimeError("RSS không có tin nào sau lọc: " + json.dumps(raw["feeds"], ensure_ascii=False)[:300])
    items = [{k: i[k] for k in ("title", "url", "summary", "published_at", "publisher", "tier")} for i in raw["items"]]
    inbox = agents.run(ctx.cfg, ctx.ep, "codex", "collect", {"Ngày": time.strftime("%Y-%m-%d"), "Bài RSS": items}, "inbox")
    known = {i["url"] for i in raw["items"]}
    for story in inbox["stories"]:  # AI không được bịa link: chỉ giữ link có trong RSS
        story["sources"] = [s for s in story["sources"] if s["url"] in known]
    inbox["stories"] = [s for s in inbox["stories"] if s["sources"]]
    write_json(ctx.ep.file("inbox.json"), inbox)


def check_collect(ctx):
    inbox = ctx.json("inbox.json")
    errors = checks.validate_schema("inbox", inbox)
    if not errors and not [s for s in inbox["stories"] if s["score"] >= 6]:
        errors.append("Không có tin nào score ≥ 6")
    return errors


# --- 2. Chọn tin ------------------------------------------------------------

def run_pick(ctx):
    if ctx.cfg.dry:
        fixture(ctx, "brief.json")
    else:
        used = sorted({u for h in ctx.history() for u in h.get("urls", [])})
        ctx_data = {"Tin trong ngày (inbox.json)": ctx.json("inbox.json"), "Link đã làm (không chọn lại)": used,
                    "Lỗi lần trước": ctx.feedback("pick")}
        write_json(ctx.ep.file("brief.json"), agents.run(ctx.cfg, ctx.ep, "claude", "pick", ctx_data, "brief"))
    ctx.ep.rename_with_slug(ctx.json("brief.json")["story_ids"][0])


def check_pick(ctx):
    brief = ctx.json("brief.json")
    errors = checks.validate_schema("brief", brief)
    if errors:
        return errors
    errors += checks.source_rule(brief["sources"])
    used = {u for h in ctx.history() for u in h.get("urls", [])}
    repeated = [s["url"] for s in brief["sources"] if s["url"] in used]
    if repeated:
        errors.append(f"Tin đã làm ở tập trước: {repeated[:2]}")
    return errors


# --- 3. Viết kịch bản ---------------------------------------------------------

def run_write(ctx):
    if ctx.cfg.dry:
        fixture(ctx, "script.json")
    else:
        ctx_data = {"Brief": ctx.json("brief.json"), "Văn bản nguồn": source_texts(ctx, ctx.json("brief.json")["sources"]),
                    "Chuẩn kịch bản": (ROOT / "core/standard/script.md").read_text(encoding="utf-8"),
                    "Bản trước": ctx.json("script.json") if ctx.ep.file("script.json").exists() else "chưa có",
                    "Cần sửa": ctx.feedback("write")}
        write_json(ctx.ep.file("script.json"), agents.run(ctx.cfg, ctx.ep, "claude", "write", ctx_data, "script"))
    derive_script_files(ctx)


def derive_script_files(ctx):
    script = ctx.json("script.json")
    # Nối các đoạn bằng dấu cách, không xuống dòng: xuống dòng làm Vbee nghỉ dài (paragraphBreak).
    write_text(ctx.ep.file("script_tts.txt"), " ".join(s["say"].strip() for s in script["segments"]) + "\n")
    lines = [f"# Nguồn: {script['title']}", ""]
    lines += [f"[{s['id']}] {s['publisher']} (tier {s['tier']}): {s['url']}\n    > {s['quote']}" for s in script["sources"]]
    write_text(ctx.ep.file("sources.md"), "\n".join(lines) + "\n")


def check_write(ctx):
    return checks.lint_script(ctx.json("script.json"))


# --- 4. Duyệt + kiểm fact -----------------------------------------------------

def run_review(ctx):
    version = next_version(ctx, "review")
    target = ctx.ep.file(f"qa/review_v{version}.json")
    if ctx.cfg.dry:
        shutil.copyfile(FIXTURE / "review.json", target)
        return
    script = ctx.json("script.json")
    sources = source_texts(ctx, script["sources"])
    facts = agents.run(ctx.cfg, ctx.ep, "codex", "factcheck", {"Kịch bản": script, "Văn bản nguồn": sources}, "factcheck")
    write_json(ctx.ep.file(f"qa/factcheck_v{version}.json"), facts)
    review = agents.run(ctx.cfg, ctx.ep, "claude", "review",
                        {"Kịch bản": script, "Kết quả đối chiếu nguồn của Codex": facts}, "review")
    review["fact_errors"] = facts["fact_errors"] + review["fact_errors"]
    write_json(target, review)


def source_texts(ctx, sources):
    """Nội dung bài nguồn, tải một lần rồi lưu trong tập (sources_text.json) để các bước dùng chung."""
    path = ctx.ep.file("sources_text.json")
    cache = read_json(path) if path.exists() else {}
    for source in sources:
        if source["url"] not in cache or cache[source["url"]].startswith("[không tải được"):
            cache[source["url"]] = fetch_text(source["url"])
    write_json(path, cache)
    return {s["url"]: cache[s["url"]] for s in sources}


def fetch_text(url, limit=15000):
    ensure_online(f"tải bài {url}")
    import html as htmllib
    import re
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; news-video/1.0)"})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(3_000_000)
        if raw[:2] == b"\x1f\x8b":  # một số trang trả gzip dù không yêu cầu
            import gzip
            raw = gzip.decompress(raw)
        page = raw.decode("utf-8", "replace")
    except OSError as error:
        return f"[không tải được: {error}]"
    page = re.sub(r"<(script|style|nav|header|footer|aside)[\s\S]*?</\1>", " ", page, flags=re.I)
    title = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", page, re.I)
    paragraphs = [htmllib.unescape(re.sub(r"<[^>]+>", " ", p)) for p in re.findall(r"<p[^>]*>([\s\S]*?)</p>", page, re.I)]
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in paragraphs if len(p.strip()) > 40]
    body = "\n".join(paragraphs) if sum(map(len, paragraphs)) > 400 else re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", page)))
    head = re.sub(r"<[^>]+>|\s+", " ", title.group(1)).strip() + "\n" if title else ""
    return (head + body)[:limit]


def check_review(ctx):
    review = read_json(latest(ctx, "qa/review_v*.json"))
    errors = checks.validate_schema("review", review)
    if errors:
        return errors
    errors += [f"Fact sai ở {e['segment']}: {e['claim']} → nguồn: {e['source_says']}. Sửa: {e['fix']}"
               for e in review["fact_errors"]]
    if review["score"] < 8:
        errors.append(f"Điểm {review['score']}/10 < 8")
        errors += [f"{i['segment']}: {i['problem']} → {i['fix']}" for i in review["issues"]]
    return errors


# --- 5. Giọng đọc -------------------------------------------------------------

def run_voice(ctx):
    audio = ctx.ep.file("audio/voice.mp3")
    if ctx.cfg.dry:
        fake_voice(ctx)
    if not ctx.cfg.dry:
        ensure_online("tạo giọng Vbee (tốn credit)")
        tts = ctx.cfg.channel["tts"]
        command = ["tts", "say", "--provider", tts["provider"], "--voice", tts["voice"], "--speed", str(tts.get("speed", 1.0)),
                   "--file", ctx.ep.file("script_tts.txt"), "--out", audio, "--project", tts["project"], "--srt"]
        if tts.get("pauses"):
            command += ["--pauses", ",".join(f"{k}={v}" for k, v in tts["pauses"].items())]
        said = ctx.sh(*command, timeout=1800)
        ctx.sh("tts", "align", "--audio", audio, "--text", ctx.ep.file("script_tts.txt"),
               "--out", ctx.ep.file("audio/voice.srt"), "--words", ctx.ep.file("audio/voice.words.json"), timeout=1800)
        if "dùng lại kết quả cũ" in said:
            ctx.ep.log("giọng: dùng lại kết quả cũ của platform/tts, không tính tiền")
        else:
            ledger(ctx, len(ctx.ep.file("script_tts.txt").read_text(encoding="utf-8")))
    else:
        ledger(ctx, len(ctx.ep.file("script_tts.txt").read_text(encoding="utf-8")))
    segments = checks.segment_times(ctx.json("script.json"), ctx.json("audio/voice.words.json"))
    write_json(ctx.ep.file("audio/segments.json"), segments)


def fake_voice(ctx):
    """Giọng giả: 0,25 giây mỗi âm tiết, chuẩn hóa -14 LUFS."""
    tokens = checks.syllables(ctx.ep.file("script_tts.txt").read_text(encoding="utf-8"))
    seconds = len(tokens) * 0.25
    ctx.sh(ctx.cfg.bin("ffmpeg"), "-y", "-v", "error", "-f", "lavfi", "-i", f"sine=frequency=220:duration={seconds}",
           "-af", "loudnorm=I=-14", "-ar", "44100", ctx.ep.file("audio/voice.mp3"))
    words = [{"text": t, "start": round(i * 0.25, 3), "end": round(i * 0.25 + 0.24, 3)} for i, t in enumerate(tokens)]
    write_json(ctx.ep.file("audio/voice.words.json"), words)
    write_text(ctx.ep.file("audio/voice.srt"), "1\n00:00:00,000 --> 00:00:01,000\n(giả)\n")


def ledger(ctx, chars):
    path = ctx.cfg.data_dir / "_ledger.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"date": time.strftime("%Y-%m-%d"), "episode": ctx.ep.id, "vbee_chars": chars,
                                 "dry": ctx.cfg.dry}) + "\n")


def chars_today(cfg):
    path = cfg.data_dir / "_ledger.jsonl"
    if not path.exists():
        return 0
    today = time.strftime("%Y-%m-%d")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return sum(r["vbee_chars"] for r in rows if r["date"] == today and not r.get("dry"))


def check_voice(ctx):
    seconds = checks.duration(ctx.ep.file("audio/voice.mp3"), ctx.cfg.bin("ffprobe"))
    if seconds > 57:
        script = ctx.json("script.json")
        total = sum(len(checks.syllables(s["say"])) for s in script["segments"])
        cut = int(total * (1 - 55 / seconds)) + 1
        return [f"Giọng dài {seconds:.1f}s > 57s: cắt khoảng {cut} âm tiết"]
    if seconds < 15:
        return [f"Giọng chỉ {seconds:.1f}s, quá ngắn"]
    # Mốc căn chữ phải hợp lý: tiếng Việt đọc tin khoảng 3–7 âm tiết/giây. Lệch là căn hỏng, không phải lỗi kịch bản.
    script = ctx.json("script.json")
    for seg in ctx.json("audio/segments.json"):
        count = len(checks.syllables(next(s["say"] for s in script["segments"] if s["id"] == seg["segment"])))
        rate = count / max(seg["end"] - seg["start"], 0.01)
        if count >= 8 and not 2.0 <= rate <= 9.0:
            raise RuntimeError(f"Căn chữ hỏng: đoạn {seg['segment']} {rate:.1f} âm tiết/giây. Chạy lại tts align")
    return []


# --- 6. Ảnh -------------------------------------------------------------------

def run_assets(ctx):
    if ctx.cfg.dry:
        fixture(ctx, "assets.json")
        colors = ["0x1f4e79", "0x7a1f3d", "0x2e6b30", "0x6b4e16", "0x3b2a6b"]
        for item in ctx.json("assets.json")["items"]:
            if item["kind"] == "cutout":  # PNG trong suốt giả: một khối màu bo giữa nền trong suốt
                ctx.sh(ctx.cfg.bin("ffmpeg"), "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0xE8B04A:s=280x560",
                       "-vf", "format=rgba,pad=400:600:60:40:color=black@0", "-frames:v", "1",
                       ctx.ep.file(f"assets/{item['file']}"))
        for i, item in enumerate(a for a in ctx.json("assets.json")["items"] if a["kind"] != "cutout"):
            ctx.sh(ctx.cfg.bin("ffmpeg"), "-y", "-v", "error", "-f", "lavfi",
                   "-i", f"testsrc2=s=1080x1350,hue=s=0.4,drawbox=c={colors[i % 5]}@0.6:t=fill",
                   "-frames:v", "1", ctx.ep.file(f"assets/{item['file']}"))
        return
    from . import media
    media.gather(ctx)


def check_assets(ctx):
    assets = ctx.json("assets.json")
    errors = checks.validate_schema("assets", assets)
    if errors:
        return errors
    segments = {s["id"] for s in ctx.json("script.json")["segments"]}
    covered = {a["segment"] for a in assets["items"]}
    errors += [f"Đoạn {s} chưa có hình" for s in sorted(segments - covered)]
    for item in assets["items"]:
        if not ctx.ep.file(f"assets/{item['file']}").exists():
            errors.append(f"Thiếu file assets/{item['file']}")
        if item["kind"] in ("real", "doc") and not item["source_url"]:
            errors.append(f"{item['id']}: ảnh {item['kind']} thiếu source_url")
    return errors


# --- 7. Plan dựng ---------------------------------------------------------------

def run_plan(ctx):
    if ctx.cfg.dry:
        return write_json(ctx.ep.file("edit_plan.json"), simple_plan(ctx))
    from . import render, timeline
    script = ctx.json("script.json")
    seconds = round(checks.duration(ctx.ep.file("audio/voice.mp3"), ctx.cfg.bin("ffprobe")), 3)
    cards, cutouts = timeline.events(script, ctx.json("audio/voice.words.json"), seconds)
    _, layout, _ = render.template(ctx.cfg)
    sfx = {k: {"category": v["category"], "duration_s": v["duration_s"]}
           for k, v in json.loads((ROOT / "assets/sfx/index.json").read_text(encoding="utf-8")).items()}
    ctx_data = {
        "Thời lượng audio (giây)": seconds,
        "Mốc từng đoạn": ctx.json("audio/segments.json"),
        "Lời từng đoạn": [{"segment": s["id"], "role": s["role"], "show": s["show"]} for s in script["segments"]],
        "Thẻ chữ/số và cutout (hệ thống tự hiện, tự có tiếng động)": [
            {"kind": k, "text": e.get("value") or e.get("name"), "start": e["start"], "end": e["end"]}
            for k, group in (("card", cards), ("cutout", cutouts)) for e in group],
        "Ảnh nền": [{k: a[k] for k in ("id", "segment", "kind", "width", "height", "note")}
                    for a in ctx.json("assets.json")["items"] if a["kind"] != "cutout"],
        "Vùng layout": layout, "Kho tiếng động": sfx,
        "Bản trước": ctx.json("edit_plan.json") if ctx.ep.file("edit_plan.json").exists() else "chưa có",
        "Cần sửa": ctx.feedback("plan")}
    write_json(ctx.ep.file("edit_plan.json"), agents.run(ctx.cfg, ctx.ep, "claude", "plan", ctx_data, "edit_plan"))


def simple_plan(ctx):
    """Plan tất định (dry): mỗi ảnh của đoạn một cảnh (không dùng lại ảnh), tiếng động ở đầu mỗi đoạn."""
    segments = ctx.json("audio/segments.json")
    assets = [a for a in ctx.json("assets.json")["items"] if a["kind"] != "cutout"]
    scenes, last_sfx = [], -9.0
    motions = ["ken-burns", "zoom-in", "pan-left", "zoom-out", "pan-right"]
    for seg in segments:
        own = [a for a in assets if a["segment"] == seg["segment"]]
        count = len(own)
        step = (seg["end"] - seg["start"]) / count
        for i in range(count):
            start = round(seg["start"] + i * step, 3)
            sfx = ("sting-01" if start == 0 else "whoosh-01") if i == 0 and start - last_sfx >= 1.5 else None
            last_sfx = start if sfx else last_sfx
            scenes.append({"start": start, "end": round(seg["start"] + (i + 1) * step, 3), "segment": seg["segment"],
                           "asset": own[i % len(own)]["id"], "motion": motions[len(scenes) % len(motions)],
                           "headline": None, "highlight_words": [], "sfx": sfx})
    scenes[0]["start"] = 0.0
    return {"template": "default", "fps": ctx.cfg.video["fps"], "duration": scenes[-1]["end"], "scenes": scenes,
            "music": None}


def check_plan(ctx):
    sfx_index = json.loads((ROOT / "assets/sfx/index.json").read_text(encoding="utf-8"))
    seconds = checks.duration(ctx.ep.file("audio/voice.mp3"), ctx.cfg.bin("ffprobe"))
    return checks.validate_plan(ctx.json("edit_plan.json"), ctx.json("audio/segments.json"), ctx.json("assets.json"),
                                sfx_index, seconds)


# --- 8. Render ----------------------------------------------------------------

def run_render(ctx):
    out = ctx.ep.file("render/final.mp4")
    if ctx.cfg.dry and os.environ.get("NEWS_DRY_RENDER") == "ffmpeg":  # test nhanh, không dùng Remotion
        video = ctx.cfg.video
        ctx.sh(ctx.cfg.bin("ffmpeg"), "-y", "-v", "error", "-f", "lavfi",
               "-i", f"color=c=0x102030:s={video['width']}x{video['height']}:r={video['fps']}",
               "-i", ctx.ep.file("audio/voice.mp3"), "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-af", "loudnorm=I=-14", out)
        return
    from . import render
    render.render(ctx)


def check_render(ctx):
    return checks.render_check(ctx.ep.file("render/final.mp4"), ctx.cfg.video, ctx.cfg.bin("ffprobe"), ctx.cfg.bin("ffmpeg"))


# --- 9. QC ----------------------------------------------------------------------

def run_qc(ctx):
    target = ctx.ep.file(f"qa/qc_v{next_version(ctx, 'qc')}.json")
    if ctx.cfg.dry:
        shutil.copyfile(FIXTURE / "qc.json", target)
        return
    from . import media
    sheets = media.contact_sheets(ctx)
    script = ctx.json("script.json")
    segments = {s["segment"]: s for s in ctx.json("audio/segments.json")}
    ctx_data = {
        "Khung hình": [{"file": str(path.relative_to(ctx.ep.path)), "giây": stamps} for path, stamps in sheets],
        "Lời theo thời gian": [{"segment": s["id"], "start": segments[s["id"]]["start"], "end": segments[s["id"]]["end"],
                                "show": s["show"]} for s in script["segments"]],
        "Plan": ctx.json("edit_plan.json"), "Template tạm": ctx.ep.state.get("template_temporary", True)}
    write_json(target, agents.run(ctx.cfg, ctx.ep, "claude", "qc", ctx_data, "qc", tools=["Read"]))


def check_qc(ctx):
    qc = read_json(latest(ctx, "qa/qc_v*.json"))
    errors = checks.validate_schema("qc", qc)
    return errors or [f"{i['time']:.1f}s {i['kind']}: {i['problem']} → {i['fix']}" for i in qc["issues"]
                      if i["severity"] == "major"]


# --- 10. Gói + 11. Đăng ---------------------------------------------------------

def run_package(ctx):
    if ctx.cfg.dry:
        return fixture(ctx, "meta.json")
    ctx_data = {"Kịch bản": ctx.json("script.json"), "Nguồn ảnh": ctx.json("assets.json"),
                "Cần sửa": ctx.feedback("package")}
    write_json(ctx.ep.file("meta.json"), agents.run(ctx.cfg, ctx.ep, "claude", "package", ctx_data, "meta"))


def check_package(ctx):
    return checks.validate_schema("meta", ctx.json("meta.json"))


def run_publish(ctx):
    from .outputs import enqueue
    write_json(ctx.ep.file("publish.json"), enqueue(ctx.cfg, ctx.ep))
    brief = ctx.json("brief.json")
    with (ctx.cfg.data_dir / "index.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"episode": ctx.ep.id, "date": time.strftime("%Y-%m-%d"), "dry": ctx.cfg.dry,
                                 "urls": [s["url"] for s in brief["sources"]]}, ensure_ascii=False) + "\n")


STEPS = [
    Step("collect", [], ["inbox.json"], run_collect, check_collect, max_rounds=1),
    Step("pick", ["inbox.json"], ["brief.json"], run_pick, check_pick),
    Step("write", ["brief.json"], ["script.json"], run_write, check_write),
    Step("review", ["script.json"], [], run_review, check_review, retry_to="write"),
    Step("voice", ["script_tts.txt"], ["audio/voice.mp3", "audio/voice.words.json", "audio/segments.json"],
         run_voice, check_voice, retry_to="write", max_rounds=2, paid=True),
    Step("assets", ["script.json"], ["assets.json"], run_assets, check_assets, max_rounds=2),
    Step("plan", ["audio/segments.json", "assets.json"], ["edit_plan.json"], run_plan, check_plan),
    Step("render", ["edit_plan.json"], ["render/final.mp4"], run_render, check_render, max_rounds=1),
    Step("qc", ["render/final.mp4"], [], run_qc, check_qc, retry_to="plan", max_rounds=2),
    Step("package", ["script.json"], ["meta.json"], run_package, check_package, max_rounds=2),
    Step("publish", ["meta.json", "render/final.mp4"], ["publish.json"], run_publish, lambda ctx: [], max_rounds=1),
]
BY_NAME = {s.name: s for s in STEPS}
ORDER = [s.name for s in STEPS]
