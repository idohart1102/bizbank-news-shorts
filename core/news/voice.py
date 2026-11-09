"""Hợp đồng với CLI platform/tts: cùng máy, cùng cổng với health check."""
import os
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlsplit


def connection(cfg):
    conf = cfg.machine['tts']
    if conf.get('backend') != 'platform_tts':
        raise ValueError('Chỉ hỗ trợ tts.backend=platform_tts; vbee_direct chưa triển khai. Xem docs/INSTALL.md.')
    url = conf.get('platform_tts_url', 'http://127.0.0.1:8791').rstrip('/')
    parsed = urlsplit(url)
    if (parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost') or
            parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
        raise ValueError('platform/tts CLI chỉ gọi dịch vụ local HTTP; dùng http://127.0.0.1:<port>, không đặt URL máy khác.')
    port = parsed.port or 80
    binary = conf.get('bin', 'bin/tts')
    if '/' in binary and not Path(binary).is_absolute():
        binary = str(cfg.root / binary)
    return binary, url, {**os.environ, 'TTS_PORT': str(port)}


def preflight(cfg):
    binary, url, env = connection(cfg)
    if not shutil.which(binary):
        raise ValueError(f'Thiếu CLI platform/tts: {binary}. Xem docs/INSTALL.md phần TTS; không cài gói trùng tên từ PyPI.')
    for command, flags in (
            ('say', ('--provider', '--voice', '--speed', '--file', '--out', '--project', '--srt', '--pauses')),
            ('align', ('--audio', '--text', '--out', '--words'))):
        try:
            out = subprocess.run([binary, command, '--help'], env=env, capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ValueError(f'CLI tts {command} không chạy được: {type(error).__name__}') from None
        if out.returncode or any(flag not in out.stdout for flag in flags):
            raise ValueError(f'CLI tts {command} không tương thích; cần bản platform/tts có các cờ {", ".join(flags)}.')
    if Path(binary).resolve() == (cfg.root / 'bin/tts').resolve():
        try:
            out = subprocess.run([binary, 'model', 'status'], env=env, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            raise ValueError('Không kiểm được model TTS offline trong 60 giây; kiểm bin/tts model status trước khi tạo giọng.') from None
        if out.returncode:
            raise ValueError('TTS chưa có thư viện/model căn từ offline. Chạy bin/bootstrap --with-tts; bin/tts model status.')
    return binary, url, env
