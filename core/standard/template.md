# Template PNG lớp trên cùng

- File: `assets/template/overlay.png` (Template 2 BizBank, 1080×1920, RGBA), nằm **trên cùng**.
- Khung ảnh/video **4:3: x 0–1080, y 300–1110 (1080×810)**. Vùng hoàn toàn trong suốt y 340–1069; hai dải 40 px trên/dưới là bóng mờ của template.
- Thứ tự lớp: ảnh nền → cutout → thẻ chữ/số (cả ba bị cắt theo khung 4:3, phóng/lia/trượt không ra ngoài khung) → overlay → câu hook. **Không có phụ đề.**
- Phóng ảnh vừa đủ: mức phóng tối đa tính từ độ phân giải ảnh gốc (1 điểm ảnh gốc ≥ 1 điểm video, tối đa 1,15; ảnh nhỏ hơn khung chỉ 1,04). Lia trong giới hạn để mép ảnh không lộ.
- Ảnh sưu tầm ưu tiên phủ được 1080×810 không cần phóng (≈ ≥ 1080p); nhỏ hơn chỉ khi không có ảnh khác. Ảnh AI tạo ngang 1536×1024.
- `assets/template/layout.json`: `media` (khung 4:3), `clear` (vùng trong suốt), `cards` (thẻ chữ/số, góc dưới trong vùng trong suốt), `cutout`, `hook` (câu hook dưới ba vạch màu), `brand` (navy #081840, lá mạ #B8D03E, xanh dương #4AA0EA, bạc hà #B2E0CA).
- Thẻ chữ/số: nền navy, ba vạch lá mạ/xanh/bạc hà như template, số trắng, nhãn bạc hà; bật lên kèm pop/ding. Có cutout thì thẻ né sang phía đối diện.
- Câu hook (`hook_text` trong script.json, < 100 ký tự): chữ trắng đậm, đứng yên suốt video.
- Font: Be Vietnam Pro (OFL, cài qua npm trong `core/remotion`).
