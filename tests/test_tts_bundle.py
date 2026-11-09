"""Bộ TTS đóng gói: chỉ server giả; không tạo giọng thật, không lấy key máy."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_tests(loader, tests, pattern):
    for path in sorted((ROOT / 'core/tts/tests').glob('test_*.py')):
        spec = importlib.util.spec_from_file_location('bundled_' + path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tests.addTests(loader.loadTestsFromModule(module))
    return tests
