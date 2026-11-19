---
name: pick-stories
description: Claude chọn 1 tin chính hoặc 3–4 tin tổng hợp từ inbox.json và viết brief.md.
---
1. Đọc `inbox.json`, `docs/decisions.md`. Bỏ tin chưa đủ 2 nguồn (hoặc 1 nguồn tier 1).
2. Ưu tiên: có hiệu lực/ảnh hưởng tiền bạc trong 30 ngày tới > tin xu hướng. Cân 4 chủ đề kênh theo `weight` trong `config/pillars.yaml`: tin gần ngang điểm thì chọn chủ đề đang thiếu; không chọn tin score < 6 chỉ để đủ tỷ trọng.
3. `brief.json` (`kind` = `news`, `pillar` của tin chính): dạng video (1 tin sâu / tổng hợp), hook, 3 ý chính, "chủ shop cần làm gì", link nguồn, mẫu template.
