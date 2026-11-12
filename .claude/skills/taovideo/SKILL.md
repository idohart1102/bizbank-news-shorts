---
name: taovideo
description: Chạy trọn quy trình làm video short tin tức tới bước cuối (package: tiêu đề, mô tả, hashtag, vào hàng chờ đăng). Có chủ đề rồi (từ /chonchude hoặc Sếp đưa id) thì làm tiếp tin đó; chưa có thì tự gom tin và chọn tin tốt nhất. Dùng khi Sếp gõ /taovideo [id chủ đề], "làm video", "tạo video". Tốn credit Vbee ở bước giọng đọc.
---
# Tạo video

Làm ở thư mục gốc dự án. Trao đổi tiếng Việt, ngắn gọn. Đối số (nếu có) là `id` chủ đề trong `inbox.json`.

## Chạy
- **Có id chủ đề** (Sếp đưa, hoặc vừa chọn ở `/chonchude`): `bin/news run --resume last --story <id>`.
  `last` phải là tập vừa gom ở `/chonchude` (kiểm bằng `bin/news topics last` có id đó). Không có thì báo Sếp, không đoán.
- **Có tập đang dừng giữa chừng** (`bin/news status`: `paused`/`needs_human`) và Sếp muốn làm tiếp: `bin/news run --resume last`.
- **Chưa có chủ đề**: `bin/news run` (tự gom tin, AI chọn tin tốt nhất, chạy hết 10 bước).

Lệnh chạy lâu (gọi AI, TTS, render): chạy nền (`run_in_background`), chờ thông báo xong, không hỏi dồn.

## Đọc kết quả
`bin/news run` in dòng cuối `Trạng thái: ...`.
- `done`: báo Sếp đường dẫn `render/final.mp4` của tập, `hook_text` (trong `script.json`), tiêu đề + hashtag (trong `meta.json`), điểm duyệt kịch bản (`qa/review_v*.json` bản mới nhất). Không đọc `audio/`, `render/`, `assets/` (chỉ đưa đường dẫn).
- `needs_human` vì **nguồn ngoài danh sách**: liệt kê `bin/news sources pending`, hỏi Sếp duyệt hay từ chối từng tên miền, rồi chạy `bin/news sources approve|reject <tên miền>` theo lời Sếp và `bin/news run --resume last`. Không tự duyệt.
- `needs_human` khác (trượt cổng nhiều vòng…) hoặc `failed`: báo nguyên văn lý do (`bin/news status last`), đề xuất cách xử lý, chờ Sếp.

Luật: giọng đọc tốn credit, chỉ tạo một lần; không dùng `--replace` trừ khi kịch bản đổi. Góp ý của Sếp về tập: `bin/news feedback <tap> <bước> "<nội dung>"`.
