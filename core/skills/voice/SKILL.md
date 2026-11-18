---
name: voice
description: Tạo giọng VieNeu local cho script_tts.txt và căn mốc từng từ bằng Whisper; dùng lại audio khi yêu cầu không đổi.
---
1. Cài máy mới theo `docs/INSTALL.md`; TTS/model/service phải được kiểm trước khi tạo giọng. Tự động trong `bin/news run` (bước `voice`), chỉ sau khi kịch bản qua duyệt.
2. Mặc định `tts.provider=vieneu`: cài bằng `bin/vieneu install`, kiểm `bin/vieneu status`; xem `docs/VIENEU.md`. Gọi `bin/vieneu say --voice <tts.voice> --file script_tts.txt --out audio/voice.mp3`, rồi `bin/tts align --audio audio/voice.mp3 --text script_tts.txt --out audio/voice.srt --words audio/voice.words.json`. Không cần service/key Vbee. Mốc từ canh thẻ/cutout; video không có phụ đề.
3. `script_tts.txt` là các `say` nối bằng dấu cách, không xuống dòng. Không tự đổi preset hoặc dùng giọng mặc định khi tên cấu hình không tồn tại.
4. Cổng: 15–57 giây (dài hơn thì trả về kịch bản, không tăng tốc quá 1,1x); mốc mỗi đoạn 2–9 âm tiết/giây (lệch là căn hỏng: chạy lại `tts align`, không tạo lại giọng).
5. Giữ audio khi căn từ lỗi, chỉ chạy lại align. VieNeu dùng lại kết quả đúng text/voice/speed; không tự `--replace`. Nếu Sếp chọn Vbee theo hướng dẫn, lỗi API không tự gửi lại; `uncertain` thì báo Sếp. Sổ chi tiêu chỉ ghi job Vbee thực sự tính tiền.
