"""Cấu hình: config/channel.yaml (vào Git) + config/machine.yaml (máy này, không vào Git) + biến môi trường."""
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

MACHINE_DEFAULTS = {
    "data_dir": "episodes",
    "tts": {"backend": "platform_tts", "platform_tts_url": "http://127.0.0.1:8791"},
    "agents": {
        "claude": {"backend": "claude_cli", "bin": "claude", "model": "claude-opus-5-5"},
        "codex": {"backend": "router", "url": "http://127.0.0.1:20128/v1", "model": "cx/gpt-6.1-sol",
                  "fallback": "codex_cli", "bin": "codex"},
    },
    "bins": {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe", "node": "node", "npx": "npx"},
    "notify": {"macos": True},
}


def merge(base, override):
    out = dict(base)
    for key, value in (override or {}).items():
        out[key] = merge(base[key], value) if isinstance(value, dict) and isinstance(base.get(key), dict) else value
    return out


def load_env_file(path):
    """Đọc .env đơn giản (KEY=VALUE) nếu có; không ghi đè biến đã đặt."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class OfflineError(RuntimeError):
    """NEWS_OFFLINE=1 (test): cấm mọi lời gọi ra ngoài và mọi bước tốn tiền."""


def ensure_online(what):
    if os.environ.get("NEWS_OFFLINE") == "1":
        raise OfflineError(f"NEWS_OFFLINE=1: chặn {what}")


class Config:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        load_env_file(self.root / ".env")
        self.channel = yaml.safe_load((self.root / "config" / "channel.yaml").read_text(encoding="utf-8"))
        machine_path = Path(os.environ.get("NEWS_MACHINE_CONFIG", self.root / "config" / "machine.yaml"))
        if not machine_path.is_absolute():
            machine_path = self.root / machine_path
        self.machine_path = machine_path
        machine = yaml.safe_load(machine_path.read_text(encoding="utf-8")) if machine_path.exists() else {}
        self.machine = merge(MACHINE_DEFAULTS, machine)
        data_dir = Path(os.environ.get("NEWS_DATA_DIR", self.machine["data_dir"]))
        self.data_dir = data_dir if data_dir.is_absolute() else self.root / data_dir
        self.dry = os.environ.get("NEWS_DRY") == "1"
        self.enforce_budget = not self.dry  # chạy thật luôn kiểm ngân sách

    @property
    def video(self):
        return self.channel["video"]

    def bin(self, name):
        return self.machine["bins"].get(name, name)

    def path(self, relative):
        return self.root / relative
