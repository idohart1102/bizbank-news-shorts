"""Cài guard hook di động; giữ hook tùy chỉnh, nhận diện chính xác hook v1."""
from pathlib import Path
import re
import subprocess

MARKER = '# news-video-managed-hook'
LEGACY = re.compile(r'#!/bin/sh\nexec ".*/\.venv/bin/python" -I ".*/core/scripts/guard_repo\.py" (pre-commit|pre-push)\n?')


def install(root):
    root = Path(root).resolve()
    result = subprocess.run(['git', 'rev-parse', '--git-path', 'hooks'], cwd=root, capture_output=True, text=True)
    if result.returncode:
        print('Không có repo Git: bỏ qua hook (ZIP).')
        return
    folder = Path(result.stdout.strip())
    if not folder.is_absolute():
        folder = root / folder
    folder.mkdir(parents=True, exist_ok=True)
    for mode in ('pre-commit', 'pre-push'):
        path = folder / mode
        if path.exists():
            current = path.read_text(encoding='utf-8')
            if MARKER not in current.splitlines() and not LEGACY.fullmatch(current):
                print(f'Giữ hook có sẵn: {path}. Tích hợp guard_repo.py theo README.md nếu chưa có.')
                continue
        path.write_text('#!/bin/sh\n' + MARKER + '\nset -eu\n'
                        'ROOT="$(git rev-parse --show-toplevel)"\n'
                        'exec "$ROOT/.venv/bin/python" -I "$ROOT/core/scripts/guard_repo.py" ' + mode + '\n', encoding='utf-8')
        path.chmod(0o755)


if __name__ == '__main__':
    install(Path(__file__).resolve().parents[2])
