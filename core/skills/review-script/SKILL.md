---
name: review-script
description: Duyệt kịch bản ở phiên Claude mới, Codex đối chiếu fact với nguồn; tối đa 3 vòng.
---
1. Codex: mở từng link trong `sources.md`, so số liệu/ngày/đối tượng áp dụng, ghi sai lệch.
2. Claude (phiên mới, không đọc quá trình viết) chấm 10 điểm: hook (2), đúng fact (3), dễ hiểu với chủ shop (2), nhịp ≤60s (2), lời kêu gọi (1).
3. Ghi `qa/script_vN.md`. Đạt khi ≥ 8 và 0 fact sai; chưa đạt thì trả writer sửa.
