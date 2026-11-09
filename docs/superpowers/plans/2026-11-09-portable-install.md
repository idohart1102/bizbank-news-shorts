# Cài đặt độc lập với Python hệ thống

Mục tiêu: triển khai phương án uv + Python 3.12 riêng đã được Sếp duyệt; rà lỗi chuyển máy, kiểm thử và phát hành GitHub.

- [x] Bộ cài: `.python-version`, requirements khóa kèm hash; uv tạo/sync `.venv`; không fallback sang Python bất kỳ. Giữ bản sao môi trường cũ khi phải thay. Kiểm Node 22, npm, FFmpeg trước thao tác tốn thời gian; cấu hình máy không bị ghi đè.
- [x] Launcher và doctor: báo rõ Python/thư viện lệch phiên bản, Node/Remotion, âm thanh và phụ thuộc theo hệ điều hành; xử lý máy sạch chưa có tập, Git worktree và đường dẫn có khoảng trắng.
- [x] Test hồi quy cho kiểm môi trường, máy sạch, launcher, cấu hình và bộ cài chạy lại; CI macOS/Linux chạy bootstrap và toàn bộ test, có render thật không tốn TTS/AI.
- [ ] Hướng dẫn nhận repo/nâng cấp/khắc phục, ghi thay đổi v1.1.0. Rà diff, guard_repo, cài từ bản sao sạch; commit, push, tag/release và xác minh GitHub.

Giới hạn: macOS/Linux; Windows dùng WSL2. Apple Vision tách nền chỉ có trên macOS 14+; dịch vụ TTS và tài khoản CLI do người nhận cấu hình, không đóng gói bí mật. Không thay dữ liệu tập/giọng thật.

Kết quả rà mã: sửa thêm hook tùy chỉnh chứa guard bị ghi đè, và package news trùng tên từ cwd. 27 test local đã qua, gồm render thật không tốn AI/TTS. Bản sao sạch cài đủ 32 âm thanh, doctor local qua; chạy lại đã giữ nguyên cấu hình máy, .env và hook riêng. CI được xác minh trên GitHub trước khi chốt release.
