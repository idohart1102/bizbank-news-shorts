# Bước 3: Viết kịch bản (Claude)

Viết kịch bản short < 60 giây theo "Chuẩn kịch bản" bên dưới, chỉ dùng fact có trong "Văn bản nguồn".

Yêu cầu bắt buộc:
- Giọng báo chí, ngắn, dễ hiểu với chủ hộ kinh doanh; thuật ngữ thuế/pháp lý có giải thích một vế ("thuế khoán, tức là mức thuế cố định hằng tháng").
- Cấu trúc đoạn: `hook` (0–3s) → `story` (1 tin sâu 3 ý, hoặc 3–4 tin mỗi tin 1 đoạn) → `action` → `cta`.
- **Tổng ≤ 200 âm tiết** (giới hạn cứng 220), mỗi câu ≤ 20 âm tiết.
- `say`: lời đọc cho máy, **không có chữ số và ký hiệu**: "một tỷ đồng", "ngày mười lăm tháng mười một", "mười phần trăm", "nghị định ba trăm chín mươi tám". Viết tắt đọc được thì viết đủ lần đầu ("bảo hiểm xã hội").
- `show`: cùng nội dung với `say` từng chữ, nhưng số dạng chữ số và ký hiệu chuẩn: "1 tỷ đồng", "15/11", "10%", "Nghị định 398". Không thêm/bớt ý so với `say`.
- `highlight`: 0–2 cụm **nguyên văn trong `show`** cần nhấn (số tiền, ngày, mức %). Mỗi cụm ≤ 4 từ.
- `visual`: mô tả hình cụ thể để tìm ảnh thật (ví dụ "ảnh chụp trang đầu Nghị định 398 trên baochinhphu.vn", "chủ tiệm tạp hóa quét mã QR thanh toán").
- `source_ids` cho mọi đoạn có fact. `sources`: mỗi nguồn dùng tới có `quote` **trích nguyên văn** câu chứa số liệu/ngày đã dùng.
- Số liệu, ngày hiệu lực, mức phạt **khớp nguyên văn nguồn**. Không suy đoán, không khuyên pháp lý/đầu tư chắc chắn ("nên hỏi kế toán/cơ quan thuế").
- `cta`: một câu ngắn mời theo dõi kênh; không cần nguồn.
- Có "Cần sửa": sửa **đúng** từng lỗi, giữ phần đã ổn của "Bản trước".
