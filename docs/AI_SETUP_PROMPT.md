# Prompt bàn giao cho AI trên thiết bị mới

Dán nội dung dưới đây cho AI có quyền đọc repo và chạy terminal trên thiết bị mới:

> Hãy cài đặt và nghiệm thu repo bizbank-news-shorts trên thiết bị này. Đọc AGENTS.md hoặc CLAUDE.md, docs/decisions.md, rồi docs/INSTALL.md. Tuân theo thứ tự và tiêu chí đạt của tài liệu; kiểm thực tế OS, CPU, shell, PATH, quyền và dung lượng trước khi chọn nhánh cài.
>
> Dùng Python/Node đã quy định trong repo, không sửa Python toàn máy hoặc nâng dependencies để né lỗi. Cài TTS từ source sạch core/tts bằng bin/bootstrap --with-tts, không cài gói PyPI trùng tên tts. Không lấy file cấu hình, key, data hoặc đường dẫn của máy cũ.
>
> Tự thực hiện các bước cài môi trường và kiểm thử không tốn tiền. Cho tôi đăng nhập/nhập key qua giao diện hoặc terminal an toàn khi cần; không yêu cầu dán bí mật vào chat, không in key ra log. Không tự tạo giọng thật, gọi model trả phí, bật lịch chạy thật, mở cổng ra Internet hoặc đăng video chỉ để kiểm tra cài đặt. Xin tôi quyết định ở đúng bước phụ thuộc tài khoản/chi phí/bật lịch; vẫn hoàn tất các phần độc lập đang làm được.
>
> Từng bước phải có lệnh đã chạy, mã thoát và bằng chứng đạt. Nếu thiếu mạng, quyền, credentials, quyền model hoặc tài nguyên, ghi chính xác phần bị chặn; không bỏ qua kiểm tra rồi báo cài xong. doctor --local chỉ chứng minh môi trường local. Phải kiểm thêm TTS CLI + model cache + service, đăng nhập CLI, model/router, chạy thật có kiểm soát và lịch hệ điều hành trước khi báo sẵn sàng chạy tự động.
>
> Cuối cùng báo: commit đang cài; OS/CPU; Python/Node/npm/FFmpeg/CLI versions; bootstrap/local tests/render/TTS/model/auth/live/scheduler đã đạt gì; phần nào chưa kiểm và vì sao; nơi lưu dữ liệu/log; cách chạy, tiếp tục, nâng cấp và tắt lịch/dịch vụ. Không đưa bí mật hoặc nội dung video vào báo cáo.
