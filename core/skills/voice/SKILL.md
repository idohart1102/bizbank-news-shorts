---
name: voice
description: Tạo giọng Vbee + srt cho script_tts.md qua platform/tts. Tốn credit, chạy một lần.
---
1. Chỉ chạy khi `qa/script_vN.md` đạt.
2. `tts say --provider vbee --voice <config> --file script_tts.md --out audio/voice.mp3 --project news-video --srt` (chờ provider Vbee trong platform/tts).
3. Kiểm thời lượng ≤ 57s; dài hơn thì trả về kịch bản, không cắt tốc độ quá 1.1x.
4. Lỗi API: không tự gửi lại, kiểm `tts service status` và credit.
