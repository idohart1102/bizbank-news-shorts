# Template PNG lớp trên cùng

- File: `assets/template/overlay.png`, 1080×1920, PNG có kênh trong suốt (alpha). Remotion đặt nó **trên cùng** (media → chữ nhấn → phụ đề → overlay), nên mọi vùng có nội dung động phải **trong suốt** trên PNG: `media`, `headline`, `emphasis`, `subtitle`. Phần đặc của PNG chỉ nên nằm ngoài các vùng đó (logo, khung, dải trên, dải dưới `safe_bottom`).
- Kèm `assets/template/layout.json` khai các vùng (pixel):
```json
{
  "media":    {"x": 0,  "y": 260,  "w": 1080, "h": 1180},
  "headline": {"x": 60, "y": 95,   "w": 960,  "h": 150},
  "emphasis": {"x": 60, "y": 1180, "w": 960,  "h": 200},
  "subtitle": {"x": 60, "y": 1470, "w": 960,  "h": 200},
  "safe_bottom": 1680
}
```
- `media`: ảnh/video chính (ảnh ngang tự có nền mờ phía sau, ảnh văn bản/chart hiển thị đủ, không cắt). `headline`: tiêu đề cảnh, ≤ 42 ký tự. `emphasis`: chữ nhấn (số liệu, ngày) bật lên đúng lúc đọc. `subtitle`: phụ đề karaoke tối đa 2 dòng.
- YouTube Shorts che khoảng 300px dưới cùng và cột nút bên phải, nên không đặt chữ quan trọng dưới `safe_bottom` hoặc sát mép phải.
- Chưa có file thật thì hệ thống dùng `overlay-temp.png` (tự vẽ, có nhãn TEMPLATE TẠM) + `layout-temp.json`; `bin/news doctor` báo thiếu.
- Nhiều mẫu (tin nóng, chính sách, tổng hợp tuần): `overlay-<loai>.png` + `layout-<loai>.json`, chọn bằng `template` trong `edit_plan.json`.
- Font: Be Vietnam Pro (OFL, cài qua npm trong `core/remotion`).
