# News video

Hệ thống tự động làm short tin tức Việt Nam (dưới 60 giây, 9:16) cho hộ kinh doanh và SME: gom tin → chọn → viết → duyệt + kiểm fact → giọng → ảnh → plan dựng → render → QC → gói → hàng chờ đăng.

```bash
bin/bootstrap          # máy mới: venv, kho sfx, git hook, config mẫu
bin/news doctor        # kiểm máy đủ điều kiện
bin/news run --dry     # chạy trọn luồng bằng dữ liệu mẫu, không tốn tiền
bin/news run           # chạy một tập thật; --resume last để tiếp tục
bin/news status
.venv/bin/python -m unittest discover -s tests
```

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
