"""Tải model một lần hoặc kiểm cache offline; không gọi dịch vụ TTS trả phí."""
import argparse
import importlib.util
import json
import os
import sys
import tempfile
import runpy
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--download', action='store_true')
args = parser.parse_args()
os.environ['HF_HUB_OFFLINE'] = '0' if args.download else '1'
config = runpy.run_path(str(Path(__file__).with_name('align_state.py')))
state = config['STATE']
state.unlink(missing_ok=True)
spec = importlib.util.spec_from_file_location('tts_align', Path(__file__).with_name('align.py'))
align = importlib.util.module_from_spec(spec)
spec.loader.exec_module(align)
if align.backend() == 'mlx':
    import mlx_whisper  # kiểm import trước khi tốn thời gian tải model
else:
    import faster_whisper
from huggingface_hub import snapshot_download
snapshot = snapshot_download(align.model_name(), local_files_only=not args.download)
if not config['snapshot_ready'](snapshot, align.backend()):
    raise SystemExit('Model cache chưa đủ artifact; chạy bin/tts model download. Không tạo giọng trước khi sửa.')
result = {'backend': align.backend(), 'model': align.model_name(), 'snapshot': snapshot, 'cached': True,
          'python': str(Path(sys.executable).resolve()), 'repo': str(config['REPO']), 'lock': config['lock_hash']()}
state.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=state.parent, delete=False) as handle:
    json.dump(result, handle)
    temporary = Path(handle.name)
temporary.replace(state)
print(json.dumps(result))
