# Template PNG lớp trên cùng

- File: `assets/template/overlay.png` (BizBank, 1080×1920, RGBA), nằm **trên cùng**. Nửa trên (y 0–880) trong suốt là vùng ảnh; nửa dưới là khung xanh có logo, để trống (không đặt nội dung).
- Thứ tự lớp: ảnh nền → cutout → thẻ chữ/số → overlay. **Không có phụ đề.**
- `assets/template/layout.json`:
  - `media`: vùng ảnh nền (ảnh ngang/văn bản tự có nền mờ phía sau).
  - `cards`: vùng thẻ chữ/số (phần dưới vùng ảnh). Thẻ: giá trị lớn + nhãn, màu `brand`, bật lên đúng lúc trigger được đọc, kèm pop/ding.
  - `cutout`: vùng cutout; cutout đứng ở cạnh trái/phải, chân chạm mép khung xanh, trượt vào kèm whoosh/swoosh. Có cutout thì thẻ né sang phía đối diện.
  - `avoid`: nhãn "Nguồn…" góc trên phải, không đặt nội dung đè lên.
  - `brand`: màu nhận diện (navy, lime, cyan, mint).
- Đổi template: thay `overlay.png` (đúng 9:16, vùng ảnh trong suốt) và chỉnh `layout.json` cho khớp. Thiếu file thì hệ thống dùng `overlay-temp.png` + `layout-temp.json`.
- Font: Be Vietnam Pro (OFL, cài qua npm trong `core/remotion`).
