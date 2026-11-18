# VieNeu-TTS chạy local thay Vbee

Repo này chỉ lưu bộ cài/adapter và hướng dẫn. Không cần chép bộ source VieNeu, file cài đặt, model hoặc môi trường Python lên GitHub.

## Cài máy mới

Hoàn tất công cụ và bootstrap theo [INSTALL.md](INSTALL.md), rồi chạy từ gốc repo:

```bash
bin/bootstrap --with-tts
bin/vieneu install
bin/vieneu status
bin/vieneu voices
bin/tts model status
```

`bin/vieneu install` clone [pnnbao97/VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) vào `local/vieneu/source`, checkout commit `22dd2ef2a89bba24a77da6dbc84c75f7f4fda05b` (SDK 3.8.4), cài Python 3.12 bằng `uv sync --frozen`, tải model rồi kiểm khả năng nạp offline. Không sửa Python/venv của pipeline hoặc Whisper. Chạy lại installer giữ nguyên bản source đã cài; nếu khác commit hoặc có sửa đổi, dừng để tránh ghi đè.

VieNeu v3 Turbo dùng ONNX CPU/fp32 trên Mac Apple Silicon và máy CPU khác; không cần CUDA hay PyTorch. Bản này không cài nhánh CUDA. Dành vài GB đĩa trống và RAM cho model; số đo trên Mac ARM64 không thay cho nghiệm thu Linux/WSL. Máy Linux/WSL vẫn phải chạy installer/status và một đoạn thử thật trước khi bật lịch.

Model lấy từ Hugging Face trong lần cài/download; các lần `status`, `voices`, `say` chỉ đọc cache offline. Source và dependencies được khóa theo commit + `uv.lock` của upstream; model dùng snapshot upstream tại thời điểm tải và được lưu trong cache riêng. Muốn cập nhật model chủ động: `bin/vieneu download`, sau đó kiểm status và chất lượng lại.

## Cấu hình và thử giọng

Mặc định `config/channel.yaml`:

```yaml
tts:
  service: local_vieneu
  provider: vieneu
  voice: Ngọc Huyền
  speed: 1.0
  project: news-video
  export_srt: true
```

Đây là preset Ngọc Huyền của VieNeu, không phải cùng bản giọng Ngọc Huyền trên Vbee. Liệt kê bằng `bin/vieneu voices`, dùng đúng trường `id`. Có thể chọn preset khác bằng `tts.voice`. Không tự clone giọng.

### Chọn giọng khác trên máy của người dùng

1. Chạy `bin/vieneu voices` để xem các preset đã cài.
2. Trong `config/channel.yaml`, đổi `tts.voice` sang đúng `id` muốn dùng, ví dụ `voice: Mai Anh`.
3. Đọc thử bằng `bin/vieneu say --voice 'Mai Anh' --file local/thu-giong.txt --out local/thu-giong-mai-anh.mp3`.
4. Các tập mới chạy bằng `bin/news run` sẽ dùng giọng vừa chọn. Tập đã tạo audio giữ nguyên khi resume.

Đổi giữa các preset có sẵn không cần cài lại VieNeu hoặc tải lại model. Chọn giọng khi gọi `say --voice` chỉ áp dụng cho lần thử đó; muốn pipeline dùng lâu dài phải sửa `tts.voice` như bước 2.

Tạo văn bản UTF-8 trong `local/thu-giong.txt` rồi chạy:

```bash
bin/vieneu say --voice 'Ngọc Huyền' --file local/thu-giong.txt --out local/thu-giong.mp3
bin/tts align --audio local/thu-giong.mp3 --text local/thu-giong.txt \
  --out local/thu-giong.srt --words local/thu-giong.words.json
```

Không tốn credit Vbee. CLI xuất MP3 48 kHz, chuẩn hóa -14 LUFS. `speed` được áp bằng FFmpeg, không cho vượt 1.1x. Yêu cầu y hệt và audio đúng checksum thì dùng lại; file đã có nhưng khác yêu cầu hoặc thiếu metadata sẽ dừng. Chỉ thêm `--replace` khi có chủ ý tạo lại sau khi sửa kịch bản. File `.mp3.vieneu.json` cạnh audio giúp nhận biết yêu cầu cũ mà không lưu nguyên văn text.

Pipeline `bin/news run` tự gọi VieNeu rồi Whisper. Không cần `bin/tts serve`, không cần App ID/token Vbee; không tự fallback sang nhà cung cấp trả phí. Lỗi căn từ giữ audio để chạy lại align. Khi resume tập cũ đã có giọng, hệ thống giữ bước đã hoàn thành; áp provider mới cho tập mới.

## Git và chuyển máy

- `local/vieneu/source/`: source bên thứ ba + `.venv` riêng.
- `local/vieneu/hf-cache/`: model/cache Hugging Face.
- `local/vieneu/smoke/`: kết quả thử tại máy nếu có.
- `local/` đã có trong `.gitignore`; guard Git chặn cả trường hợp cố thêm vùng local. Không dùng `git add -f`.

Máy mới chỉ clone repo tin tức, chạy bootstrap và `bin/vieneu install` để tải lại. Không copy `.venv` giữa máy. `VIENEU_HOME` có thể đổi nơi cài/cache tại máy; mặc định dùng `local/vieneu`. Không commit đường dẫn máy hoặc cấu hình biến này.

Nếu muốn quay về Vbee, sửa `tts.provider: vbee`, `tts.service: bundled_tts`, `tts.voice: hn_female_ngochuyen_full_48k-fhg`; thêm `pauses: {sentence: 0.1, major: 0.1, medium: 0.1, paragraph: 0}`. Thiết lập key/service theo [core/tts/README.md](../core/tts/README.md). Không cần xóa VieNeu để đổi provider.

Tham khảo: [hướng dẫn SDK của tác giả](https://github.com/pnnbao97/VieNeu-TTS#sdk), [model v3 Turbo](https://huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo). Không đưa trọng số hoặc source của họ vào repo của mình.
