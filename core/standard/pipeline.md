# Luồng chuẩn một video short tin tức

| # | Bước | Người làm | Đầu ra trong `<tap>/` | Cổng kiểm soát |
|---|---|---|---|---|
| 1 | Gom tin 24–48h từ `config/sources.yaml`, gộp tin trùng, chấm độ liên quan tới hộ KD/SME | Codex | `inbox.json` | Mỗi tin có link, giờ đăng, nguồn |
| 2 | Chọn 1 tin chính hoặc 3–4 tin tổng hợp, viết brief: góc nhìn "ảnh hưởng gì tới túi tiền chủ shop" | Claude | `brief.md` | Đủ 2 nguồn/tin |
| 3 | Viết kịch bản theo `core/standard/script.md` | Claude | `script.md`, `sources.md` | ≤ 220 âm tiết |
| 4 | Duyệt kịch bản (phiên mới) + Codex đối chiếu fact với nguồn | Claude + Codex | `qa/script_vN.md` | ≥ 8/10, 0 fact sai, tối đa 3 vòng |
| 5 | Giọng Vbee + srt qua `platform/tts` | script | `audio/voice.mp3`, `audio/voice.srt` | Thời lượng ≤ 57s |
| 6 | Tìm ảnh báo/internet, ảnh AI, chart, ảnh chụp văn bản; mỗi đoạn kịch bản ≥ 1 hình | Codex | `assets/`, `assets.json` | Ghi nguồn từng ảnh |
| 7 | Plan dựng: đoạn, mốc thời gian theo srt, hình, hiệu ứng, chữ nhấn, tiếng động | Claude | `edit_plan.json` | `validate_plan.py`: không khoảng trống, không tĩnh > 2.5s |
| 8 | Render Remotion, template PNG trên cùng | script | `render/final.mp4` | `render_check.py`: 1080×1920, ≤ 59s, âm lượng |
| 9 | QC: phụ đề không đè vùng template, hình khớp lời, chính tả | script + Claude | `qa/qc_vN.md` | Render lại tối đa 2 lần |
| 10 | Tiêu đề, mô tả có nguồn, hashtag | Claude | `meta.md` | Không giật tít sai sự thật |
| 11 | Chốt `final=ok`, Sếp đăng | Claude, Sếp | | |

Chạy song song: bước 5 và 6 cùng lúc; bước 10 trong lúc render.
