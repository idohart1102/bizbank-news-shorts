# Luồng chuẩn một video short tin tức (version 1, 2026-11-08)

Chạy tự động bằng `bin/news run` (lịch 10:30, 19:00 hoặc khi được yêu cầu). Mỗi bước có cổng kiểm bằng code; trượt thì tự sửa có giới hạn vòng, hết vòng thì dừng `needs_human`. Chi tiết input/output: `docs/roadmap.md`. Mẫu đạt chuẩn: tập demo 2026-11-08 (mã số thuế trạng thái 06).

| # | Bước | Người làm | Đầu ra trong `<tap>/` | Cổng kiểm soát |
|---|---|---|---|---|
| 1 | Gom tin RSS 48h (`config/sources.yaml`), gộp tin trùng, chấm điểm | script + Codex | `raw_feed.json`, `inbox.json` | Có tin score ≥ 6; link chỉ lấy từ RSS |
| 2 | Chọn tin, viết brief: "ảnh hưởng gì tới túi tiền chủ shop" | Claude | `brief.json` | ≥ 2 nguồn báo hoặc 1 nguồn chính thống; không lặp tin đã làm |
| 3 | Viết kịch bản theo `core/standard/script.md` | Claude | `script.json` (hook_text, đoạn say/show/visual/cards/cutouts), `script_tts.txt`, `sources.md` | `lint_script`: ≤ 220 âm tiết, câu ≤ 20, say không chữ số, ≥ 3 thẻ, mỗi đoạn tin ≥ 1 thẻ/cutout, mỗi thẻ một giá trị |
| 4 | Kiểm fact (Codex đối chiếu bài nguồn) + duyệt (Claude phiên riêng) | Codex + Claude | `qa/factcheck_vN.json`, `qa/review_vN.json` | ≥ 8/10, 0 fact sai, tối đa 3 vòng |
| 5 | Giọng Vbee liền mạch (không hạn mức ký tự) (ngắt nghỉ ngắn nhất) + căn mốc từng từ (Whisper tại máy) | `platform/tts` | `audio/voice.mp3`, `voice.words.json`, `segments.json` | 15–57 giây; mốc hợp lý (2–9 âm tiết/giây) |
| 6 | Ảnh nền (ưu tiên phủ 1080×810) + cutout người/vật | Codex + script | `assets/`, `assets.json` | Mỗi đoạn đủ ảnh (~1 ảnh/3,5s); ghi nguồn từng ảnh |
| 7 | Plan dựng: cảnh, ảnh, chuyển động, tiếng chuyển cảnh | Claude | `edit_plan.json` | `validate_plan`: phủ kín, không lặp ảnh, cảnh ≤ 4s, mỗi đoạn tin có sfx, không cắt cảnh < 1,2s sau khi thẻ hiện |
| 8 | Render Remotion: ảnh → cutout → thẻ → template (trên cùng) → câu hook; nhạc nền nhỏ + sfx | script | `render/final.mp4` | `render_check`: 1080×1920, 30fps, ≤ 59s, -14 LUFS |
| 9 | QC khung hình (contact sheet) | Claude | `qa/qc_vN.json` | 0 lỗi major (gồm: cảnh kêu gọi theo dõi là ảnh trống; thẻ kéo sang cảnh sau); sửa plan + render lại tối đa 2 lần |
| 10 | Tiêu đề, mô tả có nguồn, hashtag | Claude | `meta.json` | Schema; không giật tít |
| 11 | Hàng chờ đăng (chờ đấu nối API) | script | `episodes/outbox/` | — |

Không có phụ đề (Sếp 2026-11-08). Sau mỗi lần chạy: chưng cất bài học → `lessons/rules/<bước>.md`.
