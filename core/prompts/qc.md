# Bước 9: QC video (Claude, không phải người lên plan)

Xem các ảnh contact sheet (dùng tool Read mở từng file trong "Khung hình"). Mỗi sheet là lưới khung hình theo thứ tự thời gian, trái → phải, trên → dưới; mốc thời gian từng ô ghi trong "Khung hình".

Kiểm và ghi `issues` (time = giây của khung lỗi):
- `major`: chữ (tiêu đề, chữ nhấn, phụ đề) bị overlay/template che hoặc tràn khỏi khung; chữ nằm dưới vùng an toàn (300px dưới cùng) hoặc sát mép phải; sai chính tả tiếng Việt; hình không liên quan/ngược nghĩa với lời đang đọc (so với kịch bản); khung đen/trắng/ảnh lỗi; ảnh AI trông như ảnh thật của người/sự kiện có thật; nội dung phản cảm.
- `minor`: ảnh mờ, bố cục chưa đẹp, chữ nhấn hơi sớm/muộn.

`fix`: sửa cụ thể trong edit_plan.json (đổi asset của cảnh t=…, rút headline, đổi motion…). `pass` = không có lỗi `major`.
Lưu ý: nhãn "TEMPLATE TẠM" là overlay tạm có chủ đích, không phải lỗi.
