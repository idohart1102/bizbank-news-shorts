"""Render bằng Remotion: dựng props từ edit_plan.json, gom file vào public dir, render, chuẩn hóa âm lượng.

Lớp (cố định): media → chữ nhấn → phụ đề → overlay.png. Chưa có overlay của chủ kênh thì dùng overlay tạm
(assets/template/overlay-temp.png, tự vẽ bằng composition TempOverlay) và layout-temp.json.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

from . import captions
from .config import ROOT
from .episode import read_json, write_json

REMOTION = ROOT / "core" / "remotion"
ENTRY = REMOTION / "src" / "index.jsx"
SFX_TARGET_LUFS = -24.0  # tiếng động nhỏ hơn giọng (-14) khoảng 10 dB


def npx(cfg):
    return [cfg.bin("npx"), "--prefix", str(REMOTION), "remotion"]


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
        run([*npx(cfg), "still", str(ENTRY), "TempOverlay", str(temp_overlay), f"--props={props}", "--image-format=png"])
    return temp_overlay, read_json(temp_layout), True


def run(command, timeout=1800):
    out = subprocess.run([str(c) for c in command], capture_output=True, text=True, timeout=timeout)
    if out.returncode != 0:
        raise RuntimeError(f"{Path(str(command[0])).name} lỗi: {(out.stderr or out.stdout).strip()[-800:]}")
    return out


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

    caps, emphasis, _ = captions.build(script, ctx.json("audio/voice.words.json"))
    scenes = []
    for scene in sorted(plan["scenes"], key=lambda s: s["start"]):
        asset = assets[scene["asset"]]
        src = stage(ep.file(f"assets/{asset['file']}"), f"media/{Path(asset['file']).name}")
        scenes.append({"start": scene["start"], "end": scene["end"], "src": src, "motion": scene["motion"],
                       "headline": scene["headline"], "fit": "contain" if asset["kind"] in ("doc", "chart") else "cover"})
    wanted = {w for s in plan["scenes"] for w in s["highlight_words"]}
    emphasis = [e for e in emphasis if not wanted or e["text"] in wanted] or emphasis
    sfx = []
    for scene in plan["scenes"]:
        if scene["sfx"]:
            item = sfx_index[scene["sfx"]]
            gain = 10 ** ((SFX_TARGET_LUFS - (item["lufs"] or SFX_TARGET_LUFS)) / 20)
            sfx.append({"start": scene["start"], "src": stage(ROOT / "assets/sfx" / item["file"], f"sfx/{item['file']}"),
                        "volume": round(min(gain, 1.0), 3)})
    music = None
    if plan.get("music") and cfg.channel.get("music", {}).get("enabled"):
        music = {"src": stage(ROOT / plan["music"]["file"], "music.mp3"), "volume": 10 ** (plan["music"]["volume_db"] / 20)}
    props = {"fps": cfg.video["fps"], "width": cfg.video["width"], "height": cfg.video["height"],
             "duration": max(plan["duration"], caps[-1]["end"] if caps else 0), "layout": layout,
             "overlay": stage(overlay, "overlay.png"), "voice": stage(ep.file("audio/voice.mp3"), "voice.mp3"),
             "scenes": scenes, "captions": caps, "emphasis": emphasis, "sfx": sfx, "music": music, "style": {}}
    write_json(ep.file("render/props.json"), props)
    return props, public, temporary


def render(ctx):
    props, public, temporary = build_props(ctx)
    raw, final = ctx.ep.file("render/raw.mp4"), ctx.ep.file("render/final.mp4")
    run([*npx(ctx.cfg), "render", str(ENTRY), "NewsShort", str(raw), f"--props={ctx.ep.file('render/props.json')}",
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
