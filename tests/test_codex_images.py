"""Hợp đồng tạo ảnh: gọi Codex CLI, không gọi router, không nhận placeholder."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'core'))
from news import agents
from news.config import Config


class CodexImagesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='codex image ')
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.cfg = Config()
        self.cfg.root = self.folder
        self.cli = self.folder / 'codex'
        self.cli.write_text('''#!/usr/bin/env python3
import json,os,pathlib,sys
a=sys.argv[1:]
assert a[:3] == ['-a','never','exec'], a
assert '--ephemeral' in a and 'image_generation' in a
assert a[a.index('-s')+1] == 'workspace-write'
p=pathlib.Path(a[a.index('-C')+1])
prompt=sys.stdin.read()
assert 'image_gen' in prompt and '1536x1024' in prompt
mode=os.environ.get('FAKE_IMAGE_MODE','ok')
if mode == 'failed': sys.exit(2)
if mode != 'missing': (p/'output.png').write_bytes(pathlib.Path(os.environ['FAKE_PNG']).read_bytes() if mode == 'ok' else b'<svg/>')
pathlib.Path(a[a.index('-o')+1]).write_text(json.dumps({'status':'done','reason':''}))
''', encoding='utf-8')
        self.cli.chmod(0o755)
        self.png = self.folder / 'fixture.png'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=64x64',
                        '-frames:v', '1', str(self.png)], check=True)
        self.cfg.machine['agents']['codex'] = {'backend': 'codex_cli', 'image_backend': 'codex_cli', 'bin': str(self.cli)}
        patch = mock.patch.dict(os.environ, {'NEWS_OFFLINE': '0', 'FAKE_PNG': str(self.png), 'FAKE_IMAGE_MODE': 'ok'})
        patch.start()
        self.addCleanup(patch.stop)

    def test_returns_png_from_codex_without_router(self):
        with mock.patch.object(agents, 'router_post', side_effect=AssertionError('router forbidden')):
            result = agents.generate_image(self.cfg, 'A ceramic mug.', size='1536x1024')
        self.assertEqual(result, self.png.read_bytes())

    def test_missing_or_fake_image_is_rejected_without_fallback(self):
        for mode in ('missing', 'corrupt', 'failed'):
            with self.subTest(mode=mode), mock.patch.dict(os.environ, {'FAKE_IMAGE_MODE': mode}), \
                    mock.patch.object(agents, 'router_post', side_effect=AssertionError('router forbidden')):
                with self.assertRaises(agents.AgentError):
                    agents.generate_image(self.cfg, 'A ceramic mug.', size='1536x1024')

    def test_offline_never_starts_image_generation(self):
        with mock.patch.dict(os.environ, {'NEWS_OFFLINE': '1'}), \
                mock.patch('subprocess.run', side_effect=AssertionError('must not execute')):
            with self.assertRaisesRegex(RuntimeError, 'NEWS_OFFLINE'):
                agents.generate_image(self.cfg, 'A ceramic mug.')


if __name__ == '__main__':
    unittest.main()
