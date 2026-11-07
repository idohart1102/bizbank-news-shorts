---
name: voice
description: Tạo giọng Vbee + srt cho script_tts.md qua platform/tts. Tốn credit, chạy một lần.
---
1. Chỉ chạy khi `qa/script_vN.md` đạt.
2. `tts say --provider vbee --voice <tts.voice trong config> --file script_tts.md --out audio/voice.mp3 --project news-video --srt`.
   `script_tts.md` chỉ chứa đúng lời đọc (không tiêu đề, không ghi chú), vì SRT được căn theo đúng chữ này.
3. Kiểm thời lượng ≤ 57s; dài hơn thì trả về kịch bản, không cắt tốc độ quá 1.1x.
4. Có audio nhưng thiếu/lệch SRT: `tts align --audio audio/voice.mp3 --text script_tts.md --words audio/voice.words.json`. Không tạo lại giọng.
5. Luôn tạo thêm `audio/voice.words.json` bằng lệnh ở bước 4 (miễn phí) để plan dựng canh chữ nhấn theo từ.
6. Lỗi API: không tự gửi lại, kiểm `tts service status`. Trạng thái `uncertain` thì báo Sếp.
