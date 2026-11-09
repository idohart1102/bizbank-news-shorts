"""Lỗi chuyển máy: Python khác, thiếu gói, đường dẫn trắng, máy chưa có tập."""
import importlib.metadata
import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'core'))
from news import cli
from news.config import Config


class InstallTest(unittest.TestCase):
    def test_runtime_rejects_wrong_python_and_missing_or_drifted_package(self):
        from news.runtime import problems
        def version(name):
            if name == 'jsonschema':
                raise importlib.metadata.PackageNotFoundError(name)
            return '0.0.0'
        with mock.patch('importlib.metadata.version', side_effect=version):
            errors = problems(ROOT, python_version=(3, 14, 0))
        self.assertTrue(any('3.12' in e and '3.14' in e for e in errors), errors)
        self.assertTrue(any('jsonschema' in e for e in errors), errors)
        self.assertTrue(any('pyyaml' in e.lower() and '0.0.0' in e for e in errors), errors)

    def test_runtime_accepts_project_environment(self):
        from news.runtime import problems
        self.assertEqual(problems(ROOT), [])

    def test_last_episode_on_clean_machine_has_clear_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Config()
            cfg.data_dir = Path(tmp) / 'absent'
            with self.assertRaisesRegex(SystemExit, 'Chưa có tập nào'):
                cli.find_episode(cfg, 'last')

    def test_launcher_from_other_directory_and_path_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix='news install ') as tmp:
            root = Path(tmp)
            (root / 'bin').mkdir()
            shutil.copy2(ROOT / 'bin/news', root / 'bin/news')
            (root / '.venv').symlink_to(ROOT / '.venv', target_is_directory=True)
            (root / 'core').symlink_to(ROOT / 'core', target_is_directory=True)
            shutil.copy2(ROOT / 'requirements.lock', root / 'requirements.lock')
            shutil.copy2(ROOT / '.python-version', root / '.python-version')
            shutil.copytree(ROOT / 'config', root / 'config', ignore=shutil.ignore_patterns('machine.yaml'))
            (root / 'outside/news').mkdir(parents=True)
            (root / 'outside/news/__init__.py').write_text('raise RuntimeError("shadowed news")')
            out = subprocess.run([str(root / 'bin/news'), '--help'], cwd=root / 'outside', capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn('doctor', out.stdout)

    def test_launcher_missing_venv_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'bin').mkdir()
            shutil.copy2(ROOT / 'bin/news', root / 'bin/news')
            out = subprocess.run([str(root / 'bin/news'), 'doctor'], capture_output=True, text=True)
            self.assertNotEqual(out.returncode, 0)
            self.assertIn('bootstrap', out.stderr)
            self.assertNotIn('Traceback', out.stderr)

    def test_bootstrap_rejects_old_node_before_touching_environment(self):
        with tempfile.TemporaryDirectory(prefix='news bootstrap ') as tmp:
            root = Path(tmp)
            (root / 'bin').mkdir()
            shutil.copy2(ROOT / 'bin/bootstrap', root / 'bin/bootstrap')
            tools = root / 'tools'
            tools.mkdir()
            (tools / 'node').write_text('#!/bin/sh\necho "Cần Node.js 22.x" >&2\nexit 1\n')
            (tools / 'node').chmod(0o755)
            for name in ('uv', 'npm', 'ffmpeg', 'ffprobe'):
                (tools / name).symlink_to(shutil.which('true'))
            (root / '.venv').mkdir()
            sentinel = root / '.venv/keep'
            sentinel.write_text('unchanged')
            with mock.patch.dict(os.environ, {'PATH': str(tools) + os.pathsep + '/usr/bin:/bin'}):
                out = subprocess.run([str(root / 'bin/bootstrap')], capture_output=True, text=True)
            self.assertNotEqual(out.returncode, 0)
            self.assertIn('Node.js 22', out.stderr)
            self.assertEqual(sentinel.read_text(), 'unchanged')

    def test_local_doctor_does_not_contact_paid_or_remote_services(self):
        from news.doctor import check
        with mock.patch('urllib.request.urlopen', side_effect=AssertionError('network forbidden')), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertTrue(check(Config(), local=True), output.getvalue())

    def test_cutout_old_macos_skips_without_compiling(self):
        from news.media import cutout_tool
        with mock.patch('platform.system', return_value='Darwin'), mock.patch('platform.mac_ver', return_value=('13.7', ('', '', ''), 'arm64')):
            self.assertIsNone(cutout_tool())

    def test_hook_installer_preserves_custom_guard_hook(self):
        sys.path.insert(0, str(ROOT / 'core/scripts'))
        from install_hooks import install
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            hook = root / '.git/hooks/pre-commit'
            custom = '#!/bin/sh\necho custom\n.venv/bin/python -I core/scripts/guard_repo.py\n'
            hook.write_text(custom)
            install(root)
            self.assertEqual(hook.read_text(), custom)
            self.assertIn('pre-push', (root / '.git/hooks/pre-push').read_text())

    def test_hook_installer_migrates_legacy_and_can_run_twice(self):
        sys.path.insert(0, str(ROOT / 'core/scripts'))
        from install_hooks import install
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            hook = root / '.git/hooks/pre-commit'
            hook.write_text('#!/bin/sh\nexec "/old/repo/.venv/bin/python" -I "/old/repo/core/scripts/guard_repo.py" pre-commit\n')
            install(root)
            self.assertNotIn('/old/repo', hook.read_text())
            self.assertIn('git rev-parse --show-toplevel', hook.read_text())
            first = hook.read_text()
            install(root)
            self.assertEqual(hook.read_text(), first)
            self.assertTrue(os.access(hook, os.X_OK))

    def test_relative_repo_root_loads_its_machine_config(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp, mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('NEWS_MACHINE_CONFIG', None)
            root = Path(tmp)
            (root / 'config').mkdir()
            shutil.copy2(ROOT / 'config/channel.yaml', root / 'config/channel.yaml')
            (root / 'config/machine.yaml').write_text('data_dir: custom-data\n', encoding='utf-8')
            cfg = Config(os.path.relpath(root))
            self.assertEqual(cfg.data_dir.resolve(), root.resolve() / 'custom-data')

    def test_relative_machine_config_is_relative_to_repo(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {'NEWS_MACHINE_CONFIG': 'config/other.yaml'}):
            root = Path(tmp)
            (root / 'config').mkdir()
            shutil.copy2(ROOT / 'config/channel.yaml', root / 'config/channel.yaml')
            (root / 'config/other.yaml').write_text('data_dir: custom-data\n', encoding='utf-8')
            self.assertEqual(Config(root).data_dir.resolve(), root.resolve() / 'custom-data')


if __name__ == '__main__':
    unittest.main()
