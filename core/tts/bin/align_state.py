"""Cấu hình backend và kiểm artifact cache bằng stdlib, không inference/network."""
import hashlib
import json
import os
from pathlib import Path
import platform

REPO = Path(__file__).resolve().parents[3]
STATE = REPO / 'local/tts-model.json'


def backend():
    return os.environ.get('TTS_ALIGN_BACKEND') or ('mlx' if platform.system() == 'Darwin' and platform.machine() == 'arm64' else 'faster-whisper')


def model_name():
    return os.environ.get('TTS_ALIGN_MODEL') or ('mlx-community/whisper-large-v3-turbo' if backend() == 'mlx' else 'mobiuslabsgmbh/faster-whisper-large-v3-turbo')


def snapshot_ready(snapshot, engine):
    snapshot = Path(snapshot)
    required = ['config.json']
    if engine == 'mlx':
        weights = [snapshot / name for name in ('weights.npz', 'weights.safetensors')]
        if not any(p.is_file() and p.stat().st_size > 0 for p in weights):
            return False
    elif engine == 'faster-whisper':
        required += ['model.bin', 'tokenizer.json']
    else:
        return False
    return all((snapshot / name).is_file() and (snapshot / name).stat().st_size > 0 for name in required)


def lock_hash():
    return hashlib.sha256((REPO / 'core/tts/requirements-align.lock').read_bytes()).hexdigest()


def ready(python):
    try:
        data = json.loads(STATE.read_text(encoding='utf-8'))
        return (Path(python).exists() and data['backend'] == backend() and data['model'] == model_name()
                and data['python'] == str(Path(python).resolve()) and data['repo'] == str(REPO)
                and data['lock'] == lock_hash() and snapshot_ready(data['snapshot'], data['backend']))
    except (OSError, ValueError, KeyError):
        return False
