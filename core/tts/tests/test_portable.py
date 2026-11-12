import importlib.util
from importlib.machinery import SourceFileLoader
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_loader(name, SourceFileLoader(name, str(path)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortableTtsTest(unittest.TestCase):
    def test_cpu_backend_is_selected_outside_apple_silicon(self):
        align = load('portable_align', ROOT / 'bin/align.py')
        with mock.patch('platform.system', return_value='Linux'), mock.patch('platform.machine', return_value='x86_64'), mock.patch.dict(os.environ, {'TTS_ALIGN_BACKEND': ''}):
            self.assertEqual(align.backend(), 'faster-whisper')

    def test_splitting_word_timestamps_preserves_subword_boundaries(self):
        align = load('portable_align', ROOT / 'bin/align.py')
        self.assertEqual(align.split_words([{'word': 'hộ kinh doanh', 'start': 1, 'end': 4}]), [
            {'text': 'hộ', 'start': 1, 'end': 2}, {'text': 'kinh', 'start': 2, 'end': 3}, {'text': 'doanh', 'start': 3, 'end': 4}])

    def test_linux_credentials_are_private_and_readable_by_service(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {'TTS_DATA_DIR': tmp, 'TTS_ENV_FILE': '/nonexistent'}):
            service = load('portable_service', ROOT / 'bin/tts')
            with mock.patch.object(service.sys, 'platform', 'linux'), mock.patch('subprocess.run', side_effect=AssertionError('no keychain calls')):
                service.write_secret('test', 'token', 'synthetic-token-value', r'.+', 'test key')
                self.assertEqual(service.read_secret('test', 'token'), 'synthetic-token-value')
            path = Path(tmp) / 'credentials.json'
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_low_match_alignment_exit_code_is_preserved(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {'TTS_ENV_FILE': '/nonexistent'}):
            service = load('low_match_service', ROOT / 'bin/tts')
            text = Path(tmp) / 'text.txt'
            text.write_text('Văn bản mẫu.', encoding='utf-8')
            service.ALIGN_PYTHON = Path(__import__('sys').executable)
            args = SimpleNamespace(audio=str(Path(tmp) / 'audio.wav'), text=str(text), out=str(Path(tmp) / 'out.srt'), words=None)
            with mock.patch('subprocess.run', return_value=SimpleNamespace(returncode=3)):
                with self.assertRaises(SystemExit) as error:
                    service.cmd_align(args)
            self.assertEqual(error.exception.code, 3)

    def test_partial_snapshot_is_not_ready(self):
        state = load('align_state', ROOT / 'bin/align_state.py')
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp)
            (snapshot / 'config.json').write_text('{}')
            self.assertFalse(state.snapshot_ready(snapshot, 'faster-whisper'))
            (snapshot / 'model.bin').write_bytes(b'synthetic weights')
            (snapshot / 'tokenizer.json').write_text('{}')
            self.assertTrue(state.snapshot_ready(snapshot, 'faster-whisper'))
            (snapshot / 'model.bin').unlink()
            self.assertFalse(state.snapshot_ready(snapshot, 'faster-whisper'))

    def test_service_environment_keeps_config_but_not_credentials(self):
        with mock.patch.dict(os.environ, {'TTS_ENV_FILE': '/nonexistent', 'TTS_PORT': '8801', 'HF_HOME': '/tmp/synthetic-hf-cache', 'VBEE_TOKEN': 'synthetic-token-value'}):
            service = load('service_env', ROOT / 'bin/tts')
            env = service.service_environment()
            self.assertEqual(env['TTS_PORT'], '8801')
            self.assertEqual(Path(env['HF_HOME']).resolve(), Path('/tmp/synthetic-hf-cache').resolve())
            self.assertNotIn('VBEE_TOKEN', env)

    def test_cpu_transcription_keeps_word_timestamps_and_stays_offline(self):
        from types import SimpleNamespace
        align = load('cpu_align', ROOT / 'bin/align.py')
        word = SimpleNamespace(word='hộ kinh doanh', start=1, end=4)
        model = SimpleNamespace(transcribe=lambda *a, **kw: ([SimpleNamespace(words=[word])], None))
        constructor = mock.Mock(return_value=model)
        with mock.patch.dict(os.environ, {'TTS_ALIGN_BACKEND': 'faster-whisper'}), mock.patch.dict('sys.modules', {'faster_whisper': SimpleNamespace(WhisperModel=constructor)}):
            words = align.transcribe('synthetic.wav', '')
            self.assertEqual(words[-1], {'text': 'doanh', 'start': 3, 'end': 4})
            self.assertTrue(constructor.call_args.kwargs['local_files_only'])
            self.assertEqual(constructor.call_args.kwargs['device'], 'cpu')

    def test_service_does_not_freeze_values_read_from_env_file(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {}, clear=True):
            path = Path(tmp) / 'tts.env'
            path.write_text('TTS_PORT=8802\n', encoding='utf-8')
            os.environ['TTS_ENV_FILE'] = str(path)
            service = load('file_service_env', ROOT / 'bin/tts')
            self.assertEqual(service.PORT, 8802)
            self.assertNotIn('TTS_PORT', service.service_environment())
            self.assertEqual(Path(service.service_environment()['TTS_ENV_FILE']).resolve(), path.resolve())


class AlignMatchTest(unittest.TestCase):
    def test_numbers_heard_as_digits_count_as_matched(self):
        import runpy
        align = runpy.run_path(str(Path(__file__).resolve().parents[1] / "bin" / "align.py"), run_name="align_test")["align"]
        script = "giá còn mười chín nghìn đồng hôm nay".split()
        heard = [{"text": t, "start": i * 0.3, "end": i * 0.3 + 0.25}
                 for i, t in enumerate(["giá", "còn", "19", ".000", "đồng", "hôm", "nay"])]
        _, ratio = align(script, heard)
        self.assertEqual(ratio, 1.0)
        wrong = [dict(w, text=t) for w, t in zip(heard, ["giá", "còn", "mười", "tám", "nghìn", "hôm", "nay"])]
        _, ratio = align(script, wrong)
        self.assertLess(ratio, 1.0)
