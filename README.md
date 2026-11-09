# News video

Hệ thống tự động làm short tin tức Việt Nam (dưới 60 giây, 9:16) cho hộ kinh doanh và SME: gom tin → chọn → viết → duyệt + kiểm fact → giọng → ảnh → plan dựng → render → QC → gói → hàng chờ đăng.

## Cài đặt

**AI/người nhận repo trên máy mới: đọc [docs/INSTALL.md](docs/INSTALL.md) từ đầu tới cuối.** Có [prompt bàn giao AI](docs/AI_SETUP_PROMPT.md), tiêu chí nghiệm thu, cách cài macOS/Ubuntu/WSL2, TTS, tài khoản model/router, lịch và phục hồi.

Repo có source TTS sạch trong [core/tts](core/tts/README.md). Không kèm key, audio, job database hoặc cache model của máy cũ. Python 3.12 và Node 22 được quản lý riêng; không thay Python mặc định của thiết bị.

Sau khi cài Git, uv, Node 22 (npm >= 10), FFmpeg và Chrome libraries theo INSTALL:

```bash
git clone https://github.com/idohart1102/bizbank-news-shorts.git
cd bizbank-news-shorts
bin/bootstrap --with-tts
bin/news doctor --local
bin/tts model status
NEWS_OFFLINE=1 NEWS_NOTIFY=0 .venv/bin/python -m unittest discover -s tests -v
```

Các lệnh trên không tạo giọng trả phí. Chưa thể chạy thật cho tới khi cấu hình Vbee, Claude/Codex, gateway/model và TTS service. `--with-tts` tải model nhiều GB; nếu chỉ thử dựng dùng `bin/bootstrap`.

```bash
bin/tts key set --provider vbee  # chủ tài khoản nhập tại terminal an toàn
bin/tts serve                  # foreground; terminal khác kiểm status/doctor
bin/news doctor
```

`doctor --local` chỉ kiểm môi trường local; `doctor` không chứng minh mọi model/quota. Lịch trong YAML chưa tự bật scheduler; làm bước 10 của INSTALL. Outbox chưa tự đăng nền tảng.

## Nâng cấp

Xem git status trước; không xóa thay đổi của người vận hành. Dừng lịch đang sở hữu trước khi sửa môi trường:

```bash
git pull --ff-only
bin/bootstrap --with-tts
bin/news doctor --local
bin/tts model status
```

Giữ `.env`, `config/machine.yaml`, `local/` trên máy. Không đưa chúng vào Git hoặc copy công khai. Môi trường sai/di chuyển được giữ ở `.cache/venv-backups` trước khi tạo lại. Khởi động lại dịch vụ và nạp lại lịch theo INSTALL nếu cấu hình/path thay đổi.

Đổi gói có chủ đích: sửa file đầu vào, tạo lại lock có hash, chạy bootstrap/test trước khi phát hành. Không bỏ hash hoặc nâng Python/package chỉ để né lỗi.


```
bin/             news (CLI), bootstrap
config/          channel.yaml (kênh, vào Git), machine.example.yaml → machine.yaml (máy này, không vào Git)
core/news/       máy trạng thái, bước, cổng kiểm, adapter AI/TTS, bài học, thông báo, hàng chờ đăng
core/schemas/    hợp đồng dữ liệu JSON từng bước
core/prompts/    prompt headless từng bước (G4)
core/remotion/   composition NewsShort (G3)
core/scripts/    fetch_sfx, guard_repo, …
core/skills/     skill theo bước; core/standard/ chuẩn kịch bản, template, pipeline
lessons/         luật rút ra từ lỗi và góp ý (rules/<bước>.md)
assets/          sfx (manifest + script tải), template overlay của chủ kênh
docs/            decisions.md (quyết định chủ kênh), roadmap.md
episodes/        dữ liệu các tập: chỉ local, không vào Git
```

Phân vai và luật cứng: `AGENTS.md`. Lộ trình: `docs/roadmap.md`.
