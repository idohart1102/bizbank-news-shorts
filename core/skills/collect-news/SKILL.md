---
name: collect-news
description: Codex gom tin 24–48h từ config/sources.yaml cho hộ kinh doanh/SME, gộp tin trùng, xuất inbox.json.
---
1. Đọc `config/sources.yaml`. Quét tier 1–2 trước, tier 3 chỉ làm tín hiệu xu hướng.
2. Mỗi tin: `title, url, source, tier, published_at, summary (2 câu), impact (ai bị ảnh hưởng), score 1–10`.
3. Gộp tin trùng sự kiện, giữ danh sách mọi link nguồn.
4. Ghi `<tap>/inbox.json`, xếp theo score. Không viết kịch bản.
