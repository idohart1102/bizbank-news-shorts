---
name: gather-assets
description: Tìm ảnh thật/ảnh văn bản cho từng đoạn của script.json, dự phòng ảnh bài nguồn rồi ảnh AI; ghi assets.json.
---
1. Tự động trong `bin/news run` (bước `assets`, `core/news/media.py`, prompt `core/prompts/assets.md`).
2. Codex (9router, có web_search) trả 2–4 ứng viên/đoạn: link ảnh trực tiếp + trang + nguồn. Ưu tiên ảnh thật của sự kiện > ảnh văn bản chính thống > ảnh báo cùng chủ đề.
3. Script tải từng ảnh, kiểm (đúng là ảnh, cạnh ngắn ≥ 600px, không trùng), chuẩn hóa JPG ≤ 1920px. Đoạn > 5s cần 2 ảnh.
4. Thiếu thì lấy og:image của bài nguồn của đoạn; vẫn thiếu thì tạo ảnh AI (`kind: ai`, model `image_model` trong machine.yaml). Ảnh AI không giả làm người/sự kiện có thật.
5. `assets.json`: `id, file, segment, kind (real|doc|chart|ai|card), source_url, credit, width, height, note`. `credit` đưa vào mô tả video.
