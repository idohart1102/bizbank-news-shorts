# Thay đổi

## v1.6.0 — 2026-11-19

Kênh 2 hướng (tin tức 4/5, kiến thức 1/5) × 4 chủ đề: Vốn, Quản trị doanh nghiệp thông minh, Luật doanh nghiệp và HKD, AI Marketing.

- Hướng kiến thức (`bin/news run --kind knowledge`, `/chonchude kien thuc`): Claude Sonnet đọc 10 nguồn tham chiếu và đề xuất đề tài; chọn 1 đề tài dạng các bước/lỗi hay gặp/giải thích; viết theo `core/standard/script_knowledge.md`. Từ bước duyệt trở đi dùng chung với tin tức.
- Tỷ trọng 4 tin tức : 1 kiến thức: lịch chạy dùng `--kind auto`; chạy tay mặc định tin tức. Tập ghi hướng trong `state.json`, sổ `index.jsonl` ghi `kind`, `pillar`, `title`, `partners`.
- Cổng duyệt đối tác: video nhắc tên đối tác hoặc brief có `partner` dừng trước hàng chờ đăng, người ra lệnh duyệt bằng `bin/news approve <tap>`.
- Nguồn tham chiếu kiến thức được tính là nguồn trong danh sách (không phải chờ duyệt).
- Kênh có 4 chủ đề (`config/pillars.yaml`): Vốn, Quản trị doanh nghiệp thông minh, Luật doanh nghiệp và HKD, AI Marketing, kèm tỷ trọng mục tiêu và từ khóa lọc RSS riêng từng chủ đề.
- Gom tin gắn `pillar_hints` theo từ khóa/nguồn; Sonnet gắn `pillar` cho từng tin trong `inbox.json`. Brief có `kind` (news) và `pillar`; bước chọn tin cân tỷ trọng chủ đề theo các tập gần đây, cổng kiểm chặn `pillar` lệch tin chính. Sổ `index.jsonl` ghi `kind`, `pillar`.
- Thêm nguồn nhóm 5 (Sếp tạm chốt) và RSS chuyên mục pháp luật/công nghệ; nguồn tiếng Anh dùng bộ từ khóa riêng. `bin/news topics` và `/chonchude` hiện và nhóm theo chủ đề.
- Xác minh: 88/88 test đạt; chạy thật bước đề xuất đề tài kiến thức ra 12 đề tài đủ 4 chủ đề. Chưa nghiệm thu một video kiến thức hoàn chỉnh.

## v1.5.0 — 2026-11-18

- Chuyển ảnh minh họa, ảnh nền dự phòng và cutout AI từ 9router sang công cụ `image_gen` tích hợp của Codex CLI; dùng đăng nhập Codex tại máy.
- Cấu hình mặc định bỏ URL/key/model alias của router. Doctor kiểm khả năng CLI hỗ trợ image_generation, không yêu cầu 9router khi dùng Codex CLI.
- Adapter nhận PNG thực đã lưu, kiểm định dạng bằng FFprobe; không tự fallback qua gateway/API key riêng khi Codex lỗi. Log và file trung gian ở `local/imagegen/`, không vào Git.
- Cập nhật hướng dẫn cài máy mới và chuyển cấu hình cũ; bổ sung test CLI thành công, lỗi, file thiếu/sai định dạng và chặn gọi trong chế độ offline.
- Xác minh: 82/82 test đạt; adapter Codex CLI 0.170.0 trên macOS ARM64 tạo được cutout PNG 1024×1024 có alpha thật. Doctor đạt với cấu hình không dùng router.

## v1.4.0 — 2026-11-18

- Thay giọng mặc định Vbee bằng VieNeu-TTS v3 Turbo chạy local qua ONNX CPU/fp32; giữ Whisper để căn mốc từng từ.
- Thêm `bin/vieneu install|status|voices|say|download`; bộ cài khóa phiên bản source, cài môi trường riêng và tải model vào `local/vieneu/`, không đưa source bên thứ ba/model/audio vào GitHub.
- Cho phép chọn giọng preset bằng `tts.voice` trong `config/channel.yaml`; hướng dẫn cài máy mới, thử giọng và đổi giọng tại `docs/VIENEU.md`.
- Dùng lại audio đúng yêu cầu và checksum, không ghi đè ngầm; không tự chuyển sang Vbee trả phí khi VieNeu lỗi. Doctor nhận biết VieNeu offline, không yêu cầu Vbee key/service.
- Nguồn tin và nguồn ảnh trên template được ghi theo từng tập thay cho dòng in cứng; đánh dấu ảnh AI khi có.
- Xác minh trên macOS Apple Silicon: 79/79 test đạt, đoạn thử VieNeu 50 từ được Whisper căn khớp 100%. Chưa nghiệm thu VieNeu thật trên Linux/WSL.

## v1.3.0 — 2026-11-17

- Phân vai mới: Claude Sonnet 5.5 gom tin, kiểm fact kịch bản và tìm ảnh thật (WebSearch/WebFetch); Codex cx/gpt-6.1-sol chỉ còn tạo ảnh/asset minh họa AI.
- Skill /chonchude (tìm 3–5 chủ đề, chờ Sếp chọn) và /taovideo (chạy tới bước package); lệnh `news topics`, cờ `run --story`.
- Nguồn ưu tiên theo danh sách Sếp, nguồn ngoài chờ duyệt (`news sources pending|approve|reject`); ưu tiên tin mới, luật hook.
- Kịch bản trượt hết vòng sửa khi chưa tạo giọng thì tự chuyển sang tin kế tiếp, không tốn credit Vbee.
- Thẻ chữ/số cho phép tối đa 3 giá trị; câu kết viết «không bỏ lỡ».
- Tự chạy ổn định hơn: ảnh đúng chủ đề, bài học không phá tập đang chạy, TTS dùng chung.
- CLAUDE.md trỏ tới AGENTS.md, bỏ bản sao.

## v1.2.0 — 2026-11-09

- Bàn giao source TTS sạch cùng repo; wrapper bin/tts dùng Python riêng, dữ liệu/key tách ở local và kho key của OS.
- Bootstrap --with-tts cài aligner có lock/hash theo nền tảng, tải Whisper large-v3-turbo; MLX cho Apple Silicon, faster-whisper CPU cho Linux/Intel.
- Cổng TTS CLI/health thống nhất; kiểm cache đủ artifact, backend/model/python/lock; ngăn dịch vụ trùng cổng và dừng khi align khớp dưới 85%.
- Quản lý TTS nền qua launchd/systemd user, giữ cấu hình không bí mật đúng khi chuyển từ foreground.
- docs/INSTALL.md có quy trình AI cài mới đầy đủ, tài khoản/model, nghiệm thu, scheduler, nâng cấp và khôi phục; thêm prompt bàn giao và script sinh lịch chưa tự kích hoạt.
- Test TTS server giả, bảo vệ key/job/data, backend và lỗi môi trường; không dùng credit thật để nghiệm thu cài đặt.

## v1.1.0 — 2026-11-09

- Python 3.12 riêng qua uv, tự tải nếu thiếu; không phụ thuộc Python mặc định trên máy nhận.
- Đồng bộ thư viện Python theo phiên bản và SHA-256 trong requirements.lock; Node 22 và npm >= 10 được kiểm trước khi cài.
- Giữ bản sao .venv cũ khi sai phiên bản/đã di chuyển repo; cấu hình máy và .env được giữ khi chạy lại bộ cài.
- Cài trình duyệt Remotion trong bootstrap; doctor kiểm cả Python, gói, Node/npm, Remotion, SFX và nhạc nền. `doctor --local` không cần dịch vụ AI/TTS.
- Hook Git tự tìm vị trí repo, hỗ trợ worktree, giữ hook riêng có sẵn. Launcher hỗ trợ đường dẫn có khoảng trắng và gọi từ thư mục khác.
- Sửa tìm tập cuối khi máy chưa có dữ liệu, đường dẫn cấu hình tương đối và lỗi tách nền trên macOS cũ.
- Test hồi quy và CI macOS/Linux cài từ đầu, chạy toàn bộ test và render thật bằng dữ liệu mẫu.
