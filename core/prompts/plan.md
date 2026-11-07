# Bước 7: Plan dựng (Claude)

Lập `edit_plan.json` cho short 9:16 từ mốc thời gian thật của giọng đọc. Mục tiêu: người xem không lướt qua, hình luôn khớp lời.

Luật (code kiểm, sai là bị trả lại):
- Cảnh phủ kín từ 0 tới hết audio, liền nhau (end cảnh trước = start cảnh sau), không hở, không chồng.
- Mỗi cảnh 1,5–4 giây; cảnh `static` không quá 2,5 giây. Cảnh nằm trong một đoạn (`segment`) và dùng hình của đúng đoạn đó (`asset` là id trong danh sách ảnh).
- **Mỗi ảnh chỉ dùng cho đúng một cảnh trong cả video, tuyệt đối không dùng lại.** Số cảnh của một đoạn không vượt số ảnh của đoạn đó; thiếu ảnh thì kéo dài cảnh (tối đa 4 giây, có chuyển động) hoặc mượn ảnh chưa dùng của đoạn kề có nội dung phù hợp.
- `motion`: zoom-in, zoom-out, pan-left, pan-right, ken-burns, static, split. Xen kẽ, không lặp một kiểu quá 2 cảnh liền. Ảnh `doc`/`chart` dùng zoom-in chậm hoặc static.
- `headline`: tiêu đề ngắn (≤ 42 ký tự) cho cảnh đầu của mỗi đoạn tin; null cho các cảnh khác. Đoạn hook có headline gây chú ý đúng sự thật.
- `highlight_words`: lấy từ `highlight` của đoạn (cụm chữ nhấn), đặt ở cảnh chứa lúc cụm đó được đọc.
- `sfx`: id trong kho tiếng động. `whoosh`/`swoosh` ở đầu mỗi đoạn tin mới (trừ cảnh 0), `pop`/`ding` khi số liệu quan trọng xuất hiện, `kaching` hợp với tin về tiền, `sting` có thể dùng ở cảnh 0. Cách nhau ≥ 1,5 giây, phần lớn cảnh không có sfx.
- `template`: "default". `fps`: 30. `duration`: bằng thời lượng audio. `music`: null (nhạc nền do hệ thống tự chọn và trộn nhỏ xuyên suốt).
- Tiếng động: mỗi đoạn tin có ít nhất một sfx (chuyển đoạn hoặc nhấn số liệu).
- Có "Cần sửa": sửa đúng từng lỗi.
