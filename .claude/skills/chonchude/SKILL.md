---
name: chonchude
description: Tìm và đề xuất các chủ đề phù hợp nhất cho video short (tin tức hợp trend hôm nay, hoặc đề tài kiến thức khi Sếp gõ "kien thuc") (gom tin từ nguồn ưu tiên, chấm điểm, xếp hạng), rồi dừng để Sếp chọn. Dùng khi Sếp gõ /chonchude, hỏi "hôm nay làm tin gì", "tìm chủ đề", "chọn chủ đề". Không tốn credit Vbee.
---
# Chọn chủ đề

Làm ở thư mục gốc dự án. Trao đổi tiếng Việt, ngắn gọn.

Tham số (Sếp gõ sau `/chonchude`, có dấu hay không dấu đều được):
- Không có tham số, hoặc `tin tuc`: luồng tin tức, bước 1 chạy `bin/news run --until collect --kind news`.
- `kien thuc`: luồng kiến thức, bước 1 chạy `bin/news run --until collect --kind knowledge` (Claude Sonnet đọc 10 nguồn tham chiếu trong `config/pillars.yaml` và đề xuất đề tài, lâu hơn tin tức vài phút). Các bước sau giữ nguyên, chỉ đổi cách gọi: "đề tài" thay "tin"; không có tiêu chí "độ mới, số báo cùng đưa", thay bằng "mức hữu ích cho chủ shop" và "nguồn chính thống".

1. Gom tin: lệnh theo tham số ở trên (tạo tập mới, đọc RSS nguồn ưu tiên trong `config/sources.yaml`, Claude Sonnet gộp tin trùng và chấm điểm). Lỗi thì báo nguyên văn dòng lỗi, dừng.
   Sếp nói "dùng tập vừa gom" thì bỏ bước này.
2. Xem chủ đề: `bin/news topics last --limit 20`. Mỗi tin có một trong 4 chủ đề kênh (`config/pillars.yaml`): Vốn, Quản trị doanh nghiệp thông minh, Luật doanh nghiệp và HKD, AI Marketing.
3. Chọn ra **3–5 chủ đề tốt nhất**, bỏ tin có `[ĐÃ LÀM]`. Cố gắng phủ nhiều chủ đề kênh (mỗi chủ đề kênh có tin score ≥ 6 thì đưa tin tốt nhất của nó), không đưa tin kém chỉ để đủ chủ đề. Xếp theo:
   - Mức ảnh hưởng tới túi tiền/thủ tục của hộ kinh doanh, SME (điểm).
   - Độ trend: tin càng mới và càng nhiều báo cùng đưa càng hot.
   - Nguồn: có nhóm 1 (cơ quan nhà nước) hoặc nhóm 4 là tốt nhất; chỉ có nhóm 3/0 thì ghi rõ "thiếu nguồn số liệu".
4. Trình bày cho Sếp, **nhóm theo chủ đề kênh**; mỗi chủ đề: `id`, tiêu đề ngắn, vì sao đáng làm (một câu), độ mới + số báo, nguồn chính, một **câu hook mẫu** theo luật hook (`core/prompts/write.md`: gây tò mò, ngôn ngữ tự nhiên, đúng sự thật, < 100 ký tự). Đánh dấu chủ đề đề xuất số 1.
5. Kết bằng: "Sếp chọn chủ đề nào? Gõ `/taovideo <id>` để làm video." Không tự chạy tiếp.

Không có chủ đề nào điểm ≥ 6: nói rõ, đề xuất chờ lượt sau hoặc làm tin tổng hợp (digest).
