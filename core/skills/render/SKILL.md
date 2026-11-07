---
name: render
description: Render Remotion từ edit_plan.json, template PNG lớp trên cùng, rồi kiểm render.
---
1. `python core/scripts/render.py <tap>` → `render/final.mp4` (thứ tự lớp: media → chữ nhấn → phụ đề → overlay.png).
2. `python core/scripts/render_check.py <tap>`: 1080×1920, 30fps, ≤ 59s, loudness khoảng -14 LUFS.
