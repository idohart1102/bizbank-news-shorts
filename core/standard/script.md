# Chuẩn kịch bản short tin tức (dưới 60s)

- `hook_text`: một câu < 100 ký tự, hiện suốt video dưới khung ảnh. Gây tò mò (hé lộ quyền lợi/rủi ro, giữ lại chi tiết để video trả lời), ngôn ngữ tự nhiên: không xuồng xã, không khô cứng kiểu công văn; đúng sự thật, không giật tít sai.

Cấu trúc (mốc thời gian gần đúng):
1. **Hook 0–3s**: một câu đánh vào quyền lợi. Ví dụ: "Từ 1/7, hộ kinh doanh doanh thu trên 1 tỷ phải dùng hóa đơn điện tử."
2. **Tin 3–45s**: 1 tin sâu (3 ý) hoặc 3–4 tin ngắn (mỗi tin 8–12s: chuyện gì, áp dụng cho ai, khi nào).
3. **Việc cần làm 45–55s**: chủ shop cần làm gì ngay.
4. **Kết 55–58s**: lời kêu gọi ngắn (theo dõi để không bỏ lỡ tin chính sách; viết «không bỏ lỡ», không viết «không lỡ»).

Luật:
- Tổng ≤ 220 âm tiết. Câu ≤ 20 âm tiết, đọc một hơi.
- Kịch bản là `script.json` (schema `core/schemas/script.schema.json`), chia đoạn. Mỗi đoạn có:
  - `say`: lời đọc cho TTS, số/ký hiệu/viết tắt viết bằng chữ ("một tỷ đồng", "mười phần trăm").
  - `show`: cùng nội dung với `say` nhưng số dạng chữ số ("1 tỷ đồng", "10%"). Không hiển thị thành phụ đề; dùng để canh lúc thẻ/cutout xuất hiện (trigger) và để duyệt.
  - `visual`: mô tả hình nền để Codex tìm/tạo; `source_ids`: nguồn của fact.
  - `cards`: thẻ chữ/số (`value` ≤ 18 ký tự, `label` ≤ 40, `trigger` nguyên văn trong `show`); cả video ≥ 3 thẻ.
  - `cutouts`: người nổi tiếng được nhắc tên (`person`) hoặc sự vật quan trọng (`object`), `trigger` nguyên văn trong `show`.
  - Mỗi đoạn tin có ≥ 1 thẻ hoặc cutout. Không có phụ đề; `show` dùng để canh thời điểm thẻ/cutout và để duyệt.
- `sources`: mỗi nguồn có `quote` trích nguyên văn đoạn chứa số liệu/ngày dùng trong kịch bản.
- Không phán xét chính trị, không suy đoán, không khuyên đầu tư hay pháp lý chắc chắn.
- `script_tts.txt` và `sources.md` do hệ thống sinh từ `script.json`, không viết tay.
- Luật kiểm tự động bằng `core/news/checks.py: lint_script`.
