# Quyết định của Sếp (file này thắng khi mâu thuẫn)

- 2026-11-07: Tạo dự án tại `projects/youtube/News video`. Short tin tức VN < 60s, đối tượng hộ kinh doanh và SME, nguồn báo chí + mạng xã hội VN.
- 2026-11-07: Phân vai: Claude Opus 5.5 viết/duyệt kịch bản, plan dựng; Codex gpt-6.1-sol tìm tư liệu, ảnh thật, ảnh/asset minh họa; Remotion dựng.
- 2026-11-07: Template là 1 PNG do Sếp thiết kế, nằm lớp trên cùng.
- 2026-11-07: Giọng Vbee, tích hợp vào `platform/tts` dùng chung (không giữ key trong repo).
- 2026-11-07: Tiếng động lấy từ Pixabay Sound Effects, giữ một kho cố định `assets/sfx/` kèm license.
- 2026-11-07: Được dùng ảnh báo, ảnh internet, ảnh AI; Sếp chấp nhận rủi ro bản quyền. Vẫn ghi nguồn ảnh trong `assets.json`.
- 2026-11-07: Giọng Vbee HN - Ngọc Huyền (`hn_female_ngochuyen_full_48k-fhg`), token Vbee vĩnh viễn. SRT tạo tại máy bằng Whisper (Vbee không có SRT).
- 2026-11-07: Đăng bài: hệ thống tự chạy tới bước "đăng" nhưng chỉ xếp vào hàng chờ `publish/outbox` (trạng thái `pending_connection`); API các nền tảng Sếp tự đấu nối sau.
- 2026-11-07: Thông báo qua Telegram, đấu nối sau; trước mắt ghi `episodes/notifications.jsonl` + thông báo macOS.
- 2026-11-07: Lịch chạy mặc định 10:30 và 19:00 hằng ngày (mỗi lần 1 tập, không lặp tin đã làm), và chạy khi được yêu cầu (`news run`).
- 2026-11-07: Repo là hệ độc lập, chuyển giao được cho người khác: không đường dẫn máy/bí mật/dữ liệu tập trong Git, phụ thuộc ngoài qua adapter, không đưa lịch sử sản phẩm/video (dữ liệu các tập làm ở local) lên GitHub; lịch sử commit của hệ thống vẫn giữ. Có cơ chế bài học tự cải thiện (`lessons/`).
