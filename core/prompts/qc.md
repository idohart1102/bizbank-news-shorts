# Bước 9: QC video (Claude, không phải người lên plan)

Xem các ảnh contact sheet (dùng tool Read mở từng file trong "Khung hình"). Mỗi sheet là lưới khung hình theo thứ tự thời gian, trái → phải, trên → dưới; mốc thời gian từng ô ghi trong "Khung hình".
Bố cục: nửa trên là vùng ảnh (ảnh nền, thẻ chữ/số, cutout); nửa dưới là khung template BizBank (cố ý để trống, không phải lỗi). Video **không có phụ đề** (cố ý).

Kiểm và ghi `issues` (time = giây của khung lỗi):
- `major` (luật Sếp 2026-11-08): **cảnh lời kêu gọi theo dõi (cuối video) là ảnh trống, không có chủ thể** (tường, bàn, phòng không người); **thẻ chữ/số còn hiện khi đã sang cảnh sau hoặc lời đã chuyển ý khác**.
- `major`: thẻ chữ/số bị tràn, bị cắt, chữ đè nhau hoặc sai chính tả tiếng Việt; thẻ/cutout che nhãn "Nguồn…" góc trên phải; cutout lỗi (mất đầu, rìa bẩn, sai người/sai vật so với lời); hình nền không liên quan/ngược nghĩa với lời đang đọc; khung đen/trắng/ảnh lỗi; ảnh AI trông như ảnh thật của người/sự kiện có thật; nội dung phản cảm.
- `minor`: ảnh mờ, bố cục chưa đẹp, thẻ hơi sớm/muộn, cutout che mất chủ thể của ảnh nền.

`kind`: `background` (ảnh nền lạc đề, ngược nghĩa, gây hiểu sai với lời), `card`, `cutout`, `cta`, `frame`, `ai_realism`, `other`.
`fix`: sửa cụ thể trong edit_plan.json (đổi asset nền của cảnh t=…, đổi motion…). Lỗi nằm ở thẻ/cutout thì ghi rõ để người bảo trì sửa kịch bản/asset. `pass` = không có lỗi `major`.
