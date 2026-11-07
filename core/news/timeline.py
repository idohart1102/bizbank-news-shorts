"""Lịch xuất hiện thẻ chữ/số và cutout theo mốc lời đọc. Không làm phụ đề (Sếp 2026-11-08).

words.json căn theo `say` (số bằng chữ); trigger nằm trong `show` (số dạng chữ số). Ghép từng đoạn bằng
difflib: từ giống nhau lấy đúng mốc, cụm khác nhau ("một tỷ" ↔ "1 tỷ") chia đều khoảng của cụm lời đọc.
"""
import difflib
import unicodedata

from .checks import syllables

CARD_SECONDS, CUTOUT_SECONDS, MIN_SECONDS = 2.6, 3.2, 1.0


def norm(token):
    return "".join(c for c in unicodedata.normalize("NFC", token.lower()) if c.isalnum())


def show_word_times(segment, said):
    """said: các từ (có start/end) của lời đọc đoạn này. Trả list {text,start,end} theo show."""
    shown = [t for t in unicodedata.normalize("NFC", segment["show"]).split() if t.strip()]
    a, b = [norm(t) for t in shown], [norm(w["text"]) for w in said]
    times = [None] * len(shown)
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = (said[j1 + k]["start"], said[j1 + k]["end"])
        elif op == "replace":
            start, end = said[j1]["start"], said[j2 - 1]["end"]
            for k, i in enumerate(range(i1, i2)):
                times[i] = (start + (end - start) * k / (i2 - i1), start + (end - start) * (k + 1) / (i2 - i1))
    seg_start, seg_end = said[0]["start"], said[-1]["end"]
    for i, value in enumerate(times):
        if value is None:  # từ chỉ có trong show (ví dụ "/"): nội suy giữa hai từ kề
            left = next((times[k][1] for k in range(i - 1, -1, -1) if times[k]), seg_start)
            right = next((times[k][0] for k in range(i + 1, len(times)) if times[k]), seg_end)
            times[i] = (left, max(left, right))
    return [{"text": t, "start": round(s, 3), "end": round(e, 3)} for t, (s, e) in zip(shown, times)]


def find_phrase(shown, phrase):
    target = [norm(t) for t in phrase.split() if norm(t)]
    tokens = [norm(w["text"]) for w in shown]
    for i in range(len(tokens) - len(target) + 1):
        if target and tokens[i:i + len(target)] == target:
            return shown[i]["start"], shown[i + len(target) - 1]["end"]
    return None


def words_by_segment(script, words):
    result, index = {}, 0
    for segment in script["segments"]:
        count = len(syllables(segment["say"]))
        result[segment["id"]] = show_word_times(segment, words[index:index + count])
        index += count
    return result


def events(script, words, audio_end):
    """Trả (cards, cutouts): mỗi mục có start/end (giây), theo lúc trigger được đọc."""
    by_segment = words_by_segment(script, words)
    cards, cutouts = [], []
    for segment in script["segments"]:
        shown = by_segment[segment["id"]]
        for card in segment["cards"]:
            hit = find_phrase(shown, card["trigger"]) or (shown[0]["start"], shown[0]["end"])
            cards.append({**card, "segment": segment["id"], "start": hit[0], "end": hit[0] + CARD_SECONDS})
        for cutout in segment["cutouts"]:
            hit = find_phrase(shown, cutout["trigger"]) or (shown[0]["start"], shown[0]["end"])
            cutouts.append({**cutout, "segment": segment["id"], "start": hit[0], "end": hit[0] + CUTOUT_SECONDS})
    return settle(cards, audio_end), settle(cutouts, audio_end)


def settle(items, audio_end):
    """Cùng một lớp: cái sau xuất hiện thì cái trước kết thúc; bỏ cái quá ngắn; không quá hết audio."""
    items = sorted(items, key=lambda e: e["start"])
    for current, following in zip(items, items[1:]):
        current["end"] = min(current["end"], following["start"])
    out = []
    for item in items:
        item["end"] = round(min(item["end"], audio_end), 3)
        item["start"] = round(item["start"], 3)
        if item["end"] - item["start"] >= MIN_SECONDS:
            out.append(item)
    return out
