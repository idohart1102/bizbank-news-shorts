# Bước 7: Plan dựng (Claude)

Lập `edit_plan.json` cho short 9:16 từ mốc thời gian thật của giọng đọc. Mục tiêu: người xem không lướt qua, hình luôn khớp lời.

Luật (code kiểm, sai là bị trả lại):
- Cảnh phủ kín từ 0 tới hết audio, liền nhau (end cảnh trước = start cảnh sau), không hở, không chồng.
- Mỗi cảnh 1,5–4 giây; cảnh `static` không quá 2,5 giây. Cảnh nằm trong một đoạn (`segment`) và dùng hình của đúng đoạn đó (`asset` là id trong danh sách ảnh).
- **Mỗi ảnh chỉ dùng cho đúng một cảnh trong cả video, tuyệt đối không dùng lại.** Số cảnh của một đoạn không vượt số ảnh của đoạn đó; thiếu ảnh thì kéo dài cảnh (tối đa 4 giây, có chuyển động) hoặc mượn ảnh chưa dùng của đoạn kề có nội dung phù hợp.
- `motion`: zoom-in, zoom-out, pan-left, pan-right, ken-burns, static, split. Xen kẽ, không lặp một kiểu quá 2 cảnh liền. Ảnh `doc`/`chart` dùng zoom-in chậm hoặc static.
- `headline`: luôn null; `highlight_words`: luôn []. Không có phụ đề; thẻ chữ/số và cutout do hệ thống tự hiện theo lời (xem danh sách kèm mốc), đã có tiếng động riêng.
- Ảnh nền chỉ nằm ở vùng ảnh (nửa trên); thẻ hiện ở phần dưới vùng ảnh, cutout đứng ở cạnh trái/phải. Trong lúc có thẻ/cutout, chọn ảnh nền thoáng (không nhiều chữ nhỏ), không trùng chủ thể với cutout đang hiện (cutout sổ thì nền không phải ảnh cuốn sổ), chuyển động nhẹ (zoom-in/ken-burns).
- `sfx`: id trong kho tiếng động cho chuyển cảnh: `whoosh`/`swoosh` ở đầu mỗi đoạn tin mới (trừ cảnh 0), `kaching` hợp tin về tiền, `sting` có thể dùng ở cảnh 0. Cách nhau ≥ 1,5 giây. Tiếng chuyển cảnh trùng lúc thẻ/cutout (< 1 giây) sẽ bị bỏ, nên tránh đặt ở đó.
- `template`: "default". `fps`: 30. `duration`: bằng thời lượng audio. `music`: null (nhạc nền do hệ thống tự chọn và trộn nhỏ xuyên suốt).
- Tiếng động: mỗi đoạn tin có ít nhất một sfx (chuyển đoạn hoặc nhấn số liệu).
- **Thẻ không kéo sang cảnh sau**: thẻ tự tắt khi hết cảnh nó xuất hiện, nên cảnh chứa lúc thẻ hiện phải kéo dài ít nhất 1,2 giây sau lúc đó (code kiểm). Đặt điểm cắt cảnh trước lúc thẻ hiện hoặc sau khi thẻ đã đủ thời gian.
- **Cảnh lời kêu gọi theo dõi (cta) không được là cảnh trống**: chọn ảnh có chủ thể rõ (người xem điện thoại, chủ shop tại quầy, cửa hàng đông khách…), không chọn tường/bàn/không gian trống.
- Có "Cần sửa": sửa đúng từng lỗi.
