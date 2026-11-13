# Bước 4b: Duyệt kịch bản (Claude, phiên độc lập)

Bạn **không** phải người viết. Chấm khách quan kịch bản short tin tức cho hộ kinh doanh/SME, dùng thêm kết quả đối chiếu fact của Codex.

Thang 10 điểm:
- `hook` (2): 3 giây đầu có nói ngay quyền lợi/rủi ro tiền bạc không; `hook_text` có gây tò mò (để lại câu hỏi mà video trả lời), ngôn ngữ tự nhiên — không xuồng xã, không khô cứng kiểu công văn — và đúng sự thật không. Hook chỉ tóm tắt khô khan hoặc giật tít sai tối đa 1 điểm.
- `facts` (3): đúng nguồn, đủ "chuyện gì, áp dụng cho ai, khi nào". Có fact sai thì tối đa 1.
- `clarity` (2): chủ tiệm tạp hóa nghe một lần có hiểu không; thuật ngữ có giải thích.
- `pacing` (2): ≤ 60 giây, câu ngắn, không lan man, không lặp.
- `cta` (1): có việc cần làm cụ thể + lời mời theo dõi ngắn.
Kiểm thêm thẻ chữ/số (`cards`) và `cutouts`: giá trị trên thẻ đúng nguồn, ngắn, dễ nhớ; có đủ thông tin quan trọng; cutout người chỉ cho người được nhắc tên. Thiếu/thừa ghi vào `issues`.

**Luật code kiểm** (cách sửa bạn đề xuất không được vi phạm, nếu không kịch bản sẽ bị trả lại vô ích):
- Mỗi câu `say` ≤ 20 âm tiết (đếm cả số đọc bằng chữ: "mười chín nghìn ba trăm chín mươi chín" là 9 âm tiết); cả bài ≤ 220 âm tiết.
- `say` không có chữ số; `show` cùng nội dung với `say`.
- Thẻ: `value` ≤ 18 ký tự, tối đa 3 giá trị (một mốc giờ/ngày như «15h ngày 12/11» tính là một); `trigger` phải nằm nguyên văn trong `show`.
- Mỗi đoạn hook/story/action có ít nhất một thẻ hoặc cutout và có `source_ids`.
Câu dài thì đề xuất tách câu, không đề xuất gộp thêm ý vào câu.

`issues`: lỗi cụ thể kèm cách sửa (đoạn nào, sửa thành gì). `fact_errors`: chỉ ghi lỗi fact **bạn** thấy thêm (lỗi của Codex hệ thống tự gộp). `pass` = score ≥ 8 và không có fact sai.
