# News video

Hệ thống tự động làm short tin tức Việt Nam (dưới 60 giây, 9:16) cho hộ kinh doanh và SME: gom tin → chọn → viết → duyệt + kiểm fact → giọng → ảnh → plan dựng → render → QC → gói → hàng chờ đăng.

## Cài trên máy mới (macOS / Linux)

Windows: dùng WSL2 Ubuntu 24.04 và chạy các lệnh dưới đây trong WSL; chưa hỗ trợ PowerShell/CMD trực tiếp.

Cần Git, **uv**, **Node.js 22.x (kèm npm >= 10)**, FFmpeg/ffprobe. Không cần cài hoặc thay Python toàn máy: uv tạo Python **3.12.x** riêng theo `.python-version`. Thư viện khóa phiên bản và SHA-256 tại `requirements.lock`; `requirements.txt` là đầu vào để tạo lại khóa.

- macOS có Homebrew: `brew install uv node@22 ffmpeg git`, sau đó `export PATH="$(brew --prefix node@22)/bin:$PATH"`.
- Ubuntu/WSL2: cài Git và FFmpeg bằng `sudo apt-get update && sudo apt-get install -y git ffmpeg`, cài Node 22 qua nvm (`nvm install 22 && nvm use 22`).
- uv nếu chưa có: theo [hướng dẫn chính thức](https://docs.astral.sh/uv/getting-started/installation/), rồi mở terminal mới hoặc thêm thư mục uv vào PATH.
- Linux: dùng bản phân phối glibc >= 2.35 (khuyến nghị Ubuntu 24.04); Alpine/musl chưa được hỗ trợ. Remotion cần thư viện hệ thống cho Chrome Headless Shell; xem [hướng dẫn Linux chính thức](https://www.remotion.dev/docs/miscellaneous/linux-dependencies) nếu bootstrap/render báo thiếu thư viện `.so`.

```bash
git clone https://github.com/idohart1102/bizbank-news-shorts.git
cd bizbank-news-shorts
bin/bootstrap
bin/news doctor --local
```

Bộ cài cần Internet để tải Python, thư viện, trình duyệt và âm thanh. Chạy lại được khi mạng lỗi; không tạo giọng hay gọi AI. Không chép `.venv`, `node_modules`, `.env`, `config/machine.yaml` từ máy khác.

Tiếp theo sửa `config/machine.yaml` và `.env` trên máy nhận, cài/đăng nhập Claude CLI và Codex CLI, cấu hình 9router và kết nối dịch vụ `platform/tts` (Vbee + căn mốc từ). `platform/tts` là dịch vụ ngoài repo, người nhận phải tự triển khai/kết nối; bootstrap không cài dịch vụ này và không mang theo key. macOS 14+ cùng Xcode Command Line Tools hỗ trợ Apple Vision tách nền ảnh thật; Linux/WSL hoặc macOS cũ sẽ bỏ qua cutout nếu không có ảnh trong suốt dùng được.

```bash
bin/news doctor        # kiểm thêm dịch vụ và CLI; chưa cấu hình thì báo thiếu
bin/news run --dry     # chạy dữ liệu mẫu, không tốn TTS/AI
bin/news run           # chạy một tập thật; --resume last để tiếp tục
bin/news status
.venv/bin/python -m unittest discover -s tests -v
```

## Nâng cấp và khắc phục lệch môi trường

```bash
git pull --ff-only
bin/bootstrap
bin/news doctor --local
```

`bin/news` chỉ dùng `.venv` của dự án và dừng sớm nếu Python/thư viện sai phiên bản. Không sửa bằng cách cài gói vào Python hệ thống. Khi đổi máy/đường dẫn hoặc sai Python, bootstrap giữ môi trường cũ trong `.cache/venv-backups/`, rồi tạo lại; có thể xóa các bản sao sau khi xác nhận chạy tốt. Không ghi đè cấu hình máy hay `.env` đã có.

Nếu báo Node sai phiên bản, dùng `nvm install 22 && nvm use 22`, rồi chạy lại bootstrap. Nếu thiếu FFmpeg/uv, cài công cụ được báo trong hướng dẫn trên. Nếu không tải được âm thanh, kiểm tra kết nối/CDN rồi chạy lại bootstrap. `doctor --local` kiểm cài đặt; `doctor` đầy đủ còn cần dịch vụ/tài khoản bên ngoài. Các CLI cần đăng nhập và hỗ trợ cờ lệnh trong `core/news/agents.py`; doctor chưa xác minh quyền sử dụng từng model.

Hook Git được cài khi bootstrap chạy trong repo Git (kể cả worktree). Nếu đã có hook riêng, bộ cài giữ nguyên và báo cần tích hợp: gọi `.venv/bin/python -I core/scripts/guard_repo.py` trong pre-commit, thêm `pre-push` ở cuối lệnh trong hook pre-push; dùng đường dẫn tính từ `git rev-parse --show-toplevel`. Repo tải dạng ZIP không có hook đến khi `git init` và chạy bootstrap lại.

Đổi thư viện: sửa `requirements.txt`, chạy `uv pip compile requirements.txt --python-version 3.12 --universal --generate-hashes -o requirements.lock`, chạy bootstrap và toàn bộ test. Đổi Node/Remotion: cập nhật `.node-version`, engines, package-lock và kiểm cả CI macOS/Linux. Không nâng bản khóa chỉ để bỏ qua thông báo lỗi.


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
