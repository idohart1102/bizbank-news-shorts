---
name: chonchude
description: Tìm và đề xuất các chủ đề phù hợp nhất, hợp trend nhất cho video short tin tức hôm nay (gom tin từ nguồn ưu tiên, chấm điểm, xếp hạng), rồi dừng để Sếp chọn. Dùng khi Sếp gõ /chonchude, hỏi "hôm nay làm tin gì", "tìm chủ đề", "chọn chủ đề". Không tốn credit Vbee.
---
# Chọn chủ đề

Làm ở thư mục gốc dự án. Trao đổi tiếng Việt, ngắn gọn.

1. Gom tin: `bin/news run --until collect` (tạo tập mới, đọc RSS nguồn ưu tiên trong `config/sources.yaml`, Codex gộp tin trùng và chấm điểm). Lỗi thì báo nguyên văn dòng lỗi, dừng.
   Sếp nói "dùng tập vừa gom" thì bỏ bước này.
2. Xem chủ đề: `bin/news topics last --limit 15`.
3. Chọn ra **3–5 chủ đề tốt nhất**, bỏ tin có `[ĐÃ LÀM]`. Xếp theo:
   - Mức ảnh hưởng tới túi tiền/thủ tục của hộ kinh doanh, SME (điểm).
   - Độ trend: tin càng mới và càng nhiều báo cùng đưa càng hot.
   - Nguồn: có nhóm 1 (cơ quan nhà nước) hoặc nhóm 4 là tốt nhất; chỉ có nhóm 3/0 thì ghi rõ "thiếu nguồn số liệu".
4. Trình bày cho Sếp mỗi chủ đề: `id`, tiêu đề ngắn, vì sao đáng làm (một câu), độ mới + số báo, nguồn chính, một **câu hook mẫu** theo luật hook (`core/prompts/write.md`: gây tò mò, ngôn ngữ tự nhiên, đúng sự thật, < 100 ký tự). Đánh dấu chủ đề đề xuất số 1.
5. Kết bằng: "Sếp chọn chủ đề nào? Gõ `/taovideo <id>` để làm video." Không tự chạy tiếp.

Không có chủ đề nào điểm ≥ 6: nói rõ, đề xuất chờ lượt sau hoặc làm tin tổng hợp (digest).
