# Bước 6: Tìm ảnh cho từng đoạn (Codex, có tìm web)

Mỗi đoạn kịch bản có `visual` mô tả hình cần. Dùng web_search tìm **ảnh thật** cho từng đoạn, ưu tiên:
1. Ảnh trong chính các bài báo nguồn hoặc bài báo VN khác về cùng sự kiện (ảnh minh họa của báo).
2. Ảnh chụp/trang văn bản chính thống (cổng Chính phủ, Bộ, Cục Thuế) khi đoạn nói về văn bản.
3. Ảnh báo chí cùng chủ đề (chợ, cửa hàng, quầy thu ngân, người lao động…) nếu không có ảnh sự kiện.

Mỗi cảnh trong video dùng một ảnh riêng, **không dùng lại ảnh**, nên cần khoảng 1 ảnh cho mỗi 3,5 giây lời đọc. Với mỗi đoạn, trả 4–8 `candidates` khác nhau (không trùng ảnh, không cùng ảnh ở cỡ khác):
- `image_url`: link **trực tiếp** tới file ảnh (.jpg/.jpeg/.png/.webp), lấy đúng từ trang bạn đã mở (thẻ og:image hoặc ảnh trong bài). Không bịa, không đoán đường dẫn.
- `page_url`: trang chứa ảnh; `credit`: tên báo/cơ quan; `kind`: `real` (ảnh chụp) hoặc `doc` (ảnh văn bản, bảng, website).
- Ảnh ngang hay dọc đều được, cạnh ngắn nên ≥ 600px. Tránh ảnh có watermark to, ảnh chân dung lãnh đạo không liên quan, ảnh quảng cáo.

`ai_prompt`: mô tả tiếng Anh cho ảnh minh họa dự phòng (dọc 2:3, phong cách ảnh chụp tài liệu, bối cảnh Việt Nam), **không** tái hiện người thật hay sự kiện cụ thể, không chữ trong ảnh. Đoạn `cta` có thể để candidates rỗng.

**Cutout người** ("Người cần ảnh cutout"): với mỗi người, trả 2–4 `candidates` là ảnh báo chí thật của **đúng người đó** (ảnh chân dung hoặc nửa người, một mình, rõ mặt, nền càng đơn giản càng tốt) — hệ thống sẽ tách nền. Không lấy ảnh nhiều người, ảnh bị che, ảnh hoạt họa.

Chỉ trả một JSON object: {"segments": [{"segment": "s1", "candidates": [...], "ai_prompt": "..."}], "cutouts": [{"name": "...", "candidates": [...]}]}
