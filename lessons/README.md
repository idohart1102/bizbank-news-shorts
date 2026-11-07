# Bài học của hệ thống

Lỗi ở cổng kiểm và góp ý của chủ kênh → sự kiện (local, `<data>/_lessons/`) → Claude chưng cất → ứng viên → luật.

- `rules/<bước>.md`: luật đang áp dụng; prompt của bước tự nạp. Vào Git (là kiến thức hệ thống, chuyển giao được).
- `candidates.yaml`: ứng viên + số lần gặp (bản công khai, không có mã tập). Bản đầy đủ có bằng chứng chỉ ở local.
- Thăng hạng khi gặp ở ≥ 2 tập, hoặc ngay lập tức nếu là góp ý của chủ kênh (`bin/news feedback`).
- Luật phải tổng quát: không link, không tên tập, không nội dung tin. Không được nới luật cứng trong `AGENTS.md`/`docs/decisions.md`.
- Luật kiểm được bằng code thì chuyển thành check trong `core/news/checks.py` rồi bỏ khỏi `rules/`.
