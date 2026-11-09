# TTS đóng gói trong repo

Điểm bắt đầu: [hướng dẫn cài toàn hệ thống](../../docs/INSTALL.md). Đây là source sạch của dịch vụ TTS dùng chung, được đưa vào repo theo yêu cầu Sếp. Không có key, database job, audio hay cache model của máy cũ.

## Cài và chạy

Tại thư mục gốc repo:

```bash
bin/bootstrap --with-tts
bin/tts model status
bin/tts key set --provider vbee
bin/tts serve
```

Giữ terminal `serve` mở; ở terminal khác chạy `bin/tts service status`. Sau khi kiểm tra thành công, dừng `serve` bằng Ctrl+C rồi dùng `bin/tts service install` nếu muốn chạy nền (launchd trên macOS, systemd user trên Linux). Không chạy hai server cùng cổng.

Python runtime ở `.venv`, aligner ở `.venv-align`. `--with-tts` cài aligner từ lock có hash và tải model Whisper large-v3-turbo; không gửi yêu cầu tạo giọng, không cần key Vbee. Model có thể chiếm nhiều GB. Apple Silicon dùng `mlx-whisper`, Linux/Intel dùng `faster-whisper` CPU/int8. `--skip-tts-model` chỉ dành cho CI/chuẩn bị môi trường; chưa đủ chạy thật. Chạy `bin/tts model download` sau để hoàn tất.

## Cấu hình riêng

Mặc định HTTP chỉ nghe `127.0.0.1:8791`, không có xác thực truy cập từ cùng máy. Không đưa cổng ra Internet. Repo video dùng `config/machine.yaml → tts.platform_tts_url`; CLI và health check dùng cùng cổng qua `TTS_PORT`.

Nếu cần cấu hình dịch vụ khác mặc định, tạo `local/tts.env` (không vào Git), mỗi dòng `KEY=VALUE`, không dùng `export`, không thay thế biến shell. Dịch vụ tự đọc file này lúc khởi động. Biến môi trường đã có sẽ được ưu tiên. Service chỉ giữ whitelist cấu hình không bí mật được export lúc cài, không giữ key; giá trị đọc từ file được đọc lại sau mỗi lần restart. Nếu đổi giá trị đã export/cài vào service, cài lại service. Secret chỉ export trong terminal không tự được giữ khi chạy nền: dùng key set hoặc env file local.

| Biến | Mặc định / tác dụng |
|---|---|
| `TTS_PORT` | `8791`; đổi cả URL trong machine.yaml, khởi động lại service |
| `TTS_DATA_DIR` | `local/tts`; chứa metadata, cache audio, kho key Linux |
| `TTS_ALIGN_PYTHON` | `.venv-align/bin/python` của repo |
| `TTS_ALIGN_BACKEND` | tự chọn `mlx` hoặc `faster-whisper` theo OS/CPU |
| `TTS_ALIGN_MODEL` | MLX: `mlx-community/whisper-large-v3-turbo`; CPU: `mobiuslabsgmbh/faster-whisper-large-v3-turbo` |
| `VBEE_APP_ID`, `VBEE_TOKEN` | chỉ dùng ở dịch vụ nếu dùng env thay kho key; không đặt vào `.env` video |
| `TTS_ENV_FILE` | ghi đè vị trí file cấu hình dịch vụ |

Sau khi đổi backend/model: cài dependencies tương ứng, `bin/tts model download`, kiểm `model status`, khởi động lại service. Không ép MLX lên Linux/Intel. Theo [MLX model card](https://huggingface.co/mlx-community/whisper-large-v3-turbo) và [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

Key nhập tương tác bằng `bin/tts key set --provider vbee`. macOS lưu Keychain riêng `bizbank-news-tts-vbee`; Linux lưu `local/tts/credentials.json`, quyền `0600`. `bin/tts key status` chỉ báo có/chưa có. Không yêu cầu người dùng dán key vào chat/log. Không đưa `local/` vào Git. Dịch vụ cũ `com.idohart.tts` có namespace key khác, không tự lấy key cũ; không dừng/gỡ dịch vụ cũ khi chưa xác nhận bàn giao.

## Giao diện CLI

```bash
bin/tts --help
bin/tts say --help
bin/tts align --help
bin/tts voices --provider vbee --search "Ngọc Huyền"
bin/tts usage
```

`voices` gọi danh sách giọng của Vbee, không tạo audio. Vbee không có API số dư; `usage` là sổ theo dõi ký tự của dịch vụ.

Ví dụ tạo giọng **có tốn credit**, chỉ chạy khi chủ máy cho phép:

```bash
bin/tts say --provider vbee --voice hn_female_ngochuyen_full_48k-fhg \
  --file van-ban.txt --out local/thu-giong.mp3 --project news-video --srt \
  --pauses sentence=0.1,major=0.1,medium=0.1,paragraph=0
bin/tts align --audio local/thu-giong.mp3 --text van-ban.txt \
  --out local/thu-giong.srt --words local/thu-giong.words.json
```

Vbee không trả SRT; Whisper căn tại máy, không tốn credit. Video không hiển thị phụ đề; file words dùng canh thẻ/cutout. `align` trên audio đã có không gửi yêu cầu tạo giọng. Mặc định match < 85% trả mã 3 và pipeline dừng, giữ audio để sửa; không nuốt mã lỗi hoặc tạo lại giọng. Trạng thái khớp thấp phải kiểm text/audio, không gửi lại Vbee để sửa mốc. CPU có thể chậm hơn MLX; kiểm timeout và RAM trước khi bật lịch.

## HTTP và vòng đời

| Đường dẫn | Tác dụng |
|---|---|
| `GET /health` | trạng thái local; không gọi upstream |
| `POST /v1/speech` | tạo giọng; nhận text, provider, voice_id, speed, project, export_srt, pauses |
| `GET /v1/jobs/{id}` | theo dõi job |
| `GET /v1/jobs/{id}/audio`, `/srt` | lấy kết quả |
| `POST /v1/jobs/{id}/resume` | theo dõi job stalled, không gửi tạo mới |
| `GET /v1/usage` | sổ sử dụng local |

Job mới trả `202`; yêu cầu trùng trả `200` với `reused: true` khi có kết quả dùng lại. `queued/submitting/polling/downloading`: chờ. `done`: lấy file. `failed`: đọc lý do, xác minh trước khi gửi lại. `stalled`: resume job. `uncertain`: có thể đã tính tiền, dừng và đối chiếu lịch sử Vbee; không tự dùng `--force`.

Không xóa `local/tts` để sửa lỗi cài đặt: database và audio cache giúp tránh gửi lại yêu cầu trả phí. Sao lưu thư mục này riêng và bảo mật; không đưa vào bản source bàn giao công khai. Service hiện còn adapter KingCong cho các provider khác, nhưng pipeline video chỉ dùng Vbee; các cấu hình đó không bắt buộc.

## Kiểm thử

```bash
.venv/bin/python -m unittest discover -s core/tts/tests -v
```

Server giả, key tổng hợp, không cần tài khoản và không tốn credit. Test này cũng được nạp trong suite gốc. Cần nghiệm thu chất lượng mốc từ trên clip được chủ máy cho phép trước khi tuyên bố môi trường sản xuất đạt; mock test không thay thế nghiệm thu này.
