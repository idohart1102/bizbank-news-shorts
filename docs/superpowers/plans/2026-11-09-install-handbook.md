# Hướng dẫn bàn giao cho AI trên máy mới

Mục tiêu: AI theo tài liệu trong repo cài đúng môi trường, phân biệt chạy thử/chạy thật và nêu rõ đầu vào chưa được bàn giao.

- [x] Đối chiếu runtime với tài liệu: TTS CLI/HTTP/Whisper, model/router, lịch chạy, cutout và outbox; sửa chốt kiểm cấu hình sai trước khi tốn tiền.
- [x] Viết `docs/INSTALL.md` theo các cổng nghiệm thu: khảo sát OS → prerequisites → bootstrap → local tests → dịch vụ/đăng nhập → chạy thật có kiểm soát → lịch → vận hành/khôi phục. Thêm prompt bàn giao AI, bảng lỗi và checklist kết quả.
- [x] Dẫn AI đến tài liệu ngay từ AGENTS.md/CLAUDE.md/README; bỏ cấu hình mẫu giả định backend chưa triển khai. Không copy bí mật/dữ liệu từ hub.
- [ ] Kiểm snippet và command theo CLI thật, test hồi quy cùng suite; rà độc lập, kiểm guard, cập nhật GitHub.

Ranh giới: không tạo giọng thật hay gọi model trả phí chỉ để thử cài; không bật lịch sản xuất trên máy Sếp. Sếp đã chọn đưa source TTS sạch vào repo. Cài aligner theo nền tảng (MLX Apple Silicon; faster-whisper CPU Linux/Intel), khóa hash; không đưa bí mật/data/cache của hub vào Git.

Rà độc lập đã sửa: exit3 align khớp thấp, marker model/cache sai/thiếu artifact, cấu hình service foreground/background và test đọc config/key thật. Source TTS sạch không gồm database/audio/cache; tạo câu thử bằng giọng macOS local và align MLX offline đạt match .969. Bootstrap bản sao sạch có aligner theo lock đã qua. Không bật dịch vụ/lịch sản xuất và không gọi Vbee/model trả phí.

Xác minh trước commit: 58/58 test trên macOS (gồm Remotion thật, TTS server giả và lỗi portability) qua; links, shell/Python syntax, plist sinh từ YAML và guard staged qua. Bản sao sạch bootstrap --with-tts --skip-tts-model qua, model download/status qua với cache hợp lệ. Kiểm GitHub/Linux sau push.
