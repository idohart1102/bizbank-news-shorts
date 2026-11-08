"""Render bằng Remotion: dựng props từ edit_plan.json, gom file vào public dir, render, chuẩn hóa âm lượng.

Lớp (cố định): media → cutout → thẻ chữ/số → overlay.png (template trên cùng). Không có phụ đề. Chưa có overlay của chủ kênh thì dùng overlay tạm
(assets/template/overlay-temp.png, tự vẽ bằng composition TempOverlay) và layout-temp.json.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

from . import timeline
from .config import ROOT
from .episode import read_json, write_json

REMOTION = ROOT / "core" / "remotion"
ENTRY = REMOTION / "src" / "index.jsx"
SFX_TARGET_LUFS = -24.0  # tiếng động nhỏ hơn giọng (-14) khoảng 10 dB
CARD_SFX = ["pop-01", "ding-02", "pop-03"]          # thẻ chữ/số xuất hiện
CUTOUT_SFX = ["swoosh-01", "whoosh-04", "swoosh-02"]  # cutout trượt vào


def npx(cfg):
    """CLI Remotion của repo, kèm cổng trống riêng: dự án Remotion khác đang giữ cổng mặc định (3000)
    thì trình duyệt render sẽ nạp nhầm bundle của dự án đó."""
    return [str(REMOTION / "node_modules" / ".bin" / "remotion"), f"--port={free_port()}"]


def free_port():
    import socket
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def template(cfg, name="default"):
    """Trả (overlay_png, layout) cho mẫu `name`; thiếu overlay thật thì dùng overlay tạm."""
    folder = ROOT / "assets" / "template"
    suffix = "" if name == "default" else f"-{name}"
    overlay, layout = folder / f"overlay{suffix}.png", folder / f"layout{suffix}.json"
    if overlay.exists() and layout.exists():
        return overlay, read_json(layout), False
    temp_overlay, temp_layout = folder / "overlay-temp.png", folder / "layout-temp.json"
    if not temp_overlay.exists():
        props = json.dumps({"layout": read_json(temp_layout), "title": cfg.channel.get("display_name", "BẢN TIN KINH DOANH")})
        run([*npx(cfg)[:1], "still", str(ENTRY), *npx(cfg)[1:], "TempOverlay", str(temp_overlay), f"--props={props}", "--image-format=png"])
    return temp_overlay, read_json(temp_layout), True


def run(command, timeout=1800):
    out = subprocess.run([str(c) for c in command], capture_output=True, text=True, timeout=timeout)
    if out.returncode != 0:
        raise RuntimeError(f"{Path(str(command[0])).name} lỗi: {(out.stderr or out.stdout).strip()[-800:]}")
    return out


def pick_music(cfg, ep, stage):
    """Nhạc nền nhỏ xuyên suốt: chọn xoay vòng theo mã tập (cùng tập luôn cùng bài), cân về music.lufs."""
    conf = cfg.channel.get("music", {})
    if not conf.get("enabled"):
        return None
    library = ROOT / conf.get("library", "assets/music")
    index = read_json(library / "index.json")
    if not index:
        return None
    import hashlib
    keys = sorted(index)
    track = index[keys[int(hashlib.sha1(ep.id.encode()).hexdigest(), 16) % len(keys)]]
    gain = 10 ** ((conf.get("lufs", -32) - (track["lufs"] or -14)) / 20)
    ep.state["music"] = track["file"]
    return {"src": stage(library / track["file"], f"music-{track['file']}"), "volume": round(min(gain, 1.0), 4),
            "fade_in": conf.get("fade_in_s", 0.8), "fade_out": conf.get("fade_out_s", 1.5)}


MAX_ZOOM, LOW_RES_ZOOM = 1.15, 1.04


def zoom_limit(asset, box, fit):
    """Mức phóng tối đa của chuyển động: vừa đủ để ảnh không bị vỡ.
    Ảnh lớn hơn khung: phóng tới khi 1 điểm ảnh gốc = 1 điểm video (tối đa 1,15). Ảnh nhỏ hơn khung: chỉ 1,04."""
    w, h = asset["width"], asset["height"]
    fill = max(box["w"] / w, box["h"] / h) if fit == "cover" else min(box["w"] / w, box["h"] / h)
    if fill >= 1.0:
        return LOW_RES_ZOOM
    return round(max(1.0, min(MAX_ZOOM, 1.0 / fill)), 3)


def build_props(ctx):
    """Dựng props + thư mục public cho Remotion. Trả (props, public_dir, dùng_template_tạm)."""
    cfg, ep = ctx.cfg, ctx.ep
    plan, script = ctx.json("edit_plan.json"), ctx.json("script.json")
    assets = {a["id"]: a for a in ctx.json("assets.json")["items"]}
    sfx_index = read_json(ROOT / "assets" / "sfx" / "index.json")
    overlay, layout, temporary = template(cfg, plan.get("template") or "default")
    public = ep.file("render/public")
    if public.exists():
        shutil.rmtree(public)
    (public / "media").mkdir(parents=True)
    (public / "sfx").mkdir()

    def stage(source, relative):
        target = public / relative
        if not target.exists():
            shutil.copyfile(source, target)
        return relative

    audio_end = plan["duration"]
    cards, cutouts = timeline.events(script, ctx.json("audio/voice.words.json"), audio_end)
    cut_files = {a["note"]: a for a in assets.values() if a["kind"] == "cutout"}
    staged_cutouts = []
    for i, item in enumerate(c for c in cutouts if c["name"] in cut_files):
        asset = cut_files[item["name"]]
        staged_cutouts.append({**item, "src": stage(ep.file(f"assets/{asset['file']}"), f"media/{asset['file']}"),
                               "side": "right" if i % 2 == 0 else "left", "ratio": asset["width"] / asset["height"],
                               "sfx": CUTOUT_SFX[i % len(CUTOUT_SFX)]})
    for i, card in enumerate(cards):
        card["sfx"] = CARD_SFX[i % len(CARD_SFX)]
        beside = [c for c in staged_cutouts if c["start"] < card["end"] and card["start"] < c["end"]]
        card["align"] = ("left" if beside[0]["side"] == "right" else "right") if beside else "center"
    scenes = []
    for scene in sorted(plan["scenes"], key=lambda s: s["start"]):
        asset = assets[scene["asset"]]
        src = stage(ep.file(f"assets/{asset['file']}"), f"media/{Path(asset['file']).name}")
        fit = "contain" if asset["kind"] in ("doc", "chart") else "cover"
        scenes.append({"start": scene["start"], "end": scene["end"], "src": src, "motion": scene["motion"], "fit": fit,
                       "zoom_max": zoom_limit(asset, layout["media"], fit)})

    def sound(sfx_id, start):
        item = sfx_index[sfx_id]
        gain = 10 ** ((SFX_TARGET_LUFS - (item["lufs"] or SFX_TARGET_LUFS)) / 20)
        return {"start": round(start, 3), "src": stage(ROOT / "assets/sfx" / item["file"], f"sfx/{item['file']}"),
                "volume": round(min(gain, 1.0), 3)}

    for card in cards:  # Sếp 2026-11-08: thẻ không kéo sang cảnh sau
        scene = next((s for s in scenes if s["start"] <= card["start"] < s["end"]), None)
        if scene:
            card["end"] = round(min(card["end"], scene["end"]), 3)
    event_sounds = [sound(e["sfx"], e["start"]) for e in cards + staged_cutouts]
    busy = [s["start"] for s in event_sounds]
    scene_sounds = [sound(s["sfx"], s["start"]) for s in plan["scenes"]  # tiếng chuyển cảnh trùng lúc thẻ/cutout thì bỏ
                    if s["sfx"] and all(abs(s["start"] - t) >= 1.0 for t in busy)]
    sfx = sorted(event_sounds + scene_sounds, key=lambda s: s["start"])
    music = pick_music(cfg, ep, stage)
    props = {"fps": cfg.video["fps"], "width": cfg.video["width"], "height": cfg.video["height"],
             "duration": plan["duration"], "layout": layout,
             "overlay": stage(overlay, "overlay.png"), "voice": stage(ep.file("audio/voice.mp3"), "voice.mp3"),
             "scenes": scenes, "cards": cards, "cutouts": staged_cutouts, "sfx": sfx, "music": music,
             "hook": script.get("hook_text"),
             "style": layout.get("brand", {})}
    write_json(ep.file("render/props.json"), props)
    return props, public, temporary


def render(ctx):
    props, public, temporary = build_props(ctx)
    raw, final = ctx.ep.file("render/raw.mp4"), ctx.ep.file("render/final.mp4")
    run([*npx(ctx.cfg)[:1], "render", str(ENTRY), "NewsShort", str(raw), *npx(ctx.cfg)[1:], f"--props={ctx.ep.file('render/props.json')}",
         f"--public-dir={public}", "--codec=h264", "--crf=18", "--audio-bitrate=192k", "--log=error"], timeout=3600)
    normalize_loudness(ctx.cfg, raw, final)
    raw.unlink(missing_ok=True)
    ctx.ep.state["template_temporary"] = temporary
    return final


def normalize_loudness(cfg, source, target, lufs=-14.0):
    """loudnorm 2 lượt: đo rồi chỉnh tuyến tính, video giữ nguyên (copy)."""
    probe = run([cfg.bin("ffmpeg"), "-hide_banner", "-nostats", "-i", source, "-af",
                 f"loudnorm=I={lufs}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    measured = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", probe.stderr).group(0))
    af = (f"loudnorm=I={lufs}:TP=-1.5:LRA=11:measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
          f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
          f"offset={measured['target_offset']}:linear=true")
    run([cfg.bin("ffmpeg"), "-y", "-v", "error", "-i", source, "-c:v", "copy", "-af", af, "-ar", "48000",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", target])
