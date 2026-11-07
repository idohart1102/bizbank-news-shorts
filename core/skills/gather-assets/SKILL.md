---
name: gather-assets
description: Codex tìm ảnh báo/internet, ảnh văn bản, tạo ảnh AI/chart minh họa cho từng {hình} trong script.md.
---
1. Mỗi ghi chú `{hình: ...}` cần ≥ 1 hình, ưu tiên: ảnh thật của sự kiện > ảnh văn bản/website chính thống > chart tự dựng > ảnh AI.
2. Ảnh dọc hoặc đủ lớn để cắt vào vùng `media` trong `assets/template/layout.json`, cạnh ngắn ≥ 1080px nếu có thể.
3. Ghi `assets.json`: `id, file, segment, kind (real|ai|chart|doc), source_url, note`.
4. Ảnh AI không giả làm ảnh thật của người/sự kiện có thật.
