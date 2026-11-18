"""Tạo PNG bằng image_gen tích hợp của Codex CLI, không qua gateway/API key riêng."""
import json
from pathlib import Path
import subprocess
import uuid


def generate(cfg, prompt, size, transparent):
    from .agents import AgentError
    conf = cfg.machine['agents']['codex']
    if conf.get('image_backend', 'codex_cli') != 'codex_cli':
        raise AgentError('Tạo ảnh chỉ hỗ trợ image_backend=codex_cli; không tự gọi 9router.')
    work = cfg.root / 'local' / 'imagegen' / uuid.uuid4().hex
    work.mkdir(parents=True)
    result, image, schema = work / 'result.json', work / 'output.png', work / 'schema.json'
    schema.write_text(json.dumps({
        'type': 'object', 'properties': {
            'status': {'type': 'string', 'enum': ['done', 'unavailable']},
            'reason': {'type': 'string'},
        }, 'required': ['status', 'reason'], 'additionalProperties': False,
    }), encoding='utf-8')
    instruction = (
        'Create exactly one raster asset with the built-in image_gen tool. '
        f'Requested size/aspect: {size}. '
        + ('Use a genuinely transparent background and preserve alpha. ' if transparent else 'Use an opaque background. ')
        + 'Save or copy the final PNG to output.png in the working directory. '
        'Do not use 9router, HTTP image APIs, API keys, SVG, code-drawn placeholders, or another provider. '
        'If image_gen is unavailable or fails, return status=unavailable and explain; do not substitute a fake image. '
        'Do not modify project source or create additional assets. '
        'Return status=done only after output.png exists.\n\nImage brief:\n' + prompt
    )
    (work / 'prompt.txt').write_text(instruction, encoding='utf-8')
    command = [conf.get('bin', 'codex'), '-a', 'never', 'exec', '--skip-git-repo-check', '--ephemeral',
               '-s', 'workspace-write', '-C', str(work), '--enable', 'image_generation', '--json',
               '--output-schema', str(schema), '-o', str(result), *conf.get('cli_args', []), '-']
    try:
        with (work / 'events.jsonl').open('w', encoding='utf-8') as events, \
                (work / 'stderr.log').open('w', encoding='utf-8') as errors:
            out = subprocess.run(command, input=instruction, text=True, stdout=events, stderr=errors,
                                 timeout=conf.get('image_timeout', 1800))
        if out.returncode or not result.is_file():
            raise AgentError(f'Codex tạo ảnh lỗi (exit {out.returncode}); xem {work}. Không gọi lại qua router.')
        report = json.loads(result.read_text(encoding='utf-8'))
        if report.get('status') != 'done':
            raise AgentError('Codex không tạo được ảnh: ' + str(report.get('reason', 'image_gen unavailable'))[:300])
        if not image.is_file() or image.is_symlink():
            raise AgentError(f'Codex chưa lưu PNG hợp lệ tại {image}.')
        raw = image.read_bytes()
        if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
            raise AgentError('Codex trả file không phải PNG; không nhận SVG/placeholder.')
        checked = subprocess.run([cfg.bin('ffprobe'), '-v', 'error', '-show_entries', 'stream=codec_name,width,height',
                                  '-of', 'json', str(image)], capture_output=True, text=True, timeout=30)
        streams = json.loads(checked.stdout).get('streams', []) if checked.returncode == 0 else []
        if not streams or streams[0].get('codec_name') != 'png' or min(streams[0].get('width', 0), streams[0].get('height', 0)) <= 0:
            raise AgentError('PNG Codex tạo không đọc được bằng FFprobe.')
        return raw
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        raise AgentError(f'Codex tạo ảnh: {type(error).__name__}; xem {work}.') from None
