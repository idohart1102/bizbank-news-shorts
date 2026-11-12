#!/usr/bin/env python3
"""Căn thời gian phụ đề: ghép chữ gốc của kịch bản với mốc thời gian theo từ của Whisper.

Chạy bằng venv riêng: .venv-align/bin/python -I bin/align.py --audio a.mp3 --text a.txt --out a.srt
Phụ đề dùng đúng chữ trong kịch bản (đúng chính tả, dấu câu); Whisper chỉ cấp mốc thời gian.
Model đọc từ cache Hugging Face, không tải mạng (HF_HUB_OFFLINE=1).
"""
import argparse
import difflib
import json
import os
import runpy
import sys
import unicodedata
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
_config = runpy.run_path(str(Path(__file__).with_name('align_state.py')))
backend = _config['backend']
model_name = _config['model_name']

SENTENCE_END = tuple(".!?…")
CLAUSE_END = tuple(",;:")


def norm(token):
    """Chữ thường, bỏ dấu câu; giữ dấu tiếng Việt vì nó phân biệt từ."""
    return "".join(c for c in unicodedata.normalize("NFC", token.lower()) if c.isalnum())


def split_words(raw):
    words = []
    for word in raw:
        parts = [p for p in word['word'].split() if norm(p)]
        if not parts:
            continue
        step = (word['end'] - word['start']) / len(parts)
        for i, part in enumerate(parts):
            words.append({'text': part, 'start': word['start'] + i * step, 'end': word['start'] + (i + 1) * step})
    return words


def transcribe(audio, prompt):
    # Không dùng prompt dài: có thể làm Whisper lặp ảo với giọng liền mạch.
    if backend() == 'mlx':
        import mlx_whisper
        result = mlx_whisper.transcribe(str(audio), path_or_hf_repo=model_name(), language='vi',
                                       word_timestamps=True, condition_on_previous_text=False, verbose=None)
        raw = [word for segment in result.get('segments', []) for word in segment.get('words', [])]
    elif backend() == 'faster-whisper':
        from faster_whisper import WhisperModel
        model = WhisperModel(model_name(), device='cpu', compute_type='int8', local_files_only=True)
        segments, _ = model.transcribe(str(audio), language='vi', word_timestamps=True, condition_on_previous_text=False)
        raw = [{'word': w.word, 'start': w.start, 'end': w.end} for segment in segments for w in (segment.words or [])]
    else:
        raise SystemExit('TTS_ALIGN_BACKEND phải là mlx hoặc faster-whisper')
    return split_words(raw)


def align(script_tokens, heard):
    a = [norm(t) for t in script_tokens]
    b = [norm(w["text"]) for w in heard]
    times = [None] * len(script_tokens)
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    matched = 0
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = (heard[j1 + k]["start"], heard[j1 + k]["end"])
            matched += i2 - i1
        elif op == "replace":
            # Ví dụ kịch bản "10%" mà Whisper nghe "mười phần trăm": chia đều khoảng thời gian.
            # Whisper hay ghi số đọc bằng chữ thành chữ số ("mười chín nghìn" → "19 .000"): vẫn tính là khớp.
            if any(c.isdigit() for k in range(j1, j2) for c in b[k]):
                matched += i2 - i1
            start, end = heard[j1]["start"], heard[j2 - 1]["end"]
            weights = [max(len(a[i]), 1) for i in range(i1, i2)]
            total, cursor = sum(weights), start
            for i, weight in zip(range(i1, i2), weights):
                span = (end - start) * weight / total
                times[i] = (cursor, cursor + span)
                cursor += span
    fill_gaps(times, heard[-1]["end"] if heard else 0.0)
    return times, matched / max(len(a), 1)


def fill_gaps(times, audio_end):
    i = 0
    while i < len(times):
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(times) and times[j] is None:
            j += 1
        left = times[i - 1][1] if i > 0 else 0.0
        right = times[j][0] if j < len(times) else max(audio_end, left)
        step = max(right - left, 0.0) / (j - i)
        for k in range(i, j):
            times[k] = (left + (k - i) * step, left + (k - i + 1) * step)
        i = j
    previous = 0.0
    for k, (start, end) in enumerate(times):  # bảo đảm tăng dần
        start = max(start, previous)
        times[k] = (start, max(end, start + 0.05))
        previous = times[k][1]


def group(tokens, times, max_chars, max_seconds):
    cues, current = [], []
    for index, token in enumerate(tokens):
        if current:
            text = " ".join(tokens[i] for i in current + [index])
            if len(text) > max_chars or times[index][1] - times[current[0]][0] > max_seconds:
                cues.append(current)
                current = []
        current.append(index)
        length = len(" ".join(tokens[i] for i in current))
        if token.endswith(SENTENCE_END) or (token.endswith(CLAUSE_END) and length >= max_chars * 0.4):
            cues.append(current)
            current = []
    if current:
        cues.append(current)
    result = []
    for cue in cues:
        text = " ".join(tokens[i] for i in cue).rstrip(",;:")
        result.append({"text": text, "start": times[cue[0]][0], "end": times[cue[-1]][1]})
    for current_cue, next_cue in zip(result, result[1:]):  # lấp khoảng nghỉ ngắn cho phụ đề liền mạch
        if next_cue["start"] - current_cue["end"] < 0.4:
            current_cue["end"] = next_cue["start"]
    return result


def stamp(seconds):
    ms = int(round(seconds * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--audio", required=True)
    parser.add_argument("--text", required=True, help="file UTF-8 chứa đúng văn bản đã đọc")
    parser.add_argument("--out", required=True, help="file .srt đầu ra")
    parser.add_argument("--words", help="file .json mốc thời gian từng từ (tùy chọn)")
    parser.add_argument("--max-chars", type=int, default=int(os.environ.get("TTS_ALIGN_MAX_CHARS", "32")))
    parser.add_argument("--max-seconds", type=float, default=2.8)
    parser.add_argument("--min-match", type=float, default=0.85)
    args = parser.parse_args()

    text = unicodedata.normalize("NFC", Path(args.text).read_text(encoding="utf-8"))
    tokens = [t for t in text.split() if norm(t)]
    if not tokens:
        raise SystemExit("Văn bản rỗng")
    heard = transcribe(args.audio, text)
    if not heard:
        raise SystemExit("Whisper không nghe được từ nào")
    longest, run = 1, 1
    for previous, current in zip(heard, heard[1:]):
        run = run + 1 if norm(previous["text"]) == norm(current["text"]) else 1
        longest = max(longest, run)
    if longest >= 5:
        raise SystemExit(f"Whisper lặp ảo ({longest} từ giống nhau liền nhau), không dùng được mốc thời gian")
    times, ratio = align(tokens, heard)
    cues = group(tokens, times, args.max_chars, args.max_seconds)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    srt = "\n".join(f"{n}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}\n" for n, c in enumerate(cues, 1))
    out.with_name(out.name + ".part").write_text(srt, encoding="utf-8")
    out.with_name(out.name + ".part").replace(out)
    if args.words:
        words = [{"text": t, "start": round(s, 3), "end": round(e, 3)} for t, (s, e) in zip(tokens, times)]
        Path(args.words).write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"cues": len(cues), "words": len(tokens), "match": round(ratio, 3)}))
    if ratio < args.min_match:
        print(f"Cảnh báo: chỉ khớp {ratio:.0%} từ, kiểm tra lại văn bản có đúng với audio không", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
