"""Kiểm Python và gói khóa bằng thư viện chuẩn, chạy được trước khi import news.cli."""
import importlib.metadata
from pathlib import Path
import re
import sys


def problems(root, python_version=None):
    root = Path(root)
    required = (root / '.python-version').read_text(encoding='utf-8').strip()
    actual = python_version or sys.version_info
    errors = []
    if tuple(actual[:2]) != tuple(map(int, required.split('.'))):
        errors.append(f'Python {actual[0]}.{actual[1]} không phù hợp; dự án cần Python {required}.x')
    for name, expected in re.findall(r'^([\w.-]+)==([^\s\\]+)', (root / 'requirements.lock').read_text(encoding='utf-8'), re.M):
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            errors.append(f'Thiếu {name}=={expected}')
            continue
        if installed != expected:
            errors.append(f'{name}: đang {installed}, cần {expected}')
    return errors


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
    errors = problems(root)
    if errors:
        print('\n'.join(errors) + '\nChạy lại: bin/bootstrap (tại thư mục repo)', file=sys.stderr)
        sys.exit(1)
