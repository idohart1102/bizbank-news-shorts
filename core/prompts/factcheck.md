# Bước 4a: Đối chiếu fact (Codex)

So **từng** con số, ngày, đối tượng áp dụng, mức phạt, tên văn bản trong kịch bản (`show` và `say` của mọi đoạn) với "Văn bản nguồn".

- Fact đúng khi nguồn nói **đúng như vậy** (cho phép diễn đạt lại, không cho phép đổi số, đổi ngày, mở rộng/thu hẹp đối tượng).
- Fact không tìm thấy trong nguồn nào → ghi lỗi ("không có trong nguồn").
- `quote` trong `sources` không có nguyên văn trong văn bản nguồn → ghi lỗi.
- `say` đọc sai số so với `show` (ví dụ show "15/11", say "mười lăm tháng mười") → ghi lỗi.
- Nguồn tải lỗi ("[không tải được…]") thì dựa vào `quote` và ghi chú trong `checked`, không tự kết luận sai.

Trả `fact_errors` (rỗng nếu không có lỗi) và `checked` (mỗi fact đã kiểm, kết quả ngắn).
