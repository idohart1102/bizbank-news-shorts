# Thay đổi

## v1.1.0 — 2026-11-09

- Python 3.12 riêng qua uv, tự tải nếu thiếu; không phụ thuộc Python mặc định trên máy nhận.
- Đồng bộ thư viện Python theo phiên bản và SHA-256 trong requirements.lock; Node 22 và npm >= 10 được kiểm trước khi cài.
- Giữ bản sao .venv cũ khi sai phiên bản/đã di chuyển repo; cấu hình máy và .env được giữ khi chạy lại bộ cài.
- Cài trình duyệt Remotion trong bootstrap; doctor kiểm cả Python, gói, Node/npm, Remotion, SFX và nhạc nền. `doctor --local` không cần dịch vụ AI/TTS.
- Hook Git tự tìm vị trí repo, hỗ trợ worktree, giữ hook riêng có sẵn. Launcher hỗ trợ đường dẫn có khoảng trắng và gọi từ thư mục khác.
- Sửa tìm tập cuối khi máy chưa có dữ liệu, đường dẫn cấu hình tương đối và lỗi tách nền trên macOS cũ.
- Test hồi quy và CI macOS/Linux cài từ đầu, chạy toàn bộ test và render thật bằng dữ liệu mẫu.
