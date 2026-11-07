---
name: write-script
description: Claude viết kịch bản short tin tức theo core/standard/script.md từ brief.md.
---
1. Đọc `brief.md`, `core/standard/script.md`.
2. Ghi `script.json` theo `core/standard/script.md` (đoạn có `say`/`show`/`visual`/`cards`/`cutouts`/`source_ids`, nguồn có `quote`). Không có phụ đề: thông tin quan trọng đi vào thẻ chữ/số; người được nhắc tên và sự vật quan trọng đi vào cutout.
3. Đọc `lessons/rules/write.md`. Đếm âm tiết ≤ 220. Không tự chấm; `lint_script` kiểm tự động.
