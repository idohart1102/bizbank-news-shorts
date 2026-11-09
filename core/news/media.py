"""Ảnh cho từng đoạn và khung hình QC.

Ảnh nền: Codex tìm ứng viên (web) → tải, kiểm (đúng là ảnh, cạnh ngắn ≥ MIN_SIDE, không trùng) → chuẩn hóa JPG.
Thiếu thì lấy og:image của bài nguồn của đoạn; vẫn thiếu thì tạo ảnh AI (ghi rõ kind=ai).
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
from pathlib import Path

from . import agents
from .config import ROOT, ensure_online
from .episode import write_json

MIN_SIDE = 600               # dưới mức này bỏ hẳn
FRAME = (1080, 810)          # khung ảnh 4:3 của template: ảnh "chất lượng cao" phải phủ khung này không cần phóng


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


def gather(ctx):
    cfg, ep = ctx.cfg, ctx.ep
    script = ctx.json("script.json")
    sources = {s["id"]: s for s in script["sources"]}
    segments = [{"segment": s["id"], "role": s["role"], "visual": s["visual"], "show": s["show"],
                 "seconds": None} for s in script["segments"]]
    times = {s["segment"]: s["end"] - s["start"] for s in ctx.json("audio/segments.json")} \
        if ep.file("audio/segments.json").exists() else {}
    people = [{"name": c["name"], "search": c["search"]} for s in script["segments"] for c in s["cutouts"] if c["kind"] == "person"]
    search = agents.run(cfg, ep, "codex", "assets", {
        "Các đoạn": segments, "Nguồn bài báo": [{"url": s["url"], "publisher": s["publisher"]} for s in script["sources"]],
        "Người cần ảnh cutout": people or "không có", "Cần sửa": ctx.feedback("assets")},
        "asset_search", tools=["web_search"], timeout=1200)
    write_json(ep.file("assets/search.json"), search)
    found = {s["segment"]: s for s in search["segments"]}
    items, hashes, log = [], set(), []

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

    for segment in script["segments"]:
        sid = segment["id"]
        want = int(max(1, min(6, -(-times.get(sid, 0) // 3.5))))  # mỗi cảnh một ảnh riêng: ~1 ảnh/3,5 giây
        got = 0
        pool = []  # tải hết ứng viên rồi ưu tiên ảnh phủ được khung 1080x810 (≈ ≥1080p); ảnh nhỏ hơn chỉ để bù
        for candidate in found.get(sid, {}).get("candidates", []):
            try:
                raw = download(candidate["image_url"], referer=candidate["page_url"])
            except Exception as error:
                log.append(f"{sid}: bỏ {candidate['image_url'][:80]}: {error}")
                continue
            probe = ep.file(f"assets/.probe-{sid}.src")
            probe.write_bytes(raw)
            size = probe_image(probe, cfg.bin("ffprobe"))
            probe.unlink(missing_ok=True)
            if size and min(size) >= MIN_SIDE:
                pool.append((not high_res(size), -size[0] * size[1], len(pool), raw, candidate))
        for low, _, _, raw, candidate in sorted(pool, key=lambda item: item[:3]):
            if got >= want:
                break
            if low and len([p for p in pool if not p[0]]) + got >= want:
                break
            if add(raw, sid, candidate["kind"], candidate["page_url"], candidate["credit"], candidate["why"]):
                got += 1
            if low:
                log.append(f"{sid}: dùng ảnh < 1080x810 vì không đủ ảnh lớn ({candidate['image_url'][:70]})")
        for source_id in segment["source_ids"]:  # dự phòng 1: ảnh đại diện bài nguồn của đoạn
            if got >= want or source_id not in sources:
                continue
            image = og_image(sources[source_id]["url"])
            if image:
                try:
                    if add(download(image, referer=sources[source_id]["url"]), sid, "real", sources[source_id]["url"],
                           sources[source_id]["publisher"], "ảnh đại diện bài nguồn"):
                        got += 1
                except Exception as error:
                    log.append(f"{sid}: og:image lỗi: {error}")
        angles = ["", " Close-up detail shot.", " Wide establishing shot.", " Over-the-shoulder view.", " Top-down view."]
        for attempt in range(want - got):  # dự phòng 2: ảnh AI minh họa, mỗi ảnh một góc khác nhau
            prompt = (found.get(sid, {}).get("ai_prompt") or f"Landscape 4:3 documentary-style photo, Vietnam, {segment['visual']}")
            prompt += angles[attempt % len(angles)] + " No text, no logos, no real identifiable people."
            try:
                if add(agents.generate_image(cfg, prompt, size="1536x1024"), sid, "ai", None, "Ảnh minh họa AI", prompt):
                    got += 1
            except Exception as error:
                log.append(f"{sid}: ảnh AI lỗi: {error}")
    gather_cutouts(ctx, script, search, items, log)
    write_json(ep.file("assets.json"), {"items": items})
    (ep.file("logs") / "assets.log").write_text("\n".join(log) + "\n", encoding="utf-8")


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
