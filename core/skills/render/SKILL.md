---
name: render
description: Render Remotion từ edit_plan.json: ảnh → cutout → thẻ chữ/số → template PNG trên cùng → câu hook; nhạc nền + sfx.
---
1. Tự động trong `bin/news run` (bước `render`). Chạy riêng: `bin/news run --resume <tap>` sau khi sửa `edit_plan.json`.
2. `core/news/render.py`: lịch thẻ/cutout theo mốc trigger (`timeline.py`), tiếng động tự gắn (thẻ pop/ding, cutout whoosh/swoosh), zoom tối đa theo độ phân giải ảnh, nhạc nền xoay vòng cân -32 LUFS, gom file vào `render/public/`, render composition `NewsShort` với cổng trống riêng, chuẩn hóa -14 LUFS 2 lượt.
3. Mọi lớp hình nằm trong khung 4:3 của template (`assets/template/layout.json`). Không có phụ đề.
4. Cổng: `checks.render_check`: 1080×1920, 30fps, ≤ 59s, -14 LUFS ±1,5.
5. Máy mới: `bin/bootstrap` chạy `npm ci` trong `core/remotion`.
