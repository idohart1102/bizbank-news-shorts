"""Phụ đề và chữ nhấn: ghép chữ hiển thị (`show`, số dạng chữ số) với mốc thời gian của lời đọc (`say`).

words.json được căn theo `say`; `show` khác `say` ở số/ký hiệu ("một tỷ" ↔ "1 tỷ"), nên ghép từng đoạn
bằng difflib: từ giống nhau lấy đúng mốc, cụm khác nhau chia đều khoảng thời gian của cụm lời đọc tương ứng.
"""
import difflib
import re
import unicodedata

from .checks import syllables

SENTENCE_END = tuple(".!?…")
CLAUSE_END = tuple(",;:")


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
    # Từ chỉ có trong show (ví dụ "/"): nội suy giữa hai từ kề.
    seg_start, seg_end = said[0]["start"], said[-1]["end"]
    for i, value in enumerate(times):
        if value is None:
            left = next((times[k][1] for k in range(i - 1, -1, -1) if times[k]), seg_start)
            right = next((times[k][0] for k in range(i + 1, len(times)) if times[k]), seg_end)
            times[i] = (left, max(left, right))
    return [{"text": t, "start": round(s, 3), "end": round(e, 3)} for t, (s, e) in zip(shown, times)]


def build(script, words, max_chars=26, max_seconds=2.6):
    """Trả (captions, emphasis, words_by_segment)."""
    captions, emphasis, by_segment, index = [], [], {}, 0
    for segment in script["segments"]:
        count = len(syllables(segment["say"]))
        said, index = words[index:index + count], index + count
        shown = show_word_times(segment, said)
        by_segment[segment["id"]] = shown
        glued = phrase_continuations(shown, segment["highlight"])  # không ngắt dòng giữa cụm chữ nhấn
        current = []
        for position, word in enumerate(shown):
            text = " ".join(w["text"] for w in current + [word])
            too_long = len(text) > max_chars or word["end"] - current[0]["start"] > max_seconds if current else False
            if too_long and position in glued and len(text) <= max_chars + 12:
                too_long = False
            if too_long:
                captions.append(current)
                current = []
            current.append(word)
            joined = " ".join(w["text"] for w in current)
            if word["text"].endswith(SENTENCE_END) or (word["text"].endswith(CLAUSE_END) and len(joined) >= max_chars * 0.45):
                captions.append(current)
                current = []
        if current:
            captions.append(current)
        for phrase in segment["highlight"]:
            hit = find_phrase(shown, phrase)
            if hit:
                emphasis.append({"text": phrase, "start": hit[0], "end": round(max(hit[1] + 0.6, hit[0] + 1.4), 3),
                                 "segment": segment["id"]})
    result = []
    for group in captions:
        words_out = [dict(w, text=w["text"].rstrip(",;:") if w is group[-1] else w["text"]) for w in group]
        result.append({"start": group[0]["start"], "end": group[-1]["end"], "words": words_out})
    for current, following in zip(result, result[1:]):  # phụ đề liền mạch, không nháy trống giữa các dòng
        if following["start"] - current["end"] < 0.5:
            current["end"] = following["start"]
    return result, dedupe_emphasis(emphasis), by_segment


def phrase_continuations(shown, phrases):
    """Vị trí các từ thứ 2 trở đi của mỗi cụm chữ nhấn."""
    tokens = [norm(w["text"]) for w in shown]
    glued = set()
    for phrase in phrases:
        target = [norm(t) for t in phrase.split() if norm(t)]
        for i in range(len(tokens) - len(target) + 1):
            if target and tokens[i:i + len(target)] == target:
                glued.update(range(i + 1, i + len(target)))
    return glued


def find_phrase(shown, phrase):
    target = [norm(t) for t in phrase.split() if norm(t)]
    tokens = [norm(w["text"]) for w in shown]
    for i in range(len(tokens) - len(target) + 1):
        if tokens[i:i + len(target)] == target:
            return shown[i]["start"], shown[i + len(target) - 1]["end"]
    return None


def dedupe_emphasis(items):
    """Không cho hai chữ nhấn chồng nhau: cái sau đẩy cái trước kết thúc sớm."""
    items = sorted(items, key=lambda e: e["start"])
    for current, following in zip(items, items[1:]):
        current["end"] = min(current["end"], following["start"])
    return [e for e in items if e["end"] - e["start"] >= 0.5]
