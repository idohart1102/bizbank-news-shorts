# Chuẩn kịch bản short kiến thức (dưới 60s)

Dùng cho tập `kind = knowledge`. Mọi luật kỹ thuật của `core/standard/script.md` vẫn áp dụng (schema `script.json`, `say`/`show`, thẻ, cutout, ≤ 220 âm tiết, câu ≤ 20 âm tiết, `lint_script`). Khác ở nội dung và cấu trúc:

- `hook_text`: một câu < 100 ký tự nêu **vấn đề hoặc lợi ích** của chủ shop, giữ lại lời giải cho video. Ví dụ: "Vay Quỹ DNNVV lãi thấp: hồ sơ cần mấy giấy?", "3 lỗi khiến quảng cáo TikTok Shop đốt tiền".

Cấu trúc (mốc thời gian gần đúng, `role` giữ như tin tức):
1. **Hook 0–3s** (`hook`): một câu nêu nỗi đau/lợi ích cụ thể.
2. **Nội dung 3–45s** (`story`, 2–4 đoạn): theo `format` của brief:
   - `steps`: các bước làm theo thứ tự, mỗi đoạn một bước, thẻ «Bước 1», «Bước 2»… kèm việc cụ thể.
   - `mistakes`: các lỗi hay gặp, mỗi đoạn một lỗi + cách tránh.
   - `explainer`: giải thích một khái niệm/quy định: là gì → áp dụng cho ai → điều kiện/con số chính.
3. **Áp dụng 45–55s** (`action`): chủ shop làm gì ngay hôm nay (một việc cụ thể, nơi làm, giấy tờ cần).
4. **Kết 55–58s** (`cta`): mời theo dõi để «không bỏ lỡ» kiến thức kinh doanh.

Luật nội dung:
- Dạy **một** đề tài, không lan man. Mỗi đoạn `story` là một ý, có thẻ hoặc cutout.
- Kiến thức phải có trong "Văn bản nguồn"; số liệu, mức phí, thời hạn, điều kiện khớp nguyên văn và có `quote`. Kinh nghiệm chung từ nguồn nước ngoài (HBR, HubSpot) được diễn đạt lại, không gán số liệu nước ngoài cho Việt Nam.
- Không nêu tên, không quảng bá đối tác/sản phẩm cụ thể trừ khi brief có `partner`; có `partner` thì video phải được người ra lệnh duyệt trước khi đăng.
- Kiến thức thuế/pháp lý/vay vốn: nói đúng điều kiện áp dụng, kết bằng gợi ý hỏi cơ quan thuế, ngân hàng hoặc luật sư cho trường hợp cụ thể; không hứa chắc kết quả.
