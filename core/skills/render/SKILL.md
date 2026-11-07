---
name: render
description: Render Remotion từ edit_plan.json, template PNG lớp trên cùng, rồi kiểm render.
---
1. Tự động trong `bin/news run` (bước `render`). Chạy riêng: `bin/news run --resume <tap>` sau khi sửa `edit_plan.json`.
2. `core/news/render.py`: dựng `render/props.json` (cảnh, phụ đề karaoke từ `show` + mốc lời đọc, chữ nhấn, sfx đã cân âm lượng), gom file vào `render/public/`, `remotion render` composition `NewsShort` (`core/remotion`), rồi chuẩn hóa -14 LUFS 2 lượt → `render/final.mp4`.
3. Cổng: `checks.render_check`: 1080×1920, 30fps, ≤ 59s, -14 LUFS ±1,5.
4. Máy mới: `bin/bootstrap` chạy `npm ci` trong `core/remotion` (Remotion, React, font ghim version).
