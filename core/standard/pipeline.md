# Luồng chuẩn một video short tin tức (version 1, 2026-11-08)

Cài/chuyển máy: theo `docs/INSTALL.md`; source TTS ở `core/tts`. `schedule` trong YAML không tự bật lịch hệ điều hành.

Hai hướng trên cùng kênh: tin tức (`--kind news`) và kiến thức (`--kind knowledge`); lịch chạy dùng `--kind auto` (cứ 4 tập tin tức thì 1 tập kiến thức, `config/pillars.yaml` `kinds`). Hai hướng chỉ khác bước 1–3; từ bước 4 trở đi dùng chung.

Chạy tự động bằng `bin/news run` (lịch 10:30, 19:00 hoặc khi được yêu cầu). Mỗi bước có cổng kiểm bằng code; trượt thì tự sửa có giới hạn vòng, hết vòng thì dừng `needs_human`. Riêng kịch bản (viết/duyệt) trượt hết vòng khi chưa tạo giọng: tự bỏ tin, chọn tin xếp hạng kế tiếp (tối đa 2 lần; tin Sếp chọn bằng `--story` thì vẫn dừng). Chi tiết input/output: `docs/roadmap.md`. Mẫu đạt chuẩn: tập demo 2026-11-08 (mã số thuế trạng thái 06).

| # | Bước | Người làm | Đầu ra trong `<tap>/` | Cổng kiểm soát |
|---|---|---|---|---|
| 1 | Gom tin RSS 48h (`config/sources.yaml`), gộp tin trùng, chấm điểm, gắn 1 trong 4 chủ đề (`config/pillars.yaml`) | script + Claude Sonnet | `raw_feed.json`, `inbox.json` | Có tin score ≥ 6; link chỉ lấy từ RSS; `pillar` hợp lệ |
| 1k | (kiến thức) Đề xuất 8–12 đề tài từ nguồn tham chiếu (`config/pillars.yaml` `references`) | Claude Sonnet (WebSearch/WebFetch) | `inbox.json` | Có đề tài score ≥ 6; link chỉ thuộc nguồn tham chiếu/danh sách |
| 2 | Chọn tin, viết brief: "ảnh hưởng gì tới túi tiền chủ shop", cân tỷ trọng chủ đề | Claude | `brief.json` (`kind`, `pillar`) | ≥ 2 nguồn báo hoặc 1 nguồn chính thống; không lặp tin đã làm; `pillar` khớp tin chính |
| 3 | Viết kịch bản theo `core/standard/script.md` (kiến thức: `script_knowledge.md`, dạng các bước/lỗi hay gặp/giải thích) | Claude | `script.json` (hook_text, đoạn say/show/visual/cards/cutouts), `script_tts.txt`, `sources.md` | `lint_script`: ≤ 220 âm tiết, câu ≤ 20, say không chữ số, ≥ 3 thẻ, mỗi đoạn tin ≥ 1 thẻ/cutout, mỗi thẻ ≤ 3 giá trị |
| 4 | Kiểm fact (Claude Sonnet đối chiếu bài nguồn) + duyệt (Claude phiên riêng) | Claude Sonnet + Claude Opus | `qa/factcheck_vN.json`, `qa/review_vN.json` | ≥ 8/10, 0 fact sai, tối đa 3 vòng |
| 5 | Giọng VieNeu local + căn mốc từng từ (Whisper tại máy) | `bin/vieneu` + `bin/tts align` | `audio/voice.mp3`, `voice.words.json`, `segments.json` | 15–57 giây; mốc hợp lý (2–9 âm tiết/giây) |
| 6 | Ảnh nền (ưu tiên phủ 1080×810) + cutout người/vật | Claude Sonnet (ảnh thật) + Codex (ảnh AI) + script | `assets/`, `assets.json` | Mỗi đoạn đủ ảnh (~1 ảnh/3,5s); ghi nguồn từng ảnh |
| 7 | Plan dựng: cảnh, ảnh, chuyển động, tiếng chuyển cảnh | Claude | `edit_plan.json` | `validate_plan`: phủ kín, không lặp ảnh, cảnh ≤ 4s, mỗi đoạn tin có sfx, không cắt cảnh < 1,2s sau khi thẻ hiện |
| 8 | Render Remotion: ảnh → cutout → thẻ → template (trên cùng) → câu hook; nhạc nền nhỏ + sfx | script | `render/final.mp4` | `render_check`: 1080×1920, 30fps, ≤ 59s, -14 LUFS |
| 9 | QC khung hình (contact sheet) | Claude | `qa/qc_vN.json` | 0 lỗi major (gồm: cảnh kêu gọi theo dõi là ảnh trống; thẻ kéo sang cảnh sau); sửa plan + render lại tối đa 2 lần |
| 10 | Tiêu đề, mô tả có nguồn, hashtag | Claude | `meta.json` | Schema; không giật tít |
| 11 | Hàng chờ đăng (chờ đấu nối API) | script | `episodes/outbox/` | Video nhắc đối tác (`partner_names`, brief `partner`): dừng chờ người ra lệnh duyệt (`bin/news approve <tap>`); chạy theo lịch thì Sếp duyệt |

Không có phụ đề (Sếp 2026-11-08). Sau mỗi lần chạy: chưng cất bài học → `lessons/rules/<bước>.md`.
