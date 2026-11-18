"""VieNeu local: lỗi cài đặt rõ ràng, không ghi đè audio, không tính phí Vbee."""
import os
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'core'))
from news.config import Config
from news import steps
from news.episode import Episode


class VieneuTest(unittest.TestCase):
    def test_matching_audio_can_be_reused_without_installing_model(self):
        adapter = runpy.run_path(str(ROOT / 'core/tts/bin/vieneu.py'))
        with tempfile.TemporaryDirectory() as tmp:
            text, audio = Path(tmp) / 'text.txt', Path(tmp) / 'voice.mp3'
            text.write_text('Bản tin hôm nay.', encoding='utf-8')
            audio.write_bytes(b'cached result')
            args = argparse.Namespace(file=str(text), voice='Ngọc Huyền', speed=1.0)
            stamp = audio.with_suffix('.mp3.vieneu.json')
            stamp.write_text(json.dumps({'request_hash': adapter['identity'](args),
                                         'audio_hash': hashlib.sha256(b'cached result').hexdigest()}))
            command = [sys.executable, str(ROOT / 'core/tts/bin/vieneu.py'), 'say',
                       '--file', str(text), '--out', str(audio), '--voice', 'Ngọc Huyền']
            env = {**os.environ, 'VIENEU_HOME': tmp}
            reused = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(reused.returncode, 0, reused.stderr)
            self.assertIn('dùng lại', reused.stdout)
            audio.write_bytes(b'tampered')
            changed = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertNotEqual(changed.returncode, 0)
            self.assertIn('--replace', changed.stderr)
            self.assertEqual(audio.read_bytes(), b'tampered')

    def test_changed_text_or_voice_is_not_reused(self):
        adapter = runpy.run_path(str(ROOT / 'core/tts/bin/vieneu.py'))
        with tempfile.TemporaryDirectory() as tmp:
            text, audio = Path(tmp) / 'text.txt', Path(tmp) / 'voice.mp3'
            text.write_text('Tin cũ.', encoding='utf-8')
            audio.write_bytes(b'cached result')
            args = argparse.Namespace(file=str(text), out=str(audio), voice='Ngọc Huyền', speed=1.0, replace=False)
            stamp = audio.with_suffix('.mp3.vieneu.json')
            stamp.write_text(json.dumps({'request_hash': adapter['identity'](args),
                                         'audio_hash': hashlib.sha256(b'cached result').hexdigest()}))
            text.write_text('Tin mới.', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, '--replace'):
                adapter['reuse'](args)
            text.write_text('Tin cũ.', encoding='utf-8')
            args.voice = 'Mai Anh'
            with self.assertRaisesRegex(ValueError, '--replace'):
                adapter['reuse'](args)

    def test_missing_install_has_actionable_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = subprocess.run([sys.executable, str(ROOT / 'core/tts/bin/vieneu.py'), 'status'],
                                 env={**os.environ, 'VIENEU_HOME': tmp}, capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn('bin/vieneu install', out.stderr)
        self.assertNotIn('Traceback', out.stderr)

    def test_existing_audio_is_not_overwritten_without_replace(self):
        with tempfile.TemporaryDirectory() as tmp:
            text, audio = Path(tmp) / 'text.txt', Path(tmp) / 'voice.mp3'
            text.write_text('Bản tin hôm nay.', encoding='utf-8')
            audio.write_bytes(b'keep')
            out = subprocess.run([sys.executable, str(ROOT / 'core/tts/bin/vieneu.py'), 'say',
                                  '--file', str(text), '--out', str(audio), '--voice', 'Ngọc Huyền'],
                                 env={**os.environ, 'VIENEU_HOME': tmp}, capture_output=True, text=True)
            self.assertNotEqual(out.returncode, 0)
            self.assertIn('--replace', out.stderr)
            self.assertEqual(audio.read_bytes(), b'keep')

    def test_vieneu_pipeline_uses_local_cli_and_align_without_vbee_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Config()
            cfg.dry = False
            cfg.data_dir = Path(tmp)
            cfg.channel['tts'].update(provider='vieneu', voice='Ngọc Huyền')
            ep = Episode.create(cfg.data_dir, '2026-01-01-1030', 'manual')
            ep.file('script_tts.txt').write_text('Bản tin hôm nay.', encoding='utf-8')
            ctx = steps.Ctx(cfg, ep)
            calls = []
            def execute(*command, **kw):
                calls.append(tuple(str(c) for c in command))
                return ''
            with mock.patch.dict(os.environ, {'NEWS_OFFLINE': '0'}), \
                    mock.patch('news.voice.preflight', return_value=('bin/tts', '', os.environ.copy())), \
                    mock.patch.object(ctx, 'sh', side_effect=execute), \
                    mock.patch('news.checks.segment_times', return_value=[]), \
                    mock.patch.object(ctx, 'json', return_value={}):
                steps.run_voice(ctx)
            self.assertEqual(Path(calls[0][0]).name, 'vieneu')
            self.assertEqual(calls[0][1], 'say')
            self.assertNotIn('--pauses', calls[0])
            self.assertNotIn('--srt', calls[0])
            self.assertEqual(calls[1][0:2], ('bin/tts', 'align'))
            self.assertIn('--words', calls[1])
            self.assertFalse((cfg.data_dir / '_ledger.jsonl').exists())


if __name__ == '__main__':
    unittest.main()
