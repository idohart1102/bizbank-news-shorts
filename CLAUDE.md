# News video — bản đồ định tuyến
`CLAUDE.md` và `AGENTS.md` phải giống hệt nhau: sửa file này thì chép sang file kia.
Kênh short tin tức Việt Nam tổng hợp, dưới 60 giây, dọc 9:16, cho hộ kinh doanh và SME. "Sếp" là người dùng. `<tap>` = `episodes/<YYYY-MM-DD>-<slug>`.

## Ai làm gì
| Ai | Việc |
|---|---|
| Claude Opus 5.5 | Chọn tin, viết kịch bản, duyệt kịch bản (phiên mới, không chấm bài mình viết), lên plan dựng (`edit_plan.json`), duyệt video, chốt bản cuối |
| Codex `cx/gpt-6.1-sol` (qua 9router, lỗi thì Codex CLI) | Gom tin từ nguồn, đối chiếu tư liệu, tìm ảnh thật, tạo ảnh/asset minh họa, kiểm fact kịch bản |
| Remotion | Dựng và render; PNG template của Sếp luôn nằm lớp trên cùng |
| `platform/tts` (provider Vbee) | Giọng đọc + srt. Không giữ key Vbee trong repo |
| Kho `assets/sfx/` (Pixabay) | Tiếng chuyển cảnh, dùng lại mọi tập |
| Sếp | Thiết kế template PNG, đăng YouTube, đổi quyết định trong `docs/decisions.md` |

## Ngôn ngữ
- Trao đổi, báo cáo, QA: tiếng Việt, ngắn gọn.
- Sản phẩm: tiếng Việt chuẩn báo chí, dễ hiểu với chủ hộ kinh doanh; thuật ngữ thuế/pháp lý có giải thích một vế.

## Trình tự
1. Đọc `docs/decisions.md` một lần mỗi phiên; mâu thuẫn thì `decisions.md` thắng.
2. Mở đúng `core/skills/<skill>/SKILL.md` theo bảng, chỉ đọc các file skill nêu.
3. Luồng đầy đủ: `core/standard/pipeline.md`.

| Việc | Skill | Người làm |
|---|---|---|
| Gom tin trong ngày | collect-news | Codex |
| Chọn tin, viết brief | pick-stories | Claude |
| Viết kịch bản | write-script | Claude |
| Duyệt kịch bản + kiểm fact | review-script | Claude (phiên mới) + Codex |
| Giọng đọc + srt | voice | script |
| Ảnh, asset | gather-assets | Codex |
| Plan dựng | plan-edit | Claude |
| Render | render | script |
| QC video | qc-video | script + Claude |
| Tiêu đề, mô tả, hashtag | package | Claude |

## Luật cứng
- Mỗi tin ít nhất 2 nguồn độc lập, hoặc 1 nguồn chính thống (cơ quan nhà nước, văn bản luật). Tin chỉ có trên mạng xã hội thì ghi rõ "theo thông tin lan truyền" hoặc bỏ.
- Số liệu, ngày hiệu lực, mức phạt phải khớp nguyên văn nguồn; ghi link trong `sources.md`.
- Không đọc `node_modules/`, `episodes/*/audio|render|assets`.
- Media của tập không lên Git. Git chỉ chứa hệ thống.
- Mỗi lần tạo giọng đều tốn credit: tạo một lần, chỉ dùng `--replace` khi kịch bản đổi.
