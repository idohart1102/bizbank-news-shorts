---
name: plan-edit
description: Claude lên edit_plan.json (đoạn, mốc thời gian theo srt, hình, hiệu ứng, chữ nhấn, tiếng động) để Remotion dựng.
---
1. Đọc `script.json`, `audio/segments.json`, `audio/voice.words.json`, `assets.json`, `assets/template/layout.json`, `assets/sfx/index.json`, `lessons/rules/plan.md`.
2. Mỗi cảnh 1,5–4s, mỗi ảnh nền đúng một cảnh: `{start, end, segment, asset, motion, headline: null, highlight_words: [], sfx}`. Thẻ chữ/số và cutout do hệ thống tự hiện theo `script.json` (có tiếng động riêng).
3. Chuyển đoạn lớn (giữa các tin) có `sfx: whoosh`; số liệu nhấn có `sfx: pop`. Không quá 1 sfx / 1.5s.
4. Chạy `python core/scripts/validate_plan.py <tap>`.
