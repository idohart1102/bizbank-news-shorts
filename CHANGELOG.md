# Thay đổi

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
