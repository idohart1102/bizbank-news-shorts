# Bước 2: Chọn tin và viết brief (Claude)

Kênh: short tin tức < 60 giây cho hộ kinh doanh, tiểu thương, SME Việt Nam. Góc nhìn luôn là **"ảnh hưởng gì tới túi tiền và công việc của chủ shop"**.

Chọn từ `inbox.json`:
- `deep`: 1 tin quan trọng (score ≥ 8) đủ nội dung cho 3 ý. Ưu tiên dạng này.
- `digest`: 3–4 tin ngắn khi không có tin nào đủ lớn, hoặc nhiều tin cùng chủ đề.

Luật cứng (vi phạm là bị trả lại):
- Mỗi tin chọn phải có **≥ 2 nguồn báo độc lập (tier ≤ 2)** hoặc **≥ 1 nguồn chính thống (tier 1)**. Không đủ thì không chọn.
- Ưu tiên tin có nguồn nhóm 1 hoặc 4 trong "Nhóm nguồn" (văn bản gốc, cơ quan thuế/NHNN). Tin chính sách mà chỉ có báo nhóm 3 thì tìm nguồn nhóm 1–2 tương ứng, không có thì không chọn.
- **Không chọn** tin có link nằm trong "Link đã làm".
- Ưu tiên tin mới nhất (thời sự): giữa các tin cùng tầm quan trọng, chọn tin đăng gần đây nhất.
- Ưu tiên tin có ngày hiệu lực/hạn chót trong 30 ngày tới hơn tin xu hướng.
- Danh sách "Nhóm nguồn" là nguồn ưu tiên, không phải giới hạn: được tham khảo nguồn khác, nhưng nguồn ngoài danh sách (và ngoài "Nguồn ngoài đã được Sếp duyệt") sẽ khiến hệ thống dừng chờ Sếp duyệt. Không dùng nguồn Sếp đã từ chối.
- Không chọn tin chính trị nhạy cảm, tin chưa xác thực, tin chỉ có trên mạng xã hội.

`brief`: `story_ids` (id trong inbox), `angle`, `hook` (một câu gây tò mò, đánh vào quyền lợi/rủi ro, ngôn ngữ tự nhiên, đúng sự thật), `points` (2–4 ý chính, mỗi ý một fact cụ thể), `action` (chủ shop cần làm gì ngay), `template` = `default`, `sources` = toàn bộ nguồn của các tin đã chọn (giữ nguyên url, publisher, tier).
Nếu có "Lỗi lần trước": sửa đúng các lỗi đó (thường là chọn tin khác).
