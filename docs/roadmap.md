# Lộ trình xây dựng và tự động hóa (2026-11-07)

Mục tiêu: một lệnh (hoặc lịch launchd mỗi sáng) đi từ "hôm nay" tới `final.mp4` + `meta.json`, có thể tự đăng, không cần người can thiệp. Người chỉ nhận báo cáo và xử lý khi hệ thống tự dừng ở cổng an toàn.

```
launchd 10:30 + 19:00 ─▶ news run ─▶ [1 gom] ─▶ [2 chọn] ─▶ [3 viết] ⇄ [4 duyệt+fact] ─▶ [5 giọng] ┬▶ [7 plan] ─▶ [8 render] ⇄ [9 QC] ─▶ [10 gói] ─▶ [11 đăng/Drive] ─▶ báo cáo
                                                                                   [6 ảnh]  ┘
```

## 1. Nguyên tắc để chạy tự động 100%

1. **Mỗi bước là hàm thuần trên thư mục tập**: đọc file đầu vào cố định, ghi file đầu ra cố định, có schema JSON. Không bước nào phụ thuộc trí nhớ của phiên chat.
2. **Máy trạng thái** `<tap>/state.json`: chạy lại lệnh thì tiếp đúng chỗ dở, bỏ qua bước đã xong (so mã băm đầu vào). Không cần biết lần trước dừng vì sao.
3. **Cổng kiểm soát là code, không phải người**: validator tất định (đếm âm tiết, thời lượng, độ phủ plan, độ phân giải, LUFS) + LLM chấm ở phiên riêng. Trượt thì quay vòng sửa với ngân sách số vòng; hết vòng thì dừng ở `needs_human` và báo, không đăng bừa.
4. **Bước tốn tiền chỉ chạy một lần**: giọng Vbee khóa theo mã băm `script_tts`; ngân sách ký tự/ngày trong `config/channel.yaml`.
5. **AI gọi headless qua adapter**: `claude -p` (skill + tool giới hạn, xuất JSON) và Codex qua 9router `cx/gpt-6.1-sol`, lỗi thì `codex exec`. Adapter ghi prompt/kết quả vào `<tap>/logs/`.
6. **Một nguồn sự thật cho kịch bản**: `script.json` theo đoạn, mỗi đoạn có `say` (lời đọc, số bằng chữ) và `show` (phụ đề, chữ số). Bỏ cặp `script.md` / `script_tts.md` rời nhau, vì SRT căn theo lời đọc sẽ không khớp chữ hiển thị.

## 2. Input

### 2.1 Sếp đưa một lần (đang chờ)
| Input | Dùng cho | Nếu chưa có |
|---|---|---|
| `assets/template/overlay.png` 1080×1920 alpha + `layout.json` | Lớp trên cùng, vùng media/headline/phụ đề | Dùng overlay tạm do hệ thống vẽ, đánh dấu `TEMP` |
| Nhạc nền có/không (+ âm lượng) | Bước render | Không nhạc |
| Thư mục Drive | Lưu bản cuối + gói tư liệu | Chỉ lưu local |
| GitHub private `idohart1102/youtube-news-video` | Sao lưu hệ thống | Chỉ Git local |
| API các nền tảng (YouTube, TikTok, Facebook) | Bước 11 | **Đã chốt**: xếp `publish/outbox`, trạng thái `pending_connection`, Sếp đấu nối sau |
| Giờ chạy, số tập/ngày, ngân sách ký tự Vbee/ngày | launchd + giới hạn chi phí | **Đã chốt**: 10:30 và 19:00, 1 tập/lần, 3.000 ký tự/ngày |
| Bot Telegram (token + chat id) | Báo `needs_human` và báo cáo | **Đã chốt** Telegram, đấu nối sau; tạm `notifications.jsonl` + macOS notification |

### 2.2 Hệ thống có sẵn
| Input | Trạng thái |
|---|---|
| `platform/tts` provider Vbee + SRT Whisper | Xong 2026-11-07 |
| `config/channel.yaml`, `config/sources.yaml` | Có; cần thêm RSS/sitemap từng báo |
| `assets/sfx/` ~20 tiếng Pixabay + `LICENSES.csv` | Chưa |
| Font tiếng Việt (Be Vietnam Pro / Montserrat, OFL) trong `assets/fonts/` | Chưa |
| Claude CLI, Codex CLI, 9router `127.0.0.1:20128` | Có trên máy |

### 2.3 Mỗi lần chạy
Chỉ có **ngày** (mặc định hôm nay) và tùy chọn `--slug`, `--story <url>` (ép chọn tin). Còn lại tự lấy từ config.

## 3. Output và hợp đồng dữ liệu

Mỗi tập là `episodes/<YYYY-MM-DD>-<slug>/` (không vào Git). Schema nằm ở `core/schemas/*.schema.json`, validator dùng chung `core/scripts/check_schema.py`.

| # | Bước | Người làm | Input | Output | Cổng tự động | Trượt thì |
|---|---|---|---|---|---|---|
| 0 | Tạo tập | script | ngày | `state.json`, cây thư mục | — | — |
| 1 | Gom tin | `fetch_feeds.py` + Codex | `sources.yaml` | `raw_feed.json`, `inbox.json` (tin: title, urls[], tier, published_at, summary, impact, score) | ≥ 3 tin score ≥ 6, mỗi tin có link + giờ đăng trong 48h | Mở rộng 72h; vẫn thiếu thì `needs_human` (ngày không có tin) |
| 2 | Chọn tin | Claude | `inbox.json`, `decisions.md` | `brief.json` (dạng video, hook, 3 ý, việc cần làm, nguồn, mẫu template) | Mỗi tin đủ 2 nguồn hoặc 1 tier 1; không trùng tin 7 ngày qua (`episodes/index.jsonl`) | Chọn tin kế tiếp |
| 3 | Viết | Claude | `brief.json`, `standard/script.md` | `script.json` (segments: id, say, show, visual, source_ids), `sources.md` | `lint_script.py`: ≤ 220 âm tiết, câu ≤ 20 âm tiết, mỗi câu fact có `[n]`, mỗi đoạn có `visual`, số trong `show` khớp số đọc trong `say` | Trả lỗi cho writer, tối đa 3 vòng |
| 4 | Duyệt + fact | Claude phiên mới + Codex | `script.json`, `sources.md` | `qa/script_vN.json` (điểm, fact sai[], sửa đề xuất) | ≥ 8/10 và 0 fact sai | Về bước 3; quá 3 vòng → `needs_human` |
| 5 | Giọng | `tts` | `say` ghép từ `script.json` | `audio/voice.mp3`, `voice.srt`, `voice.words.json`, `audio/segments.json` (mốc từng đoạn) | 20–57s; align match ≥ 0,85 | > 57s: về bước 3 cắt chữ (không tăng tốc > 1,1x); lỗi API `uncertain` → dừng, báo |
| 6 | Ảnh | Codex (+ script tải/chuẩn hóa) | `script.json.visual`, `layout.json` | `assets/*.jpg|png`, `assets.json` (id, file, segment, kind real/doc/chart/ai, source_url, w, h) | Mỗi đoạn ≥ 1 hình (≥ 2 nếu đoạn > 5s), cạnh ngắn ≥ 720px, có source_url, ảnh AI không giả người/sự kiện thật | Chart/ảnh chụp văn bản tự dựng; cuối cùng là thẻ chữ |
| 7 | Plan dựng | Claude | script, `segments.json`, `words.json`, `assets.json`, `layout.json`, `sfx/index.json` | `edit_plan.json` | `validate_plan.py`: phủ kín 0→hết audio, không cảnh tĩnh > 2,5s, chữ trong vùng layout, sfx ≤ 1/1,5s, asset tồn tại | Trả lỗi cho Claude, tối đa 3 vòng |
| 8 | Render | `render.py` (Remotion) | `edit_plan.json` + media + overlay | `render/final.mp4` | `render_check.py`: 1080×1920, 30fps, ≤ 59s, −14 LUFS ±1, không khung đen | Lỗi code → `needs_human` |
| 9 | QC | `qc_frames.py` + Claude (khác phiên plan) | `final.mp4`, srt, script | `qa/qc_vN.json`, `qa/contact_sheet.jpg` | 0 lỗi nặng (chữ đè template, sai chính tả, hình lệch lời, che bởi UI Shorts) | Sửa `edit_plan.json` → render lại, tối đa 2 lần |
| 10 | Gói | Claude | script, sources | `meta.json` (title ≤ 60 ký tự, description + nguồn, tags) | Không giật tít: Claude kiểm title so với fact | Viết lại 1 lần |
| 11 | Đăng / lưu | `publish.py` | `final.mp4`, `meta.json` | `publish/outbox/<tap>.<platform>.json` (`pending_connection`), bản sao Drive khi có, `episodes/index.jsonl` | Adapter nền tảng nào `enabled` mới gửi; chưa có thì giữ hàng chờ | Lỗi → giữ file, báo |
| — | Báo cáo | script | `state.json`, qa | `report.md` + thông báo (`notify.py`: Telegram khi bật, tạm jsonl + macOS) | — | — |

`state.json` mẫu:
```json
{"tap": "2026-11-08-hoa-don-dien-tu", "status": "running|done|needs_human|failed",
 "steps": {"voice": {"state": "done", "input_hash": "…", "attempts": 1, "cost": {"vbee_chars": 912}}},
 "blocker": null}
```

## 4. Cấu trúc repo đích

```
bin/news                      # CLI: new | run | step <x> | status | report
core/schemas/                 # inbox, brief, script, assets, edit_plan, qa, meta, state
core/scripts/
  pipeline.py                 # máy trạng thái, khóa chạy đơn, ngân sách, retry
  agents.py                   # adapter claude -p / 9router / codex exec, ghi log
  new_episode.py  fetch_feeds.py  lint_script.py  voice.py  fetch_assets.py
  validate_plan.py  render.py  render_check.py  qc_frames.py  publish.py  notify.py
core/prompts/                 # prompt từng bước cho headless, trỏ tới core/skills/*
core/remotion/                # package.json ghim version; NewsShort: media → chữ nhấn → phụ đề → overlay
assets/sfx/  assets/fonts/  assets/template/
ops/com.idohart.news-video.plist   # lịch launchd 10:30 + 19:00
publish/adapters/            # youtube.py, tiktok.py... (Sếp đấu nối sau), outbox/ không vào Git
tests/                        # tập mẫu cố định (fixture) chạy offline: lint, validate, render 5s
lessons/rules/<step>.md       # luật đã thăng hạng (vào Git); candidates.yaml
config/machine.example.yaml  .env.example   bin/bootstrap
```

## 5. Các giai đoạn

| GĐ | Việc | Xong khi |
|---|---|---|
| G0 ✅ | Khung repo, provider Vbee + SRT | Gọi Vbee thật OK |
| G1 Nền | schemas, `new_episode`, `pipeline.py` (state, resume, lock, ngân sách), adapter TTS/LLM, `machine.example.yaml`, `bin/bootstrap`, `news doctor`, ghi sự kiện bài học, `bin/news`, chuyển skill sang `script.json` | `news run --dry` chạy hết 11 bước với stub, resume được giữa chừng; clone sạch vào thư mục khác vẫn chạy |
| G2 Kho | ✅ 20 sfx (manifest + `fetch_sfx.py`, sha256, LUFS); còn font OFL, overlay tạm | Validator thấy đủ loại whoosh/pop/ding/swoosh/riser/click |
| G3 Dựng | Remotion NewsShort (ken-burns/zoom/pan/split, chữ nhấn theo `words.json`, phụ đề karaoke theo `show`), `validate_plan`, `render`, `render_check` | Render fixture 30s ra 1080×1920, đạt check |
| G4 Nội dung | `fetch_feeds` (RSS/sitemap), prompt + adapter cho bước 1–4, `lint_script` | Từ ngày bất kỳ ra `script.json` đạt QA |
| G5 Media | `voice.py`, `fetch_assets` (Codex tìm ảnh → script tải, chuẩn hóa, ghi nguồn; chart tự dựng), prompt plan-edit | Có `edit_plan.json` hợp lệ từ tập thật |
| G6 Kết | QC khung hình + Claude vision, `meta.json`, `publish.py` (outbox), `notify`, `report`, chưng cất bài học | Một lệnh ra video + báo cáo; clone từ GitHub vào thư mục sạch chạy được, không có dữ liệu tập nào |
| G7 Chạy thật | Tập thử với tin hôm nay (có người xem kết quả), rồi 3 ngày chạy lịch (10:30, 19:00) với outbox, sửa lỗi; Sếp đấu nối API đăng + Telegram khi sẵn sàng | 3 tập liên tiếp không cần sửa tay |

Thứ tự Sếp giao trước đây khớp như sau: việc 2 = G2, việc 3 = G1 + G3, việc 4 = G7.

## 6. Repo độc lập, chuyển giao được

Mục tiêu: người khác clone repo trên máy Mac/Linux bất kỳ, chạy `bin/bootstrap` → `news doctor` → `news run` là có video, không cần IDOHART UNIVERSE, không thấy video/tin/dữ liệu sản phẩm nào của chủ cũ.

| Nguyên tắc | Cách làm |
|---|---|
| Không đường dẫn máy, không bí mật trong Git | `config/machine.yaml` + `.env` không vào Git; có `machine.example.yaml`, `.env.example`. Key đọc từ env hoặc Keychain. `news doctor` báo thiếu gì |
| Phụ thuộc ngoài qua adapter, có bản dự phòng tự chứa | TTS: `platform_tts` (máy này) hoặc `vbee_direct` (client Vbee + căn Whisper đóng gói trong repo). LLM: `claude_cli` / `anthropic_api`; Codex: `9router` / `codex_cli` / `openai_api`. Chọn trong `machine.yaml` |
| Cài một lệnh | `bin/bootstrap`: venv Python ghim version, `npm ci` cho Remotion, `fetch_sfx.py`, tải font OFL, kiểm ffmpeg |
| Tài sản có license không phân phối lại | Chỉ commit manifest + script tải (`assets/sfx/LICENSES.csv`), không commit file |
| Dữ liệu chạy tách khỏi hệ thống | `episodes/`, `publish/outbox/`, log, chỉ số: không vào Git; đường dẫn đặt được qua `NEWS_DATA_DIR` |
| Không đưa lịch sử sản phẩm lên GitHub | Git chỉ chứa hệ thống (lịch sử commit của hệ thống vẫn giữ). Mọi thứ về video đã làm ở local: `episodes/`, `episodes/index.jsonl` (danh sách tin đã làm), `publish/outbox/`, `notifications.jsonl`, sự kiện bài học thô, chỉ số, log: không bao giờ vào Git. Chốt chặn: `.gitignore` + hook pre-commit/pre-push `core/scripts/guard_repo.py` từ chối file media, file trong vùng dữ liệu, file > 2 MB, và luật bài học có link/tên tập. `bin/bootstrap` tự cài hook |
| Danh tính chủ kênh là cấu hình | Tên kênh, đối tượng, giọng, lịch, nền tảng nằm trong `config/channel.yaml`; tài liệu viết "chủ kênh", không gắn người cụ thể |

## 7. Cơ chế bài học (hệ thống tự cải thiện)

```
lỗi ở cổng / góp ý của chủ kênh ─▶ sự kiện (local) ─▶ chưng cất (Claude) ─▶ ứng viên ─▶ luật đang áp dụng ─▶ nạp vào prompt bước tương ứng
                                                                                     └▶ đủ cụ thể → biến thành validator code
```

1. **Ghi sự kiện** (tự động, không vào Git): mỗi lần cổng trượt (lint, duyệt, fact, validate_plan, render_check, QC) hoặc chủ kênh góp ý (`news feedback <tap> "…"`), ghi `episodes/<tap>/lessons.jsonl`: `{step, gate, kind, detail, fix_applied, rounds}`.
2. **Chưng cất** cuối mỗi lần chạy: Claude gom sự kiện mới, viết thành luật tổng quát (không chứa nội dung tin, tên người, link) vào `lessons/candidates.yaml`: `{id, step, rule, why, evidence: số tập, first_seen, last_seen}`.
3. **Thăng hạng**: ứng viên lặp ≥ 2 tập, hoặc đến từ góp ý của chủ kênh, được chuyển vào `lessons/rules/<step>.md` (vào Git). Prompt của mỗi bước tự nạp đúng file luật của bước đó.
4. **Cứng hóa**: luật kiểm được bằng code (ví dụ "không viết tắt BHXH khi chưa giải thích") được chuyển thành check trong validator, ghi `enforced_by`. Luật trong prompt giữ ngắn.
5. **Đo và dọn**: `lessons/metrics` local ghi tỷ lệ qua cổng lần đầu, số vòng sửa, chi phí theo bước. `news lessons review` (hằng tuần, chạy cùng lịch) báo luật nào giúp giảm lỗi, luật nào 30 ngày không còn tác dụng thì đề xuất bỏ. Luật mâu thuẫn `decisions.md` bị chặn.
6. **An toàn**: bài học không được nới lỏng luật cứng (2 nguồn, khớp số liệu, ngân sách credit); chỉ chủ kênh sửa được những luật đó qua `decisions.md`.

## 8. Rủi ro và cách chặn
- **Fact sai**: luật 2 nguồn trong cổng bước 2, Codex mở link đối chiếu nguyên văn ở bước 4, Claude kiểm title ở bước 10. Không đạt thì không đăng.
- **Tốn credit ngoài ý muốn**: bước giọng khóa theo mã băm, có ngân sách ký tự/ngày, `uncertain` luôn dừng.
- **Trang báo đổi cấu trúc / chặn bot**: dùng RSS trước, Codex duyệt web làm phương án hai, cảnh báo khi một nguồn 0 tin 3 ngày liền.
- **Ảnh lỗi/kém**: tải về rồi kiểm kích thước, mã băm trùng, ảnh trắng; thiếu thì tự dựng chart/thẻ chữ.
- **Chạy chồng**: file khóa trong `episodes/.lock`; launchd không khởi động lần hai.
- **Bản quyền**: Sếp chấp nhận rủi ro (decisions.md); hệ thống vẫn ghi nguồn trong `assets.json` và mô tả video.
