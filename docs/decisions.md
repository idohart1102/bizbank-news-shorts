# Quyết định của Sếp (file này thắng khi mâu thuẫn)

- 2026-11-07: Tạo dự án tại `projects/youtube/News video`. Short tin tức VN < 60s, đối tượng hộ kinh doanh và SME, nguồn báo chí + mạng xã hội VN.
- 2026-11-07: Phân vai: Claude Opus 5.5 viết/duyệt kịch bản, plan dựng; Codex gpt-6.1-sol tìm tư liệu, ảnh thật, ảnh/asset minh họa; Remotion dựng.
- 2026-11-07: Template là 1 PNG do Sếp thiết kế, nằm lớp trên cùng. (2026-11-08: giữ nguyên, template BizBank trên cùng; thẻ/cutout chỉ trong vùng ảnh nửa trên.)
- 2026-11-07: Giọng Vbee, tích hợp vào `platform/tts` dùng chung (không giữ key trong repo).
- 2026-11-07: Tiếng động lấy từ Pixabay Sound Effects, giữ một kho cố định `assets/sfx/` kèm license.
- 2026-11-07: Được dùng ảnh báo, ảnh internet, ảnh AI; Sếp chấp nhận rủi ro bản quyền. Vẫn ghi nguồn ảnh trong `assets.json`.
- 2026-11-07: Giọng Vbee HN - Ngọc Huyền (`hn_female_ngochuyen_full_48k-fhg`), token Vbee vĩnh viễn. SRT tạo tại máy bằng Whisper (Vbee không có SRT).
- 2026-11-07: Đăng bài: hệ thống tự chạy tới bước "đăng" nhưng chỉ xếp vào hàng chờ `publish/outbox` (trạng thái `pending_connection`); API các nền tảng Sếp tự đấu nối sau.
- 2026-11-07: Thông báo qua Telegram, đấu nối sau; trước mắt ghi `episodes/notifications.jsonl` + thông báo macOS.
- 2026-11-07: Lịch chạy mặc định 10:30 và 19:00 hằng ngày (mỗi lần 1 tập, không lặp tin đã làm), và chạy khi được yêu cầu (`news run`).
- 2026-11-07: Repo là hệ độc lập, chuyển giao được cho người khác: không đường dẫn máy/bí mật/dữ liệu tập trong Git, phụ thuộc ngoài qua adapter, không đưa lịch sử sản phẩm/video (dữ liệu các tập làm ở local) lên GitHub; lịch sử commit của hệ thống vẫn giữ. Có cơ chế bài học tự cải thiện (`lessons/`).
- 2026-11-07: Không dùng lại ảnh trong một video (mỗi ảnh một cảnh). Giọng đọc liền mạch, ngắt nghỉ ngắn nhất (Vbee clientPause). Có nhạc nền nhỏ xuyên suốt video (kho Pixabay `assets/music/`) kèm hiệu ứng âm thanh.
- 2026-11-08: Không làm phụ đề. Tập trung thẻ chữ/số cho thông tin quan trọng, mỗi thẻ xuất hiện kèm tiếng động.
- 2026-11-08: Đa dạng cutout: người nổi tiếng được nhắc tên (ảnh thật tách nền, không AI vẽ người thật), sự vật quan trọng được nhắc tới (AI PNG trong suốt hoặc ảnh thật tách nền); xuất hiện kèm tiếng động.
- 2026-11-08: Template mặc định: BizBank (`assets/template/overlay.png`, bản Sếp gửi ngày 2026-11-07, Drive `05 - BUSINESS/Bizbank`). Không dùng `Template 1.png`.
- 2026-11-08: Template 2 BizBank (khung ảnh/video 4:3, 1080x810) thay template trước. Thẻ chữ/số, cutout, ảnh luôn nằm trong khung 4:3 kể cả khi phóng/lia; phóng vừa đủ theo độ phân giải ảnh gốc. Câu hook < 100 ký tự dưới khung. Ảnh sưu tầm ưu tiên ≥ 1080p (phủ khung 1080x810), ảnh nhỏ hơn chỉ khi không tìm được ảnh khác. Thẻ theo màu template (navy, lá mạ, xanh dương, bạc hà).
- 2026-11-08: Version 1 của hệ thống đạt (video demo mã số thuế 06). Repo GitHub private `idohart1102/bizbank-news-shorts`, tag `v1.0.0`. Repo chỉ chứa hệ thống, không chứa video/dữ liệu tập.
- 2026-11-08: Bỏ hạn mức ký tự Vbee (`budget.vbee_chars_per_day: 0`). Sổ chi tiêu vẫn ghi để theo dõi.
- 2026-11-08: Luật QC thêm: cảnh lời kêu gọi theo dõi không được là ảnh trống không chủ thể; thẻ chữ/số không được kéo sang cảnh sau (render tự tắt thẻ ở cuối cảnh, validate_plan chặn cắt cảnh < 1,2s sau khi thẻ hiện).
- 2026-11-08: Repo `idohart1102/bizbank-news-shorts` chuyển sang **public** theo yêu cầu Sếp.

- 2026-11-09: Theo yêu cầu Sếp, bộ cài dùng uv quản lý Python 3.12 riêng, khóa thư viện theo hash, kiểm Node 22/npm trước khi cài; thêm doctor --local, test cài mới macOS/Linux và phát hành v1.1.0. Windows dùng WSL2.

- 2026-11-09: Sếp yêu cầu rà lại và hướng dẫn AI cài đầy đủ trên máy mới; chọn đưa source TTS sạch vào cùng repo. Dùng bin/tts, source core/tts; key/job/audio/model cache vẫn local. MLX Apple Silicon, faster-whisper CPU Linux/Intel. Lịch được sinh riêng và chỉ bật sau nghiệm thu, không mặc định có scheduler sau bootstrap.

- 2026-11-12: Cập nhật nguồn ưu tiên theo tài liệu Sếp "BizBank Academy - List nguồn lấy tin" (`config/sources.yaml`, trường `group`). Nhóm 1 cơ quan nhà nước (Thời báo Tài chính VN, Tạp chí Kinh tế - Tài chính, NHNN, Báo Chính phủ, Tạp chí Công Thương) tính là nguồn chính thống (tier 1). Nhóm 2 báo kinh tế SME, nhóm 4 chuyên hộ kinh doanh (VINASME, Cục Thuế, VCCI) dùng làm nguồn số liệu. Nhóm 3 báo đại chúng chỉ bắt mạch, không làm nguồn số liệu; CafeF là aggregator, tier 3, không tính nguồn độc lập.
- 2026-11-12: Danh sách nguồn là ưu tiên, không phải giới hạn. Được tham khảo nguồn khác nhưng phải Sếp duyệt: nguồn lạ làm tập dừng chờ (`bin/news sources pending|approve|reject`, lưu `config/sources_approved.yaml`). Tin mới nhất được ưu tiên (tính thời sự khi chấm và chọn tin).
- 2026-11-12: Hook text trên video phải gây tò mò, ngôn ngữ tự nhiên: không xuồng xã, không khô cứng quá mức; vẫn đúng sự thật, không giật tít sai.
- 2026-11-13: Thẻ chữ/số được tối đa 3 giá trị (một mốc giờ/ngày như «15h ngày 12/11» tính là một), vẫn ≤ 18 ký tự. Kiểm nguồn chỉ áp cho nguồn tin; nguồn lấy ảnh không giới hạn tên miền.
- 2026-11-13: Kịch bản trượt hết vòng sửa khi chưa tạo giọng thì tự bỏ tin, làm tin xếp hạng kế tiếp (tối đa 2 tin/tập, chỉ tin score ≥ 6 chưa làm); tin Sếp tự chọn bằng `/taovideo <id>` thì vẫn dừng báo Sếp.
