"""Chẩn đoán máy mới; --local không gọi dịch vụ/TTS/AI."""
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
import urllib.request

from .runtime import problems


def check(cfg, local=False):
    ok = True

    def report(name, good, detail=''):
        nonlocal ok
        ok = ok and bool(good)
        print(f"{'✓' if good else '✗'} {name}" + (f': {detail}' if detail else ''))

    report('Python', sys.version_info[:2] == (3, 12), f'{platform.python_version()} — {sys.executable}')
    errors = problems(cfg.root)
    report('gói Python khóa phiên bản', not errors, '; '.join(errors) or f"jsonschema {importlib.metadata.version('jsonschema')}")
    for name in ('ffmpeg', 'ffprobe', 'node', 'npx', 'npm'):
        binary = cfg.bin(name)
        good, detail = bool(shutil.which(binary)), shutil.which(binary) or 'không thấy'
        if good:
            try:
                out = subprocess.run([binary, '-version' if name in ('ffmpeg', 'ffprobe') else '--version'],
                                     capture_output=True, text=True, timeout=10)
                good = out.returncode == 0
                detail = (out.stdout or out.stderr).splitlines()[0]
                if name == 'node':
                    good = good and int(detail.lstrip('v').split('.')[0]) == 22
                    detail += ' (cần 22.x)'
                elif name == 'npm':
                    good = good and int(detail.split('.')[0]) >= 10
                    detail += ' (cần >= 10)'
            except (OSError, ValueError, IndexError, subprocess.TimeoutExpired) as error:
                good, detail = False, str(error)
        report(name, good, detail)
    folder = cfg.root / 'core/remotion'
    packages = json.loads((folder / 'package.json').read_text(encoding='utf-8'))
    for name, version in packages['dependencies'].items():
        path = folder / 'node_modules' / name / 'package.json'
        try:
            actual = json.loads(path.read_text(encoding='utf-8')).get('version')
        except (OSError, ValueError):
            actual = None
        report(f'Remotion/npm {name}', actual == version, f'{actual or "chưa cài"}; cần {version}')
    for library in ('sfx', 'music'):
        folder = cfg.root / 'assets' / library
        index = json.loads((folder / 'index.json').read_text(encoding='utf-8'))
        missing = [v['file'] for v in index.values() if not (folder / v['file']).exists()]
        report(f'kho {library}', not missing, f'thiếu {len(missing)} file; chạy bin/bootstrap' if missing else f'{len(index)} file')
    template = cfg.root / cfg.video['template']
    report('template overlay', template.exists(), str(template) if template.exists() else 'chưa có')
    report('cấu hình máy', cfg.machine_path.exists(), str(cfg.machine_path))
    # Apple Vision là tùy chọn: máy khác vẫn chạy, cutout ảnh thật cần adapter thay thế.
    vision = platform.system() == 'Darwin' and int(platform.mac_ver()[0].split('.')[0] or 0) >= 14 and shutil.which('swiftc')
    if not vision:
        print('! Cutout ảnh thật: Apple Vision cần macOS 14+ và Xcode Command Line Tools; máy này sẽ bỏ qua khi không tách nền được.')
    git = subprocess.run(['git', 'rev-parse', '--git-path', 'hooks'], cwd=cfg.root, capture_output=True, text=True) if shutil.which('git') else None
    if git and git.returncode == 0:
        from pathlib import Path
        hook_dir = Path(git.stdout.strip())
        if not hook_dir.is_absolute():
            hook_dir = cfg.root / hook_dir
        for hook in ('pre-commit', 'pre-push'):
            path = hook_dir / hook
            report(f'git hook {hook}', path.exists() and 'guard_repo.py' in path.read_text(encoding='utf-8'), 'chạy bin/bootstrap hoặc tích hợp hook theo README.md')
    if not local:
        from .voice import preflight
        try:
            binary, url, _ = preflight(cfg)
            report('tts CLI', True, binary + ' (say + align --words)')
            with urllib.request.urlopen(url + '/health', timeout=5) as response:
                health = json.loads(response.read())
            report('tts service', health.get('service') == 'bizbank-news-tts' and health.get('vbee_configured') and health.get('align_ready'),
                   'cần service=bizbank-news-tts, Vbee key và aligner; nếu cổng có dịch vụ khác, chọn cổng riêng')
        except (OSError, ValueError) as error:
            report('tts', False, str(error))
        for role, conf in cfg.machine['agents'].items():
            if any(conf.get(k, '').endswith('_cli') for k in ('backend', 'fallback', 'agentic_backend')):
                binary = conf.get('bin', role)
                report(f'agent {role}', bool(shutil.which(binary)), shutil.which(binary) or 'chưa cài/đăng nhập CLI')
            if conf['backend'] == 'router' or role == 'codex':
                try:
                    from .agents import router_key
                    request = urllib.request.Request(conf['url'].rstrip('/') + '/models',
                                                    headers={'Authorization': f'Bearer {router_key(conf)}'})
                    with urllib.request.urlopen(request, timeout=5):
                        report(f'router {role}', True, conf['url'] + ' (cần cả ảnh AI cho codex)')
                except Exception as error:
                    # Không in response/secret của nhà cung cấp trong báo cáo máy.
                    report(f'router {role}', False, f'kiểm URL/key trong .env ({type(error).__name__})')
    return ok
