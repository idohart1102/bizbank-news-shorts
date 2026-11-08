---
name: voice
description: Tạo giọng Vbee liền mạch cho script_tts.txt (sinh từ script.json) và mốc thời gian từng từ qua platform/tts. Tốn credit, chạy một lần.
---
1. Tự động trong `bin/news run` (bước `voice`), chỉ sau khi kịch bản qua duyệt.
2. `tts say --provider vbee --voice <tts.voice> --pauses sentence=0.1,major=0.1,medium=0.1,paragraph=0 --file script_tts.txt --out audio/voice.mp3 --project news-video --srt`, rồi `tts align ... --words audio/voice.words.json` (miễn phí). Mốc từng từ dùng để canh thẻ chữ/số và cutout; video không có phụ đề.
3. `script_tts.txt` là các `say` nối bằng dấu cách (không xuống dòng, để Vbee không nghỉ dài).
4. Cổng: 15–57 giây (dài hơn thì trả về kịch bản, không tăng tốc quá 1,1x); mốc mỗi đoạn 2–9 âm tiết/giây (lệch là căn hỏng: chạy lại `tts align`, không tạo lại giọng).
5. Lỗi API: không tự gửi lại; `uncertain` thì báo Sếp. Sổ chi tiêu chỉ ghi job Vbee thực sự tính tiền.
