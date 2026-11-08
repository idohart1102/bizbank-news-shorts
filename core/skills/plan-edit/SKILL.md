---
name: plan-edit
description: Claude lên edit_plan.json (cảnh theo mốc lời đọc, ảnh nền không lặp, chuyển động, tiếng chuyển cảnh) để Remotion dựng; thẻ/cutout hệ thống tự hiện.
---
1. Đọc `script.json`, `audio/segments.json`, `audio/voice.words.json`, `assets.json`, `assets/template/layout.json`, `assets/sfx/index.json`, `lessons/rules/plan.md`.
2. Mỗi cảnh 1,5–4s, mỗi ảnh nền đúng một cảnh: `{start, end, segment, asset, motion, headline: null, highlight_words: [], sfx}`. Thẻ chữ/số và cutout do hệ thống tự hiện theo `script.json` (có tiếng động riêng).
3. Chuyển đoạn lớn (giữa các tin) có `sfx: whoosh`; số liệu nhấn có `sfx: pop`. Không quá 1 sfx / 1.5s.
4. Chạy `python core/scripts/validate_plan.py <tap>`.
