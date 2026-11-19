# News video — bản đồ định tuyến
`AGENTS.md` là bản duy nhất; `CLAUDE.md` chỉ chứa dòng `@AGENTS.md`.
Kênh short Việt Nam, dưới 60 giây, dọc 9:16, cho hộ kinh doanh và SME. Hai hướng trên cùng kênh và template: tin tức (4/5) và kiến thức (1/5, giai đoạn 2), 4 chủ đề Vốn, Quản trị thông minh, Luật DN/HKD, AI Marketing (`config/pillars.yaml`). "Sếp" là người dùng. `<tap>` = `episodes/<YYYY-MM-DD>-<slug>`.

## Ai làm gì
| Ai | Việc |
|---|---|
| Claude Opus 5.5 | Chọn tin, viết kịch bản, duyệt kịch bản (phiên mới, không chấm bài mình viết), lên plan dựng (`edit_plan.json`), duyệt video, chốt bản cuối |
| Claude Sonnet 5.5 | Gom tin từ nguồn, kiểm fact kịch bản (đối chiếu tư liệu), tìm ảnh thật |
| Codex CLI (`image_gen` tích hợp) | Tạo ảnh/asset minh họa AI bằng tài khoản Codex của máy; không qua 9router |
| Remotion | Dựng và render; PNG template của Sếp luôn nằm lớp trên cùng; không có phụ đề, thông tin quan trọng đi vào thẻ chữ/số và cutout |
| `bin/vieneu` + `bin/tts align` | VieNeu tạo giọng local, Whisper căn mốc từng từ. Source/model/venv VieNeu ở `local/vieneu`, không vào Git |
| Kho `assets/sfx/` (Pixabay) | Tiếng chuyển cảnh, dùng lại mọi tập |
| Sếp | Thiết kế template PNG, đăng YouTube, đổi quyết định trong `docs/decisions.md` |

## Ngôn ngữ
- Trao đổi, báo cáo, QA: tiếng Việt, ngắn gọn.
- Sản phẩm: tiếng Việt chuẩn báo chí, dễ hiểu với chủ hộ kinh doanh; thuật ngữ thuế/pháp lý có giải thích một vế.

## Trình tự
1. Đọc `docs/decisions.md` một lần mỗi phiên; mâu thuẫn thì `decisions.md` thắng.
2. Mở đúng `core/skills/<skill>/SKILL.md` theo bảng, chỉ đọc các file skill nêu.
3. Luồng đầy đủ: `core/standard/pipeline.md`. Lộ trình xây hệ thống, input/output từng bước: `docs/roadmap.md`.
4. Chạy tự động: `bin/news run` (lịch 10:30, 19:00); `bin/news status`, `bin/news run --resume last`. Nguồn ngoài danh sách ưu tiên chờ Sếp duyệt: `bin/news sources pending|approve|reject <tên miền>`. Máy mới/cài lại/chuyển máy: đọc `docs/INSTALL.md` trước khi chạy; prompt bàn giao ở `docs/AI_SETUP_PROMPT.md`. `bin/bootstrap --with-tts` cài Whisper; `bin/vieneu install` tải VieNeu riêng theo `docs/VIENEU.md`. Chưa tự bật dịch vụ/lịch.
5. Lệnh nhanh cho Sếp: `/chonchude` (tìm 3–5 chủ đề hợp trend, dừng chờ chọn), `/taovideo [id]` (chạy hết tới bước package). Skill ở `.claude/skills/`; AI khác đọc trực tiếp file `SKILL.md` ở đó.
6. Bài học: luật đã rút ra nằm ở `lessons/rules/<bước>.md`, bắt buộc tuân theo. Góp ý của Sếp: `bin/news feedback <tap> <bước> "<nội dung>"`.

| Việc | Skill | Người làm |
|---|---|---|
| Gom tin trong ngày | collect-news | Claude Sonnet |
| Chọn tin, viết brief | pick-stories | Claude |
| Viết kịch bản | write-script | Claude |
| Duyệt kịch bản + kiểm fact | review-script | Claude Opus (phiên mới) + Claude Sonnet |
| Giọng đọc + mốc từng từ | voice | script |
| Ảnh, asset | gather-assets | Claude Sonnet (ảnh thật) + Codex (ảnh AI) |
| Plan dựng | plan-edit | Claude |
| Render | render | script |
| QC video | qc-video | script + Claude |
| Tiêu đề, mô tả, hashtag | package | Claude |

## Luật cứng
- Mỗi tin ít nhất 2 nguồn độc lập, hoặc 1 nguồn chính thống (cơ quan nhà nước, văn bản luật). Tin chỉ có trên mạng xã hội thì ghi rõ "theo thông tin lan truyền" hoặc bỏ.
- Số liệu, ngày hiệu lực, mức phạt phải khớp nguyên văn nguồn; ghi link và trích nguyên văn (`quote`) trong `script.json`.
- Không đọc `node_modules/`, `episodes/*/audio|render|assets`.
- Repo là hệ độc lập, chuyển giao được: không đường dẫn máy, bí mật, dữ liệu sản phẩm/video. Dữ liệu các tập, hàng chờ đăng, sự kiện bài học thô chỉ ở local; hook `core/scripts/guard_repo.py` chặn khi commit/push.
- VieNeu chạy local không tốn credit Vbee. Tạo một lần, dùng lại audio đúng yêu cầu; chỉ dùng `--replace` khi kịch bản đổi. Khi chọn Vbee, mỗi lần tạo vẫn tốn credit, không tự gửi lại.
