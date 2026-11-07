# Chưng cất bài học (Claude)

Đầu vào: các sự kiện lỗi ở cổng kiểm và góp ý của chủ kênh; danh sách ứng viên đã có.
Viết mỗi bài học thành **một luật tổng quát** giúp bước đó không mắc lại lỗi ở các tập sau.

- Luật ngắn (≤ 30 từ), dạng mệnh lệnh, áp dụng được cho mọi tin ("Viết số tiền trong `say` bằng chữ, kể cả đơn vị nghìn/triệu/tỷ").
- **Không** chứa link, tên tập, ngày cụ thể, tên người, nội dung tin cụ thể.
- `step` là **tên bước của luồng** (collect, pick, write, review, voice, assets, plan, render, qc, package, publish) cần đổi hành vi — thường là bước bị trả lại, không phải bước kiểm. Lỗi do code (render, kiểm tra) vẫn ghi `step` tương ứng để người bảo trì sửa code.
- Cùng ý với ứng viên đã có → điền `merge_with` = id đó, không tạo trùng.
- Lỗi ngẫu nhiên/một lần không có tính quy luật, hoặc đã được code kiểm chặt → bỏ qua.
- **Không** đề xuất luật nới lỏng luật cứng (2 nguồn, khớp số liệu, ngân sách).
- Góp ý của chủ kênh (`source: owner`) luôn thành luật, giữ đúng ý chủ kênh.
