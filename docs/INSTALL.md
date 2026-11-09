# Cài đặt và nghiệm thu trên thiết bị mới

Tài liệu dành cho người vận hành và AI có terminal. Đọc `AGENTS.md`/`CLAUDE.md`, `docs/decisions.md`, rồi làm theo thứ tự dưới đây. [Prompt bàn giao cho AI](AI_SETUP_PROMPT.md). Không lấy đường dẫn, key hay data từ máy tác giả.

## 1. Xác định mức hoàn tất

| Mức | Bằng chứng cần có |
|---|---|
| Môi trường local đạt | bootstrap, doctor --local, toàn bộ test và render mẫu đều exit 0 |
| Dịch vụ đạt | TTS CLI + thư viện + model cache offline + service + Vbee key; Claude/Codex đăng nhập; router/model sẵn sàng |
| Chạy thật đạt | một tập được chủ máy cho phép, vượt cổng kiểm và tạo final.mp4/meta/outbox; không coi test giả là bằng chứng truy cập model thật |
| Tự động đạt | lịch hệ điều hành đã cài và được kiểm tra bằng tài khoản/PATH dùng khi chạy nền |

`doctor --local` không kiểm tài khoản, model hoặc tạo giọng. `doctor` kiểm CLI, health và router; không chứng minh mọi endpoint/model/quota hoạt động. Không tự chạy bước trả phí để biến báo cáo thành “đạt”. Thiếu quyền/tài khoản thì nêu đúng phần bị chặn, hoàn tất phần độc lập trước.

## 2. Khảo sát máy và chọn nhánh

Chạy trong terminal POSIX (bash/zsh; Windows dùng WSL2):

```bash
uname -sm
pwd
date '+%Y-%m-%d %H:%M:%S %Z %z'
df -h .
command -v git uv node npm ffmpeg ffprobe
```

macOS: thêm `sw_vers`. Linux: thêm `cat /etc/os-release`, `ldd --version`, `free -h`. Ghi OS, kiến trúc CPU, shell, user thực thi, proxy/mạng và ổ đĩa còn trống. Model/venv/Chrome cần nhiều GB; kiểm lại dung lượng khi tải thất bại. Không dùng `sudo` để chạy bootstrap, pip, npm global, news hoặc tts.

| Thiết bị | Môi trường dựng | Căn từ TTS | Cutout ảnh thật |
|---|---|---|---|
| Mac Apple Silicon | Node 22 + Python 3.12 | MLX/Whisper large-v3-turbo | Apple Vision nếu macOS >= 14 và có swiftc |
| Mac Intel | tương tự | faster-whisper CPU/int8 | Apple Vision nếu OS/SDK hỗ trợ |
| Ubuntu 24.04 x86_64 | glibc + Chrome shared libraries | faster-whisper CPU/int8 | chưa có adapter tách nền; có thể bị bỏ qua |
| WSL2 Ubuntu 24.04 | như Ubuntu, cài trong filesystem Linux | CPU như Linux | như Linux |

Linux ARM64 phụ thuộc wheel của CTranslate2/Remotion; không coi là đã nghiệm thu nếu pip/render chưa qua. Alpine/musl không nằm trong phạm vi hỗ trợ. Không cài trực tiếp bằng PowerShell/CMD. WSL không đảm bảo máy tiếp tục chạy khi Windows ngủ hoặc tắt.

Giờ bản tin là 10:30 và 19:00 Việt Nam. Kiểm timezone trước khi bật lịch. Giữ clock/NTP đúng để lọc RSS và thời gian tập không sai.

## 3. Cài công cụ hệ thống

### macOS

1. Nếu chưa có Homebrew, cài theo [brew.sh](https://brew.sh), hoàn tất các lệnh “Next steps” mà installer in ra để `brew` có trong PATH.
2. Cài công cụ:

```bash
brew install git uv node@22 ffmpeg
export PATH="$(brew --prefix node@22)/bin:$PATH"
git --version
uv --version
node --version
npm --version
ffmpeg -version
ffprobe -version
```

Node phải là `v22.x`, npm >= 10. Lưu dòng bổ sung PATH phù hợp vào profile của user nếu cần; mở terminal mới và kiểm lại. Không thay PATH bằng đường dẫn máy người khác. Khi cần Apple Vision: `xcode-select --install`, hoàn tất UI cài SDK rồi kiểm `xcrun --find swiftc`. Có thể bỏ bước này nếu chấp nhận chưa có cutout ảnh thật.

### Ubuntu 24.04 / WSL2

Nếu chưa có WSL2, làm theo [Microsoft WSL](https://learn.microsoft.com/windows/wsl/install), chọn Ubuntu 24.04, mở shell Ubuntu. Các lệnh tiếp theo chạy trong Linux, repo nên nằm trong home Linux thay vì `/mnt/c`.

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates ffmpeg \
  libnss3 libdbus-1-3 libatk1.0-0 libasound2t64 libxrandr2 \
  libxkbcommon-dev libxfixes3 libxcomposite1 libxdamage1 \
  libgbm-dev libcups2 libcairo2 libpango-1.0-0 libatk-bridge2.0-0
```

Danh sách dành cho Ubuntu 24.04; distro khác đối chiếu [Remotion Linux dependencies](https://www.remotion.dev/docs/miscellaneous/linux-dependencies), không thay tên package theo phỏng đoán.

Cài uv và nvm nếu chưa có, theo [uv](https://docs.astral.sh/uv/getting-started/installation/) và [nvm](https://github.com/nvm-sh/nvm). Ví dụ đã đối chiếu với tài liệu chính thức khi viết:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.41.0/install.sh | bash
if [ -n "${XDG_CONFIG_HOME:-}" ]; then
  export NVM_DIR="$XDG_CONFIG_HOME/nvm"
else
  export NVM_DIR="$HOME/.nvm"
fi
. "$NVM_DIR/nvm.sh"
nvm install 22
nvm use 22
```

Nếu nvm được cài vào vị trí riêng thì dùng vị trí thực tế do installer báo, không ghi đè thư mục đã có. Kiểm `uv --version`, `node --version`, `npm --version`, `ffmpeg -version`, `ffprobe -version`. Scheduler không tự đọc `.bashrc`/nvm; bước 10 sẽ ghi nhận PATH đã kiểm chứng.

## 4. Clone và đọc cấu hình khóa

```bash
git clone https://github.com/idohart1102/bizbank-news-shorts.git
cd bizbank-news-shorts
git status --short
git rev-parse HEAD
cat .python-version
cat .node-version
```

Không clone đè lên thư mục chứa dữ liệu. Với repo đã có: xem `git status` trước, không reset/xóa thay đổi của người vận hành. Nếu cần cài một bản release cụ thể, checkout tag đã được chọn trước khi bootstrap; ghi lại tag/commit. Muốn theo cập nhật dùng nhánh main. Không dùng `git pull` trên detached HEAD.

Python 3.12 là runtime của dự án, jsonschema là thư viện (4.x không phải Python 4). Không cần đổi Python mặc định của máy. `requirements.lock` khóa Python packages theo phiên bản/hash; `core/remotion/package-lock.json` khóa npm; `core/tts/requirements-align.lock` khóa môi trường căn từ theo OS/CPU.

## 5. Bootstrap đầy đủ, chưa bật dịch vụ trả phí

```bash
bin/bootstrap --with-tts
bin/news doctor --local
bin/tts model status
```

Bộ cài sẽ: kiểm Git/uv/Node/npm/FFmpeg → tạo `.venv` Python 3.12 → sync gói khóa → tạo config mẫu nếu chưa có → cài hook Git → npm ci, font và Chrome của Remotion → tải/kiểm 32 âm thanh theo manifest → tạo `.venv-align` theo OS/CPU → tải cache Whisper.

Không gửi TTS trả phí, không đăng nhập tài khoản hộ bạn, không tự bật service/lịch. Chạy lại sau lỗi mạng được. Giữ `.env` và `config/machine.yaml` đã có. Khi môi trường cũ sai Python/khác vị trí, giữ bản sao tại `.cache/venv-backups` trước khi tạo lại. Không chép `.venv`, `.venv-align`, node_modules từ máy khác.

Chỉ cần dựng thử: `bin/bootstrap` bỏ cài aligner/model. Chuẩn bị CI: `bin/bootstrap --with-tts --skip-tts-model` cài thư viện nhưng chưa đủ chạy giọng thật. Hoàn tất bằng `bin/tts model download`, rồi `model status` (offline). Không nâng gói để né lỗi hash; kiểm nguồn/mạng và chạy lại đúng lock.

## 6. Nghiệm thu local không tốn tiền

```bash
NEWS_OFFLINE=1 NEWS_NOTIFY=0 .venv/bin/python -m unittest discover -s tests -v
```

Phải exit 0, không bỏ qua test render vì thiếu node_modules. Suite có pipeline giả, render Remotion thật, kiểm cổng, resume, bộ TTS với server upstream/key giả. Mock test không xác nhận Vbee/model thật. Nếu báo thiếu Chrome `.so`, sửa công cụ hệ thống ở bước 3; không tắt test.

Chạy smoke qua CLI bằng vùng data riêng để không lẫn lịch sử thật:

```bash
NEWS_DATA_DIR="$PWD/local/install-smoke" NEWS_NOTIFY=0 NEWS_OFFLINE=1 \
  bin/news run --dry --no-distill
NEWS_DATA_DIR="$PWD/local/install-smoke" bin/news status
```

Lần đầu kỳ vọng `done`, file `render/final.mp4`, `meta.json` và outbox nằm trong vùng smoke. Chạy lại cùng tin mẫu có thể dừng vì chống lặp; dùng `--resume last` cho tập đang dở hoặc tạo vùng smoke mới. Dữ liệu smoke vẫn là local; không đưa vào Git. Muốn nghiệm thu bằng mắt, chủ máy mở file render local; không cần AI đọc toàn bộ thư mục media.

## 7. Thiết lập TTS cùng repo

Xem thêm [core/tts/README.md](../core/tts/README.md). Luôn gọi **`bin/tts`** từ repo, không `pip install tts`, không phụ thuộc binary `tts` của máy cũ.

1. `bin/tts model status` phải exit 0, báo backend đúng CPU, model cache có sẵn. Nếu chưa có: `bin/tts model download`. Không đổi model nhỏ hơn chỉ để chạy qua.
2. Chủ máy tạo/lấy App ID và token ứng dụng TTS từ tài khoản Vbee của họ. Nhập tại terminal, không dán vào chat:

```bash
bin/tts key set --provider vbee
bin/tts key status
```

macOS lưu Keychain; Linux lưu file quyền 0600 trong `local/tts`. Không in nội dung file/biến secret ra màn hình. Không đặt Vbee key trong `.env` video. Keychain/file local không đi cùng source Git.

3. Kiểm cổng 8791 trước khi chạy. Nếu đã có TTS của dự án khác, không tự dừng nó. Chọn cổng trống, ví dụ 8801: tạo `local/tts.env` có `TTS_PORT=8801`; sửa `tts.platform_tts_url` trong `config/machine.yaml` thành `http://127.0.0.1:8801`. Dịch vụ đọc env file lúc khởi động; pipeline truyền cùng port sang CLI. Chỉ hỗ trợ dịch vụ trên cùng máy, không dùng URL remote. Mọi đường dẫn riêng của TTS nếu tương đối được tính từ repo. Khi dùng HF_HOME hoặc auth-dir riêng, kiểm cùng user/cache ở cả foreground và service.
4. Chạy foreground để phát hiện lỗi trước:

```bash
bin/tts serve
```

Ở terminal thứ hai, cùng repo: `bin/tts service status`, `bin/tts voices --provider vbee --search "Ngọc Huyền"`. Health phải có `vbee_configured` và `align_ready` true. `voices` không tạo audio nhưng cần mạng/tài khoản upstream; không dùng lệnh `credits` để kiểm Vbee vì Vbee không có API số dư.
5. Nếu đạt, Ctrl+C terminal foreground. Sau khi chủ máy đồng ý chạy nền:

```bash
bin/tts service install
bin/tts service status
```

macOS: launchd user `vn.bizbank.news-tts`; Linux: systemd user `bizbank-news-tts.service`. Cài dưới user giữ key và cache, không sudo. WSL phải có systemd và user service hoạt động; nếu chưa có, giữ foreground cho lần nghiệm thu và báo chưa đủ vận hành nền. Máy chạy không đăng nhập cần cấu hình vòng đời user service riêng với quản trị viên; không mặc định user service luôn chạy khi logout.

Key đã cấu hình không chứng minh có quota. Trước khi bật lịch, cần một phép thử được chủ máy cho phép trên nội dung mới; hoặc clip âm thanh/text đã được chủ máy cung cấp để `bin/tts align` kiểm mốc mà không tốn credit. Kỳ vọng words tăng dần, đúng text, các cổng `check_voice` qua. Không dùng mẫu sin để kết luận Whisper hiểu tiếng Việt.

## 8. Thiết lập Claude, Codex, router và cấu hình máy

Cài CLI theo tài liệu chính thức; không coi ứng dụng desktop có sẵn là đã có lệnh trong PATH. Ví dụ:

```bash
curl -fsSL https://claude.ai/install.sh | bash -s stable
curl -fsSL https://chatgpt.com/codex/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
claude --version
codex --version
claude auth login
codex login
claude auth status
codex login status
```

Đăng nhập có thể cần chủ máy thao tác trình duyệt. Máy headless có thể dùng `codex login --device-auth` nếu tài khoản cho phép. Không chép auth cache/tài khoản của chủ cũ. Theo [Claude setup](https://code.claude.com/docs/en/setup), [Codex CLI](https://developers.openai.com/codex/cli/) và [Codex auth](https://developers.openai.com/codex/auth/). Ghi phiên bản CLI đã nghiệm thu; bản mới phải kiểm lại help/cờ, không tự nâng trong lịch sản xuất.

Kiểm các cờ adapter thực dùng, không gửi prompt tính phí:

```bash
claude --help
codex exec --help
bin/tts say --help
bin/tts align --help
```

Claude cần `-p`, `--output-format json`, `--json-schema`, `--no-session-persistence`, `--permission-mode dontAsk`, `--tools`. Codex cần `exec`, `--ephemeral`, `--skip-git-repo-check`, sandbox workspace-write, `-C`, `--output-schema`, `-o`, đọc stdin `-`. TTS cần `say` và `align --words`. Nếu phiên bản không có cờ, dừng và chọn bản tương thích; không xóa cờ bảo vệ để chạy tạm.

Mở `config/machine.yaml` do bootstrap sinh; đối chiếu `config/machine.example.yaml`. Bỏ hẳn khóa muốn dùng mặc định, không ghi YAML null. Các điểm phải kiểm:

| Khóa | Cách thiết lập đúng |
|---|---|
| `data_dir` | `episodes` hoặc đường dẫn local đã chọn; không dùng thư mục source TTS làm data video |
| `tts.backend/bin/platform_tts_url` | `platform_tts`, `bin/tts`, URL HTTP local trùng cổng dịch vụ |
| `agents.claude` | backend claude_cli; bin trong PATH hoặc absolute tại máy; model cần quyền thực tế |
| `agents.codex` | router URL `/v1`, model alias đúng router, fallback/agentic_backend codex_cli và CLI có đăng nhập |
| `agents.codex.image_model` | model ảnh thật sự được gateway hỗ trợ; ảnh AI vẫn cần router dù text chuyển sang codex_cli |
| `bins` | FFmpeg/ffprobe/Node/npx/npm thực tế; Node render phải có trong PATH |
| `notify.macos` | false trên Linux nếu muốn; Telegram mặc định tắt |

`anthropic_api`, `openai_api`, `vbee_direct` chỉ từng nằm trong roadmap, chưa có backend thực hiện. Không chọn các giá trị này. `agents.codex.model` hiện dùng cho router; Codex CLI lấy model/provider từ cấu hình CLI hoặc cli_args của máy, không tự hiểu tiền tố `cx/`.

9router là một gateway ngoài repo, không bắt buộc đúng một bản phân phối: cần HTTP API tương thích `/v1/models`, `/v1/chat/completions` với JSON schema, `/v1/responses` với web_search, và `/v1/images/generations`. Nguồn cài/phiên bản gateway và quyền model phải do chủ máy cung cấp; không cài dự án trùng tên từ kết quả tìm kiếm không xác minh. Repo không mang theo subscription/key của tác giả.

Trong `.env` video đặt `NINEROUTER_API_KEY` bằng cách nhập an toàn tại máy; không ghi key vào YAML hay báo cáo. Khuyến nghị key env rõ ràng, không dựa vào DB `~/.9router` chưa tồn tại trên máy mới. `chmod 600 .env` và `local/tts.env` nếu có secret. Không source `.env` như shell script; app đọc định dạng KEY=VALUE.

Sau cấu hình: `bin/news doctor`. Phải sửa lỗi thiếu CLI, TTS cache/cổng/key, Node, hooks/router trước khi thử thật. `/models` trả 200 không chứng minh text/web_search/image model đúng quota; kiểm các khả năng đó ở bước nghiệm thu có kiểm soát.

## 9. Chạy thật có kiểm soát

Chỉ sau khi chủ máy đã cho phép sử dụng tài khoản/credit:

```bash
bin/news run --until review --no-distill
bin/news status last
```

Đây vẫn là gọi AI trả phí, chỉ chưa tạo giọng. Kỳ vọng `paused` sau duyệt; kiểm brief/script/qa và nguồn. Tới đây chưa được báo hoàn tất video thật. Khi được phép tiếp tục các bước Vbee/ảnh/render:

```bash
bin/news run --resume last
bin/news status last
```

`--resume last` không tự biết tập nào người vận hành muốn nếu có nhiều data_dir; dùng đúng `NEWS_DATA_DIR` hoặc tên tập cụ thể. Không thêm `--dry` khi resume tập thật, và ngược lại. Exit 0: done/paused; exit 2: kiểm state/blocker, không lập vòng lặp gửi lại vô hạn.

TTS `uncertain`/`stalled`: đối chiếu job hiện có, resume đúng job, không `--force`. Audio đã có nhưng lệch mốc: align lại với text đúng, không tạo giọng mới. Nếu đã đổi script, cần duyệt lại trước khi phát sinh chi phí mới.

Đầu ra sản xuất: `<data_dir>/<tap>/render/final.mp4`, `meta.json`; queue tại `<data_dir>/outbox`. Hiện **không tự đăng YouTube/TikTok/Facebook**, trạng thái `pending_connection` là dự kiến. `drive_folder: TODO` không phải tích hợp Drive hoạt động. Đăng bài/thêm publisher là một yêu cầu triển khai riêng.

## 10. Lịch hệ điều hành — không tự có sau bootstrap

`config/channel.yaml → schedule` chỉ là cấu hình; phải sinh và cài scheduler. Chỉ bật sau khi chạy thật được duyệt và chủ máy chấp nhận lịch có thể tiêu credit.

Tại shell đã có PATH đúng Node/Claude/Codex/FFmpeg và đang ở repo:

```bash
.venv/bin/python core/scripts/schedule.py
```

Lệnh chỉ sinh file dưới `local/ops`, không bật job. Đọc lại giờ, đường dẫn và PATH; không commit các file này. Đổi repo/PATH/giờ thì sinh lại và nạp lại scheduler.

**macOS:** `StartCalendarInterval` dùng giờ hệ thống, không đổi theo `TZ` của tiến trình. Máy phải có timezone Việt Nam hoặc người vận hành quy đổi lịch trước khi nạp. Kiểm trong System Settings; không tự đổi timezone toàn máy. Sau đó:

```bash
plutil -lint local/ops/vn.bizbank.news-video.plist
mkdir -p "$HOME/Library/LaunchAgents"
cp local/ops/vn.bizbank.news-video.plist "$HOME/Library/LaunchAgents/"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/vn.bizbank.news-video.plist"
launchctl print "gui/$(id -u)/vn.bizbank.news-video"
```

Nếu label đã có, kiểm nguồn job cũ trước; chỉ `bootout` label thuộc bản cài này khi được phép thay. Log ở `local/logs/news-video.log` và `news-video-error.log`. launchd có thể chạy bù khi máy thức dậy; không hứa chạy đúng giờ khi máy tắt/ngủ.

**Linux/systemd user:** kiểm `systemctl --user status`; WSL cần systemd được bật theo [Microsoft](https://learn.microsoft.com/windows/wsl/systemd). Timer ghi timezone Asia/Ho_Chi_Minh rõ ràng:

```bash
mkdir -p "$HOME/.config/systemd/user"
cp local/ops/bizbank-news-video.service local/ops/bizbank-news-video.timer "$HOME/.config/systemd/user/"
systemd-analyze --user verify "$HOME/.config/systemd/user/bizbank-news-video.service" "$HOME/.config/systemd/user/bizbank-news-video.timer"
systemctl --user daemon-reload
systemctl --user enable --now bizbank-news-video.timer
systemctl --user list-timers bizbank-news-video.timer
```

Timer không chạy bù các lần máy tắt (`Persistent=false`). Log: `journalctl --user -u bizbank-news-video.service`. Không tự dùng `systemctl start ...service` để thử, vì đó là chạy thật trả phí. Kiểm vòng đời user/login/WSL trước khi tuyên bố chạy 24/7. Dừng lịch bằng `systemctl --user disable --now bizbank-news-video.timer`; macOS dùng `launchctl bootout "gui/$(id -u)/vn.bizbank.news-video"`. Dừng lịch không xóa data/credential.

## 11. Vận hành, nâng cấp và khôi phục

- Chạy tay `bin/news run`; xem `bin/news status`; tiếp tục đúng tập `bin/news run --resume <tap>`.
- Góp ý: `bin/news feedback <tap> <bước> "nội dung"`. Luật bài học tại lessons/rules; không đưa sự kiện thô/tên tập lên Git.
- Nâng cấp: xem git status, dừng lịch đang sở hữu để tránh chạy chồng, `git pull --ff-only`, `bin/bootstrap --with-tts`, doctor local/model status/full, test; khởi động lại TTS và nạp lại lịch nếu path/config thay. Không reset thay đổi local để ép pull.
- Sao lưu riêng data_dir và `local/tts` (có thể có key Linux), cấu hình local và tài khoản; không gửi public. Xóa database TTS làm mất thông tin chống tính tiền lặp. Keychain macOS không nằm trong bản sao file.
- Gỡ TTS nền: `bin/tts service uninstall`, dữ liệu/key vẫn giữ. Không gỡ dịch vụ TTS khác đang dùng chung. Không xóa cache/model/job chỉ để thử sửa mạng.
- Hook: `bin/bootstrap` cài guard; hook tùy chỉnh được giữ. Nếu cảnh báo chưa tích hợp, bổ sung guard theo README rồi kiểm staged/pre-push. Không `git add -f local/` hay bỏ hook để đẩy được.

## 12. Bảng xử lý lỗi

| Triệu chứng | Kiểm/sửa |
|---|---|
| Python/jsonschema lệch | dùng bin/bootstrap, không pip vào Python hệ thống; kiểm `.venv/bin/python`, không nhầm version package |
| uv/node/npm không thấy | nạp profile/PATH tại user đang chạy; Node 22/npm >=10; scheduler có PATH riêng |
| lỗi hash / package wheel | không bỏ require-hashes; kiểm OS/CPU/nguồn và mạng; distro/arch chưa hỗ trợ phải báo rõ |
| Chrome thiếu shared library | Ubuntu package ở bước 3; render thật phải qua |
| thiếu âm thanh / sha256 đổi | chạy lại bootstrap, xem CDN; không tự --update manifest để bỏ kiểm hash |
| `tts` trùng tên / thiếu align --words | dùng bin/tts của repo và default `tts.bin: bin/tts` |
| align_ready false / HF offline missing | bootstrap --with-tts, model download rồi model status; không tạo giọng trước khi cache sẵn |
| MLX không chạy Linux/Intel | dùng backend mặc định faster-whisper CPU; không ép cài mlx-metal |
| port already in use | xác định dịch vụ đang giữ cổng; đổi cả local/tts.env và machine.yaml; không kill bừa |
| 401/403/model không có | chủ tài khoản xác minh login/key/quota/model alias; doctor 200 không đủ chứng minh ảnh/web_search |
| chạy tay được, lịch lỗi | user/PATH/timezone/keychain/venv khác; kiểm journal/launchd log; không chạy paid retry liên tục |
| state needs_human/failed/uncertain | đọc blocker/log/job, xử lý nguyên nhân, tiếp tục đúng tập/job; không --force |
| có outbox nhưng chưa có video YouTube | publisher chưa kết nối; đây không phải lỗi bootstrap |

## 13. Báo cáo bàn giao bắt buộc

Ghi commit/tag; OS/CPU/user/timezone; phiên bản các công cụ; lệnh đã chạy và exit code. Đánh dấu riêng: bootstrap, test/render local, TTS source/deps/model/key/service, Claude/Codex auth, router/model, live video, scheduler. Ghi cái chưa kiểm/đang bị chặn, nơi giữ data/log, cách tắt lịch và phục hồi. Không đưa nội dung `.env`, credentials, auth cache hoặc text/audio của video vào báo cáo.
