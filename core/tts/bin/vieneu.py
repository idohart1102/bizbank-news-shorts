#!/usr/bin/env python3
"""Bộ cài và CLI VieNeu local; chỉ installer được tải mạng, runtime chạy offline."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[3]
UPSTREAM = 'https://github.com/pnnbao97/VieNeu-TTS.git'
REVISION = '22dd2ef2a89bba24a77da6dbc84c75f7f4fda05b'
VIENEU_HOME = Path(os.environ.get('VIENEU_HOME', REPO / 'local/vieneu')).expanduser().resolve()
SOURCE = VIENEU_HOME / 'source'
PYTHON = SOURCE / '.venv/bin/python'


def environment(online=False):
    return {**os.environ, 'HF_HOME': str(VIENEU_HOME / 'hf-cache'),
            'HF_HUB_OFFLINE': '0' if online else '1', 'HF_HUB_DISABLE_TELEMETRY': '1'}


def install():
    VIENEU_HOME.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists():
        subprocess.run(['git', 'clone', '--no-checkout', '--filter=blob:none', UPSTREAM, str(SOURCE)], check=True)
        subprocess.run(['git', '-C', str(SOURCE), 'checkout', '--detach', REVISION], check=True)
    current = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(SOURCE), 'status', '--porcelain'], text=True).strip()
    if current != REVISION or dirty:
        raise ValueError('Source VieNeu khác bản khóa hoặc có sửa đổi; giữ nguyên, hãy chuyển bản cũ sang nơi khác trước khi cài.')
    subprocess.run(['uv', 'sync', '--frozen', '--python', '3.12'], cwd=SOURCE, check=True)
    subprocess.run([str(PYTHON), '-I', str(Path(__file__).resolve()), '--worker', 'download'],
                   env=environment(online=True), check=True)
    subprocess.run([str(PYTHON), '-I', str(Path(__file__).resolve()), '--worker', 'status'],
                   env=environment(), check=True)
    print('Đã cài VieNeu riêng tại local; chưa bật service/lịch. Kiểm: bin/vieneu voices')


def file_hash(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def identity(args):
    return hashlib.sha256(json.dumps({
        'text': Path(args.file).read_text(encoding='utf-8').strip(), 'voice': args.voice,
        'speed': args.speed, 'source': REVISION,
    }, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def reuse(args):
    """Chỉ dùng lại đúng text/voice/speed và audio chưa bị thay; không ghi đè ngầm."""
    target = Path(args.out)
    if not target.exists() or args.replace:
        return False
    stamp = target.with_suffix(target.suffix + '.vieneu.json')
    try:
        metadata = json.loads(stamp.read_text(encoding='utf-8'))
        if metadata['request_hash'] == identity(args) and metadata['audio_hash'] == file_hash(target):
            print('dùng lại kết quả cũ VieNeu: ' + str(target))
            return True
    except (OSError, ValueError, KeyError):
        pass
    raise ValueError('Audio đã có nhưng khác yêu cầu hoặc thiếu metadata. Chỉ dùng --replace khi muốn tạo lại.')


def worker(args):
    from vieneu import Vieneu
    tts = Vieneu(mode='v3turbo', backend='onnx', device='cpu', precision='fp32')
    voices = tts.list_preset_voices()
    if args.command in ('download', 'status', 'voices'):
        print(json.dumps({'ready': True, 'backend': 'onnx/cpu/fp32', 'source': REVISION,
                          'voices': [{'label': label, 'id': voice} for label, voice in voices]}, ensure_ascii=False))
        return
    if args.voice not in {voice for _, voice in voices}:
        raise ValueError('Không có giọng này; tra bin/vieneu voices, dùng đúng id.')
    text = Path(args.file).read_text(encoding='utf-8').strip()
    if not text:
        raise ValueError('Văn bản tạo giọng rỗng.')
    target = Path(args.out).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='vieneu-', dir=target.parent) as tmp:
        wav, mp3 = Path(tmp) / 'voice.wav', Path(tmp) / 'voice.mp3'
        audio = tts.infer(text, voice=args.voice)
        if len(audio) == 0:
            raise ValueError('VieNeu trả audio rỗng.')
        tts.save(audio, str(wav))
        subprocess.run([args.ffmpeg, '-nostdin', '-v', 'error', '-y', '-i', str(wav),
                        '-af', f'atempo={args.speed},loudnorm=I=-14:TP=-1.5:LRA=11',
                        '-ar', '48000', '-b:a', '192k', str(mp3)], check=True)
        os.replace(mp3, target)
    stamp = target.with_suffix(target.suffix + '.vieneu.json')
    metadata = {'request_hash': identity(args), 'audio_hash': file_hash(target),
                'provider': 'vieneu', 'voice': args.voice, 'speed': args.speed, 'source': REVISION}
    part = stamp.with_suffix('.json.part')
    part.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(part, stamp)
    print('VieNeu local: ' + str(target))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('install', 'status', 'voices', 'download'):
        commands.add_parser(name)
    say = commands.add_parser('say')
    say.add_argument('--file', required=True)
    say.add_argument('--out', required=True)
    say.add_argument('--voice', required=True)
    say.add_argument('--speed', type=float, default=1.0)
    say.add_argument('--ffmpeg', default='ffmpeg')
    say.add_argument('--replace', action='store_true')
    args = parser.parse_args()
    if args.command == 'say':
        if not 0.5 <= args.speed <= 1.1:
            raise ValueError('Tốc độ phải từ 0.5 đến 1.1 (luật video: không tăng quá 1.1x).')
        if Path(args.out).suffix.lower() != '.mp3':
            raise ValueError('--out phải có đuôi .mp3.')
        if not args.worker and reuse(args):
            return
    if args.worker:
        worker(args)
    elif args.command == 'install':
        install()
    else:
        if not PYTHON.is_file():
            raise ValueError('Chưa cài VieNeu. Chạy bin/vieneu install.')
        current = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip()
        if current != REVISION:
            raise ValueError('Source VieNeu khác phiên bản khóa; chạy bin/vieneu install để kiểm tra.')
        command = [str(PYTHON), '-I', str(Path(__file__).resolve()), '--worker', *sys.argv[1:]]
        raise SystemExit(subprocess.run(command, env=environment(online=args.command == 'download')).returncode)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print('VieNeu: ' + str(error), file=sys.stderr)
        sys.exit(1)
