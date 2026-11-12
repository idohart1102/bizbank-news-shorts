"""Ảnh cho từng đoạn và khung hình QC.

Ảnh nền: Codex tìm ứng viên (web, song song từng đoạn, chấm `relevance` 0–10 theo lời đọc) → bỏ ảnh < MIN_RELEVANCE
→ tải, kiểm (đúng là ảnh, cạnh ngắn ≥ MIN_SIDE, không trùng) → chuẩn hóa JPG.
Đoạn còn thiếu ảnh thì tìm bù một lượt, rồi og:image của bài nguồn, rồi ảnh AI (ghi rõ kind=ai).
Cutout (kind=cutout, PNG trong suốt):
- người được nhắc tên: ảnh báo chí thật → tách nền (Apple Vision, giữ người lớn nhất). Không dùng AI vẽ người thật.
- sự vật: AI tạo PNG nền trong suốt; dự phòng ảnh thật → tách nền.
"""
import hashlib
import json
import platform
import re
import shutil
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import agents
from .config import ROOT, ensure_online
from .episode import write_json

MIN_SIDE = 600               # dưới mức này bỏ hẳn
MIN_RELEVANCE = 6            # ảnh khớp lời dưới mức này dễ gây hiểu sai (QC bắt lỗi nặng), bỏ trước khi plan
SEARCH_WORKERS = 3           # số lượt Codex tìm ảnh chạy song song
FRAME = (1080, 810)          # khung ảnh 4:3 của template: ảnh "chất lượng cao" phải phủ khung này không cần phóng


# Đoạn đường dẫn ảnh thu nhỏ của CDN báo Việt (thumb_w/640/, thumb/w_1000/, w1280/…): bỏ đi thường ra ảnh gốc lớn.
THUMB = re.compile(r"/(?:thumb_w|thumb_h|resize|crop)/[^/]+/|/thumb/w_\d+/|/w\d{3,4}/|/zoom/\d+_\d+/")


def original_url(url):
    return THUMB.sub("/", url, count=1)


def high_res(size):
    return size[0] >= FRAME[0] and size[1] >= FRAME[1]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def download(url, referer=None, limit=15_000_000):
    ensure_online(f"tải ảnh {url}")
    headers = {"User-Agent": UA, "Accept": "image/avif,image/webp,image/*,*/*;q=0.8"}
    if referer:
        headers["Referer"] = referer
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        return response.read(limit)


def probe_image(path, ffprobe="ffprobe"):
    out = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "json", str(path)], capture_output=True, text=True)
    streams = json.loads(out.stdout or "{}").get("streams") or []
    return (streams[0]["width"], streams[0]["height"]) if streams else None


def normalize(raw, target, ffmpeg="ffmpeg", ffprobe="ffprobe"):
    """Ghi raw ra target (.jpg), thu nhỏ cạnh dài ≤ 1920. Trả (w, h) hoặc None nếu không phải ảnh hợp lệ."""
    temporary = target.with_suffix(".src")
    temporary.write_bytes(raw)
    try:
        size = probe_image(temporary, ffprobe)
        if not size or min(size) < MIN_SIDE:
            return None
        subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(temporary), "-frames:v", "1", "-vf",
                        "scale='if(gt(iw,ih),min(1920,iw),-2)':'if(gt(iw,ih),-2,min(1920,ih))'", "-q:v", "3", str(target)],
                       check=True, capture_output=True)
        return probe_image(target, ffprobe)
    except subprocess.CalledProcessError:
        return None
    finally:
        temporary.unlink(missing_ok=True)


def cutout_tool():
    """Công cụ tách nền: Apple Vision (macOS, biên dịch từ core/tools/cutout.swift một lần). Máy khác: None."""
    binary, source = ROOT / ".cache" / "bin" / "cutout", ROOT / "core" / "tools" / "cutout.swift"
    if platform.system() != "Darwin" or int(platform.mac_ver()[0].split(".")[0] or 0) < 14 or not shutil.which("swiftc"):
        return None
    if not binary.exists() or binary.stat().st_mtime < source.stat().st_mtime:
        binary.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["swiftc", "-O", str(source), "-o", str(binary)], check=True, capture_output=True)
    return binary


def remove_background(raw, target, largest):
    """Ghi PNG trong suốt đã tách nền; trả (w, h) hoặc None."""
    tool = cutout_tool()
    if not tool:
        return None
    source = target.with_suffix(".src")
    source.write_bytes(raw)
    try:
        out = subprocess.run([str(tool), str(source), str(target)] + (["--largest"] if largest else []),
                             capture_output=True, text=True, timeout=120)
        if out.returncode != 0 or not target.exists():
            return None
        size = probe_image(target)
        return size if size and size[1] >= 300 else None
    finally:
        source.unlink(missing_ok=True)


def has_alpha(path, ffprobe="ffprobe"):
    out = subprocess.run([ffprobe, "-v", "error", "-show_entries", "stream=pix_fmt", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True)
    return "a" in out.stdout.strip().replace("gray", "")


def gather_cutouts(ctx, script, search, items, log):
    cfg, ep = ctx.cfg, ctx.ep
    found = {c["name"]: c["candidates"] for c in search.get("cutouts", [])}
    done = set()
    for segment in script["segments"]:
        for cutout in segment["cutouts"]:
            if cutout["name"] in done:
                continue
            done.add(cutout["name"])
            target = ep.file(f"assets/cut-{len(done)}.png")
            size, source_url, credit = None, None, None
            if cutout["kind"] == "object":
                try:
                    raw = agents.generate_image(cfg, f"{cutout['search']}. Single isolated object, product photo style, "
                                                     "transparent background, no text, no logo.", size="1024x1024", transparent=True)
                    target.write_bytes(raw)
                    if has_alpha(target, cfg.bin("ffprobe")):
                        size, credit = probe_image(target, cfg.bin("ffprobe")), "Ảnh minh họa AI"
                    else:
                        size = remove_background(raw, target, largest=True)
                        credit = "Ảnh minh họa AI" if size else None
                except Exception as error:
                    log.append(f"cutout {cutout['name']}: AI lỗi: {error}")
            for candidate in found.get(cutout["name"], []) if not size else []:
                try:
                    raw = download(candidate["image_url"], referer=candidate["page_url"])
                except Exception as error:
                    log.append(f"cutout {cutout['name']}: bỏ {candidate['image_url'][:80]}: {error}")
                    continue
                size = remove_background(raw, target, largest=True)
                if size:
                    source_url, credit = candidate["page_url"], candidate["credit"]
                    break
            if not size:
                log.append(f"cutout {cutout['name']}: không có ảnh dùng được, bỏ qua")
                target.unlink(missing_ok=True)
                continue
            items.append({"id": target.stem, "file": target.name, "segment": segment["id"], "kind": "cutout",
                          "source_url": source_url, "credit": credit, "width": size[0], "height": size[1],
                          "note": cutout["name"]})


def og_image(url):
    try:
        page = download(url, limit=2_000_000).decode("utf-8", "replace")
    except Exception:
        return None
    match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', page, re.I) or \
        re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', page, re.I)
    return match.group(1) if match else None


def search_segments(ctx, segments, people, feedback, label):
    """Một lượt Codex tìm ảnh cho vài đoạn; lỗi thì trả kết quả rỗng để đoạn đó rơi xuống dự phòng."""
    script = ctx.json("script.json")
    context = {"Các đoạn": segments, "Nguồn bài báo": [{"url": s["url"], "publisher": s["publisher"]} for s in script["sources"]],
               "Người cần ảnh cutout": people or "không có", "Cần sửa": feedback}
    errors = []
    for agentic in (True, False):  # Codex CLI mở trang thật, lấy ảnh gốc; lỗi thì thử router có tìm web
        try:
            return agents.run(ctx.cfg, ctx.ep, "codex", "assets", context, "asset_search", tools=["web_search"],
                              timeout=900, label=label, agentic=agentic)
        except agents.AgentError as error:
            errors.append(str(error)[:200])
    return {"segments": [], "cutouts": [], "error": "; ".join(errors)}


def parallel_search(ctx, jobs):
    """jobs: [(segments, people, feedback, label)] → gộp thành một kết quả asset_search."""
    with ThreadPoolExecutor(max_workers=SEARCH_WORKERS) as pool:
        results = list(pool.map(lambda job: search_segments(ctx, *job), jobs))
    merged = {"segments": [], "cutouts": [], "errors": [r["error"] for r in results if r.get("error")]}
    for result in results:
        merged["segments"] += result["segments"]
        merged["cutouts"] += result["cutouts"]
    return merged


def gather(ctx):
    cfg, ep = ctx.cfg, ctx.ep
    script = ctx.json("script.json")
    sources = {s["id"]: s for s in script["sources"]}
    times = {s["segment"]: s["end"] - s["start"] for s in ctx.json("audio/segments.json")} \
        if ep.file("audio/segments.json").exists() else {}
    segments = [{"segment": s["id"], "role": s["role"], "visual": s["visual"], "show": s["show"],
                 "seconds": round(times[s["id"]], 1) if s["id"] in times else None} for s in script["segments"]]
    people = [{"name": c["name"], "search": c["search"]} for s in script["segments"] for c in s["cutouts"] if c["kind"] == "person"]
    feedback = ctx.feedback("assets")
    # Mỗi đoạn một lượt Codex chạy song song (một lượt cho cả video mất 10–15 phút); người cutout đi cùng đoạn đầu.
    search = parallel_search(ctx, [([seg], people if i == 0 else [], feedback, seg["segment"])
                                   for i, seg in enumerate(segments)])
    if search["errors"] and not search["segments"]:
        raise agents.AgentError("Codex không tìm được ảnh: " + "; ".join(search["errors"])[:500])
    found = {}
    for entry in search["segments"]:
        found.setdefault(entry["segment"], {"candidates": [], "ai_prompt": entry["ai_prompt"]})["candidates"] += entry["candidates"]
    items, hashes, log = [], set(), []
    want = {s["id"]: int(max(1, min(6, -(-times.get(s["id"], 0) // 3.5)))) for s in script["segments"]}  # ~1 ảnh/3,5 giây
    tried = set()

    def add(raw, segment, kind, source_url, credit, note):
        digest = hashlib.sha1(raw).hexdigest()[:12]
        if digest in hashes:
            return False
        target = ep.file(f"assets/{segment}-{len([i for i in items if i['segment'] == segment]) + 1}.jpg")
        size = normalize(raw, target, cfg.bin("ffmpeg"), cfg.bin("ffprobe"))
        if not size:
            return False
        hashes.add(digest)
        items.append({"id": target.stem, "file": target.name, "segment": segment, "kind": kind, "source_url": source_url,
                      "credit": credit, "width": size[0], "height": size[1], "note": note[:200]})
        return True

    def got(sid):
        return len([i for i in items if i["segment"] == sid])

    def take(sid, candidates):
        """Tải ứng viên đủ liên quan, ưu tiên ảnh liên quan hơn rồi ảnh phủ được khung 1080x810."""
        pool = []
        for candidate in candidates:
            if candidate["image_url"] in tried:
                continue
            tried.add(candidate["image_url"])
            if candidate.get("relevance", 0) < MIN_RELEVANCE:
                log.append(f"{sid}: bỏ ảnh liên quan thấp ({candidate.get('relevance')}/10: {candidate.get('subject', '')[:60]})")
                continue
            raw, size = None, None
            for url in dict.fromkeys([original_url(candidate["image_url"]), candidate["image_url"]]):  # ảnh gốc trước
                try:
                    raw = download(url, referer=candidate["page_url"])
                except Exception as error:
                    log.append(f"{sid}: bỏ {url[:80]}: {error}")
                    continue
                probe = ep.file(f"assets/.probe-{sid}.src")
                probe.write_bytes(raw)
                size = probe_image(probe, cfg.bin("ffprobe"))
                probe.unlink(missing_ok=True)
                if size and min(size) >= MIN_SIDE:
                    break
                log.append(f"{sid}: bỏ ảnh nhỏ {size} {url[:70]}")
                raw, size = None, None
            if raw:
                pool.append((not high_res(size), -candidate["relevance"], -size[0] * size[1], len(pool), raw, candidate))
        for low, _, _, _, raw, candidate in sorted(pool, key=lambda item: item[:4]):
            if got(sid) >= want[sid]:
                break
            if low and len([p for p in pool if not p[0]]) + got(sid) >= want[sid]:
                break
            note = f"[liên quan {candidate['relevance']}/10] {candidate.get('subject', '')}. {candidate.get('why', '')}"
            if add(raw, sid, candidate["kind"], candidate["page_url"], candidate["credit"], note) and low:
                log.append(f"{sid}: dùng ảnh < 1080x810 vì không đủ ảnh lớn ({candidate['image_url'][:70]})")

    for segment in script["segments"]:
        take(segment["id"], found.get(segment["id"], {}).get("candidates", []))
    # Tìm bù một lượt cho đoạn còn thiếu ảnh đủ liên quan, trước khi dùng ảnh đại diện bài nguồn hay ảnh AI.
    short = [seg for seg in segments if seg["role"] != "cta" and got(seg["segment"]) < want[seg["segment"]]]
    if short:
        extra = parallel_search(ctx, [([seg], [], [
            f"Đoạn {seg['segment']} mới có {got(seg['segment'])}/{want[seg['segment']]} ảnh đủ liên quan (≥ {MIN_RELEVANCE}/10). "
            "Tìm thêm ảnh khác, khớp đúng sự vật trong lời đọc; không trả lại ảnh cũ."], f"{seg['segment']}-bu")
            for seg in short])
        for entry in extra["segments"]:
            if entry["segment"] in want:
                take(entry["segment"], entry["candidates"])
        log += [f"tìm bù lỗi: {e}" for e in extra["errors"]]
    for segment in script["segments"]:
        sid = segment["id"]
        for source_id in segment["source_ids"]:  # dự phòng 1: ảnh đại diện bài nguồn của đoạn
            if got(sid) >= want[sid] or source_id not in sources:
                continue
            image = og_image(sources[source_id]["url"])
            if image:
                try:
                    add(download(image, referer=sources[source_id]["url"]), sid, "real", sources[source_id]["url"],
                        sources[source_id]["publisher"], "ảnh đại diện bài nguồn")
                except Exception as error:
                    log.append(f"{sid}: og:image lỗi: {error}")
        angles = ["", " Close-up detail shot.", " Wide establishing shot.", " Over-the-shoulder view.", " Top-down view."]
        for attempt in range(max(0, want[sid] - got(sid))):  # dự phòng 2: ảnh AI minh họa, mỗi ảnh một góc khác nhau
            prompt = (found.get(sid, {}).get("ai_prompt") or f"Landscape 4:3 documentary-style photo, Vietnam, {segment['visual']}")
            prompt += angles[attempt % len(angles)] + " No text, no logos, no real identifiable people."
            try:
                add(agents.generate_image(cfg, prompt, size="1536x1024"), sid, "ai", None, "Ảnh minh họa AI", prompt)
            except Exception as error:
                log.append(f"{sid}: ảnh AI lỗi: {error}")
    write_json(ep.file("assets/search.json"), search)
    gather_cutouts(ctx, script, search, items, log)
    write_json(ep.file("assets.json"), {"items": items})
    (ep.file("logs") / "assets.log").write_text("\n".join(log) + "\n", encoding="utf-8")


def add_ai_backgrounds(ctx, qc):
    """QC chê ảnh nền lạc đề (major, kind=background): thêm một ảnh AI đúng nội dung cho đoạn của cảnh đó để plan
    có ảnh thay, không phải chờ người tìm ảnh. Trả số ảnh đã thêm."""
    plan, script = ctx.json("edit_plan.json"), ctx.json("script.json")
    visuals = {s["id"]: s["visual"] for s in script["segments"]}
    search = ctx.json("assets/search.json") if ctx.ep.file("assets/search.json").exists() else {"segments": []}
    prompts = {s["segment"]: s["ai_prompt"] for s in search.get("segments", [])}
    assets = ctx.json("assets.json")
    added = 0
    for issue in (i for i in qc["issues"] if i["severity"] == "major" and i["kind"] == "background"):
        scene = next((s for s in plan["scenes"] if s["start"] <= issue["time"] < s["end"]), None)
        if not scene:
            continue
        sid = scene["segment"]
        prompt = (prompts.get(sid) or f"Landscape 4:3 documentary-style photo, Vietnam, {visuals.get(sid, '')}")
        prompt += " Close-up of the exact subject being discussed. No text, no logos, no real identifiable people."
        try:
            raw = agents.generate_image(ctx.cfg, prompt, size="1536x1024")
        except Exception:
            continue
        n = len([i for i in assets["items"] if i["segment"] == sid]) + 1
        target = ctx.ep.file(f"assets/{sid}-{n}.jpg")
        size = normalize(raw, target, ctx.cfg.bin("ffmpeg"), ctx.cfg.bin("ffprobe"))
        if not size:
            continue
        assets["items"].append({"id": target.stem, "file": target.name, "segment": sid, "kind": "ai", "source_url": None,
                                "credit": "Ảnh minh họa AI", "width": size[0], "height": size[1],
                                "note": f"[liên quan 8/10] Ảnh AI thay ảnh QC chê lạc đề ở cảnh {scene['start']}s. {prompt}"[:200]})
        added += 1
    if added:
        write_json(ctx.ep.file("assets.json"), assets)
    return added


def contact_sheets(ctx, every=1.0, columns=4, rows=3):
    """Trích khung mỗi `every` giây, ghép lưới columns×rows. Trả [(file, [mốc giây])]."""
    cfg, ep = ctx.cfg, ctx.ep
    video = ep.file("render/final.mp4")
    seconds = float(json.loads(subprocess.run([cfg.bin("ffprobe"), "-v", "error", "-show_entries", "format=duration",
                                               "-of", "json", str(video)], capture_output=True, text=True).stdout)["format"]["duration"])
    stamps = [round(every * i + 0.5, 2) for i in range(int(seconds / every)) if every * i + 0.5 < seconds]
    folder = ep.file("qa/frames")
    folder.mkdir(parents=True, exist_ok=True)
    per = columns * rows
    sheets = []
    for start in range(0, len(stamps), per):
        chunk = stamps[start:start + per]
        target = folder / f"sheet-{start // per + 1}.jpg"
        select = "+".join(f"eq(n\\,{round(t * cfg.video['fps'])})" for t in chunk)
        subprocess.run([cfg.bin("ffmpeg"), "-y", "-v", "error", "-i", str(video), "-vf",
                        f"select='{select}',scale=360:640,tile={columns}x{rows}", "-frames:v", "1", "-fps_mode", "passthrough", str(target)],
                       check=True, capture_output=True)
        sheets.append((target, chunk))
    return sheets
