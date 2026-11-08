---
name: qc-video
description: QC video short: khung hình mẫu, thẻ chữ/số, cutout, khung 4:3 của template, hình khớp lời. Tối đa 2 lần sửa plan + render lại.
---
1. Tự động trong `bin/news run` (bước `qc`): trích khung mỗi 1s, ghép contact sheet 4×3 (`qa/frames/sheet-N.jpg`).
2. Claude (phiên riêng, không phải người lên plan) mở từng sheet bằng Read, so với lời theo thời gian (`core/prompts/qc.md`): thẻ tràn/sai chính tả, cutout lỗi hoặc sai người/vật, hình lệch lời, khung lỗi, ảnh AI giả thật. Video không có phụ đề (cố ý).
3. Ghi `qa/qc_vN.json`. Có lỗi `major` → góp ý vào `qa/feedback_plan.json`, làm lại plan + render (tối đa 2 vòng), hết vòng thì `needs_human`.
