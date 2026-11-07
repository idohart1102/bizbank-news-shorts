# Template PNG lớp trên cùng

- File: `assets/template/overlay.png`, 1080×1920, PNG có kênh trong suốt (alpha). Vùng trong suốt là chỗ hiện hình/video bên dưới.
- Kèm `assets/template/layout.json` khai các vùng (pixel). Plan dựng và phụ đề chỉ đặt nội dung vào đúng vùng:
```json
{
  "media":    {"x": 0,  "y": 300,  "w": 1080, "h": 1100},
  "headline": {"x": 60, "y": 120,  "w": 960,  "h": 160},
  "subtitle": {"x": 60, "y": 1450, "w": 960,  "h": 220},
  "safe_bottom": 1700
}
```
- Số trên là ví dụ; Sếp chốt theo thiết kế thật. YouTube Shorts che khoảng 300px dưới cùng và cột nút bên phải, nên không đặt chữ quan trọng ở đó.
- Có nhiều mẫu (tin nóng, chính sách, tổng hợp tuần) thì đặt `overlay-<loai>.png` + `layout-<loai>.json`, chọn trong `edit_plan.json`.
