---
name: collect-news
description: Codex gom tin 24–48h từ config/sources.yaml cho hộ kinh doanh/SME, gộp tin trùng, xuất inbox.json.
---
1. Đọc `config/sources.yaml`. Ưu tiên theo `group` (danh sách của Sếp): nhóm 1 → 4 → 2 → 3. Nhóm 3 và tier 3 (CafeF, mạng xã hội) chỉ làm tín hiệu, không làm nguồn số liệu.
   Danh sách là ưu tiên, không phải giới hạn: nguồn khác được tham khảo nhưng phải Sếp duyệt (`bin/news sources pending|approve|reject`, lưu ở `config/sources_approved.yaml`). Tin mới nhất được ưu tiên.
2. Mỗi tin: `title, url, source, tier, published_at, summary (2 câu), impact (ai bị ảnh hưởng), score 1–10`.
3. Gộp tin trùng sự kiện, giữ danh sách mọi link nguồn.
4. Ghi `<tap>/inbox.json`, xếp theo score. Không viết kịch bản.
