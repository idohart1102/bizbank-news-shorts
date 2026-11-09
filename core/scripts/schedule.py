"""Sinh lịch từ config/channel.yaml tại local/ops; KHÔNG cài/bật lịch. Xem docs/INSTALL.md."""
import argparse
import os
from pathlib import Path
import platform
import plistlib
import re

import yaml


def generate(root, system):
    root = Path(root).resolve()
    conf = yaml.safe_load((root / 'config/channel.yaml').read_text(encoding='utf-8'))
    times = conf.get('schedule', [])
    if not times or any(not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', t) for t in times):
        raise ValueError('schedule phải là danh sách HH:MM hợp lệ, ví dụ 10:30 và 19:00')
    folder = root / 'local/ops'
    folder.mkdir(parents=True, exist_ok=True)
    logs = root / 'local/logs'
    logs.mkdir(parents=True, exist_ok=True)
    path = os.environ.get('PATH', '/usr/bin:/bin')
    names = ('NEWS_MACHINE_CONFIG', 'NEWS_DATA_DIR', 'CODEX_HOME', 'CLAUDE_CONFIG_DIR', 'TTS_ENV_FILE',
             'TTS_ALIGN_MODEL', 'TTS_ALIGN_BACKEND', 'TTS_ALIGN_PYTHON', 'HF_HOME', 'HUGGINGFACE_HUB_CACHE',
             'SSL_CERT_FILE', 'SSL_CERT_DIR', 'CODEX_CA_CERTIFICATE')
    env = {'PATH': path, 'TZ': 'Asia/Ho_Chi_Minh', **{name: os.environ[name] for name in names if name in os.environ}}
    command = [str(root / 'bin/news'), 'run', '--trigger', 'schedule']
    if system == 'macos':
        result = folder / 'vn.bizbank.news-video.plist'
        data = {'Label': 'vn.bizbank.news-video', 'ProgramArguments': command, 'WorkingDirectory': str(root),
                'EnvironmentVariables': env, 'RunAtLoad': False,
                'StartCalendarInterval': [{'Hour': int(t.split(':')[0]), 'Minute': int(t.split(':')[1])} for t in times],
                'StandardOutPath': str(logs / 'news-video.log'), 'StandardErrorPath': str(logs / 'news-video-error.log')}
        result.write_bytes(plistlib.dumps(data))
        return [result]
    if system != 'linux':
        raise ValueError('Chỉ sinh lịch macos hoặc linux; Windows dùng WSL2 có systemd.')
    def quote(value):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%') + '"'
    service = folder / 'bizbank-news-video.service'
    service.write_text('[Unit]\nDescription=BizBank news video\n[Service]\nType=oneshot\n'
                       + ''.join('Environment=' + quote(k + '=' + v) + '\n' for k, v in env.items())
                       + 'ExecStart=:' + ' '.join(quote(c) for c in command) + '\n', encoding='utf-8')
    timer = folder / 'bizbank-news-video.timer'
    timer.write_text('[Unit]\nDescription=BizBank news video schedule\n[Timer]\n'
                     + ''.join('OnCalendar=*-*-* ' + t + ':00 Asia/Ho_Chi_Minh\n' for t in times)
                     + 'Persistent=false\n[Install]\nWantedBy=timers.target\n', encoding='utf-8')
    return [service, timer]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', choices=['macos', 'linux'], default='macos' if platform.system() == 'Darwin' else 'linux')
    args = parser.parse_args()
    for path in generate(Path(__file__).resolve().parents[2], args.platform):
        print(path)
