"""Cổng kiểm soát tất định. Mỗi hàm trả danh sách lỗi (chuỗi tiếng Việt); rỗng là đạt."""
import json
import re
import subprocess
import unicodedata
from functools import lru_cache
from pathlib import Path

import jsonschema

from .config import ROOT

MAX_SYLLABLES = 220
MAX_SENTENCE_SYLLABLES = 20


@lru_cache(maxsize=None)
def schema(name):
    return json.loads((ROOT / "core" / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))


def validate_schema(name, value):
    validator = jsonschema.Draft202012Validator(schema(name))
    return [f"{name}: {'/'.join(map(str, e.path)) or '(gốc)'}: {e.message}" for e in validator.iter_errors(value)][:20]


def is_word(token):
    return any(c.isalnum() for c in token)


def syllables(text):
    return [t for t in unicodedata.normalize("NFC", text).split() if is_word(t)]


def numbers(text):
    return re.findall(r"\d+(?:[.,]\d+)*", text)


def lint_script(script):
    """Luật của core/standard/script.md có thể kiểm bằng code."""
    errors = validate_schema("script", script)
    if errors:
        return errors
    total = sum(len(syllables(s["say"])) for s in script["segments"])
    if total > MAX_SYLLABLES:
        errors.append(f"Tổng {total} âm tiết, vượt {MAX_SYLLABLES}; cắt bớt {total - MAX_SYLLABLES}")
    source_ids = {s["id"] for s in script["sources"]}
    if sum(len(s["cards"]) for s in script["segments"]) < 3:
        errors.append("Cần ≥ 3 thẻ chữ/số trong cả video (số tiền, ngày, mức %, đối tượng áp dụng)")
    roles = [s["role"] for s in script["segments"]]
    if roles[0] != "hook":
        errors.append("Đoạn đầu phải là hook")
    if "action" not in roles:
        errors.append("Thiếu đoạn action (chủ shop cần làm gì)")
    for segment in script["segments"]:
        sid = segment["id"]
        for sentence in re.split(r"(?<=[.!?…])\s+", segment["say"]):
            count = len(syllables(sentence))
            if count > MAX_SENTENCE_SYLLABLES:
                errors.append(f"{sid}: câu {count} âm tiết (> {MAX_SENTENCE_SYLLABLES}): «{sentence[:60]}…»")
        if numbers(segment["say"]):
            errors.append(f"{sid}: say còn chữ số {numbers(segment['say'])}; TTS cần số viết bằng chữ")
        if len(syllables(segment["show"])) == 0 or not segment["visual"].strip():
            errors.append(f"{sid}: thiếu show hoặc visual")
        if segment["role"] in ("hook", "story", "action") and not segment["source_ids"]:
            errors.append(f"{sid}: đoạn có fact nhưng không có source_ids")
        missing = set(segment["source_ids"]) - source_ids
        if missing:
            errors.append(f"{sid}: source_ids {sorted(missing)} không có trong sources")
        for card in segment["cards"]:
            if len(numbers(card["value"])) > 2:
                errors.append(f"{sid}: thẻ «{card['value']}» nhồi {len(numbers(card['value']))} con số; mỗi thẻ một giá trị (tối đa 2 số cho khoảng)")
        for item in segment["cards"] + segment["cutouts"]:
            if item["trigger"].lower() not in segment["show"].lower():
                errors.append(f"{sid}: trigger «{item['trigger']}» không có nguyên văn trong show")
        if segment["role"] in ("hook", "story", "action") and not (segment["cards"] or segment["cutouts"]):
            errors.append(f"{sid}: đoạn chưa có thẻ chữ/số hay cutout nào (mỗi đoạn tin cần ≥ 1)")
    return errors


def source_rule(sources):
    """Luật cứng: ≥ 2 nguồn độc lập, hoặc 1 nguồn chính thống (tier 1)."""
    if any(s["tier"] == 1 for s in sources):
        return []
    publishers = {s["publisher"].strip().lower() for s in sources if s["tier"] <= 2}
    if len(publishers) >= 2:
        return []
    return [f"Chỉ có {len(publishers)} nguồn báo độc lập (tier ≤ 2), cần 2 hoặc 1 nguồn chính thống"]


def ffprobe(path, ffprobe_bin="ffprobe"):
    out = subprocess.run([ffprobe_bin, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise ValueError(f"ffprobe lỗi: {out.stderr.strip()[:200]}")
    return json.loads(out.stdout)


def duration(path, ffprobe_bin="ffprobe"):
    return float(ffprobe(path, ffprobe_bin)["format"]["duration"])


def loudness(path, ffmpeg_bin="ffmpeg"):
    out = subprocess.run([ffmpeg_bin, "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True)
    found = re.findall(r"I:\s+(-?[\d.]+) LUFS", out.stderr)
    return float(found[-1]) if found else None


def segment_times(script, words):
    """Mốc từng đoạn từ words.json (căn theo script_tts.txt = các say nối nhau)."""
    result, index = [], 0
    for segment in script["segments"]:
        count = len(syllables(segment["say"]))
        chunk = words[index:index + count]
        if not chunk:
            raise ValueError(f"words.json thiếu từ cho đoạn {segment['id']}")
        result.append({"segment": segment["id"], "start": chunk[0]["start"], "end": chunk[-1]["end"]})
        index += count
    if index != len(words):
        raise ValueError(f"Số từ lệch: kịch bản {index}, words.json {len(words)}")
    for current, following in zip(result, result[1:]):  # đoạn kéo tới đầu đoạn sau, không có khoảng trống
        current["end"] = following["start"]
    return result


CARD_HOLD = 1.2  # thẻ cần đứng yên trên một cảnh ít nhất ngần này giây


def validate_plan(plan, segments, assets, sfx_index, audio_seconds, max_static=2.5, cards=()):
    errors = validate_schema("edit_plan", plan)
    if errors:
        return errors
    for card in cards:  # Sếp 2026-11-08: thẻ không kéo sang cảnh sau, nên cảnh phải đủ dài sau lúc thẻ hiện
        scene = next((s for s in plan["scenes"] if s["start"] <= card["start"] < s["end"]), None)
        if scene and scene["end"] - card["start"] < min(CARD_HOLD, card["end"] - card["start"]) - 0.01:
            errors.append(f"Thẻ «{card['value']}» hiện lúc {card['start']:.2f}s nhưng cảnh cắt ở {scene['end']:.2f}s: "
                          f"kéo dài cảnh tới ít nhất {card['start'] + CARD_HOLD:.2f}s (thẻ không được kéo sang cảnh sau)")
    scenes = sorted(plan["scenes"], key=lambda s: s["start"])
    asset_ids = {a["id"] for a in assets["items"] if a["kind"] != "cutout"}  # cutout là lớp riêng, không làm nền
    if scenes[0]["start"] > 0.05:
        errors.append(f"Khoảng trống đầu video 0→{scenes[0]['start']:.2f}s")
    if scenes[-1]["end"] < audio_seconds - 0.05:
        errors.append(f"Cảnh cuối dừng ở {scenes[-1]['end']:.2f}s, audio dài {audio_seconds:.2f}s")
    last_sfx = -9.0
    for previous, scene in zip([None] + scenes, scenes):
        span = f"{scene['start']:.2f}-{scene['end']:.2f}s"
        if previous and abs(scene["start"] - previous["end"]) > 0.05:
            errors.append(f"Hở/chồng giữa {previous['end']:.2f}s và {scene['start']:.2f}s")
        if scene["end"] <= scene["start"]:
            errors.append(f"Cảnh {span} có độ dài ≤ 0")
        if scene["end"] - scene["start"] > max_static and scene["motion"] == "static":
            errors.append(f"Cảnh {span} đứng yên > {max_static}s")
        if scene["end"] - scene["start"] > 4.0:
            errors.append(f"Cảnh {span} dài > 4s, cần tách")
        if scene["headline"] and len(scene["headline"]) > 42:
            errors.append(f"Cảnh {span}: headline dài {len(scene['headline'])} ký tự (> 42)")
        if scene["asset"] not in asset_ids:
            errors.append(f"Cảnh {span}: asset {scene['asset']} không có trong assets.json")
        if scene["sfx"]:
            if scene["sfx"] not in sfx_index:
                errors.append(f"Cảnh {span}: sfx {scene['sfx']} không có trong kho")
            if scene["start"] - last_sfx < 1.5:
                errors.append(f"Cảnh {span}: sfx cách cái trước < 1.5s")
            last_sfx = scene["start"]
    used = {}
    for scene in scenes:
        used.setdefault(scene["asset"], []).append(f"{scene['start']:.1f}s")
    for asset, at in used.items():
        if len(at) > 1:  # Sếp 2026-11-07: không dùng lại ảnh trong một video
            errors.append(f"Ảnh {asset} dùng {len(at)} lần ({', '.join(at)}); mỗi ảnh chỉ một cảnh")
    by_asset = {}
    for scene in scenes:
        by_asset.setdefault((scene["segment"], scene["asset"]), 0.0)
        by_asset[(scene["segment"], scene["asset"])] += scene["end"] - scene["start"]
    for (segment, asset), seconds in by_asset.items():
        others = {a for (s, a) in by_asset if s == segment}
        if seconds > 7 and len([a for a in assets["items"] if a["segment"] == segment and a["kind"] != "cutout"]) > len(others):
            errors.append(f"Đoạn {segment}: ảnh {asset} chiếm {seconds:.1f}s trong khi đoạn còn ảnh chưa dùng")
    with_sfx = {s["segment"] for s in scenes if s["sfx"]}
    for segment in segments[:-1]:  # đoạn cuối (lời kêu gọi) không bắt buộc
        if segment["segment"] not in with_sfx:
            errors.append(f"Đoạn {segment['segment']} không có tiếng động nào (cần ≥ 1: chuyển đoạn hoặc nhấn số)")
    covered = {s["segment"] for s in scenes}
    for segment in segments:
        if segment["segment"] not in covered:
            errors.append(f"Đoạn {segment['segment']} không có cảnh nào")
    return errors


def render_check(path, video, ffprobe_bin="ffprobe", ffmpeg_bin="ffmpeg", target_lufs=-14.0):
    info = ffprobe(path, ffprobe_bin)
    errors = []
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if not v or not a:
        return ["Thiếu luồng video hoặc âm thanh"]
    if (v["width"], v["height"]) != (video["width"], video["height"]):
        errors.append(f"Kích thước {v['width']}x{v['height']}, cần {video['width']}x{video['height']}")
    num, den = map(int, v["r_frame_rate"].split("/"))
    if abs(num / den - video["fps"]) > 0.01:
        errors.append(f"fps {num / den:.2f}, cần {video['fps']}")
    seconds = float(info["format"]["duration"])
    if seconds > video["max_seconds"]:
        errors.append(f"Dài {seconds:.1f}s, tối đa {video['max_seconds']}s")
    lufs = loudness(path, ffmpeg_bin)
    if lufs is None or abs(lufs - target_lufs) > 1.5:
        errors.append(f"Âm lượng {lufs} LUFS, cần {target_lufs} ±1.5")
    return errors
