---
name: qc-video
description: QC video short: khung hình mẫu, phụ đề, vùng template, hình khớp lời. Tối đa 2 lần render lại.
---
1. Script trích khung hình mỗi 1s, kèm srt.
2. Claude (không phải người lên plan) chấm: chữ không đè vùng template, không bị che bởi UI Shorts, chính tả, hình khớp lời, không cảnh đứng hình.
3. Ghi `qa/qc_vN.md`, đề xuất sửa `edit_plan.json`.
