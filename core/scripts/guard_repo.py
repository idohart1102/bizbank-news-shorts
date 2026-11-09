#!/usr/bin/env python3
"""Chặn dữ liệu sản phẩm/video và bí mật đi vào Git (hook pre-commit, pre-push).

Repo chỉ chứa hệ thống. Bị chặn: file trong vùng dữ liệu (episodes/, outbox...), media, file > 2 MB,
cấu hình máy/.env, chuỗi giống token, và luật bài học có link hoặc mã tập.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PREFIXES = ("episodes/", "publish/outbox/", "logs/", "lessons/events/", "lessons/metrics/", "local/", "core/tts/data/")
ALLOWED = {"episodes/.gitkeep"}
MEDIA = re.compile(r"\.(mp4|mov|mkv|webm|mp3|wav|m4a|aac|flac|ogg|jpg|jpeg|png|webp|gif|psd)$", re.I)
MEDIA_ALLOWED = ("assets/template/", "tests/fixtures/")   # template của chủ kênh, fixture nhỏ
SECRET = re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.|sk-[A-Za-z0-9]{20,}|\b\d{8,10}:[A-Za-z0-9_-]{30,}")
LESSON_LEAK = re.compile(r"https?://|\b\d{4}-\d{2}-\d{2}-\d{4}")
MAX_BYTES = 2 * 1024 * 1024


def files(mode):
    if mode == "pre-push":
        out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=ROOT)
    else:
        out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], capture_output=True,
                             text=True, cwd=ROOT)
    return [line for line in out.stdout.splitlines() if line]


def problems(path):
    full = ROOT / path
    if path in ALLOWED:
        return []
    found = []
    if path.startswith(DATA_PREFIXES):
        found.append("dữ liệu sản phẩm (vùng dữ liệu tập)")
    if path in ("config/machine.yaml", ".env") or path.endswith(".env"):
        found.append("cấu hình/bí mật của máy")
    if MEDIA.search(path) and not path.startswith(MEDIA_ALLOWED):
        found.append("file media")
    if full.is_file():
        if full.stat().st_size > MAX_BYTES:
            found.append(f"file lớn {full.stat().st_size // 1024} KB")
        elif not MEDIA.search(path):
            text = full.read_text(encoding="utf-8", errors="ignore")
            if SECRET.search(text):
                found.append("có chuỗi giống token/API key")
            if path.startswith("lessons/") and LESSON_LEAK.search(text):
                found.append("bài học chứa link hoặc mã tập")
    return found


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "pre-commit"
    bad = {path: issues for path in files(mode) if (issues := problems(path))}
    if bad:
        print("guard_repo: chặn vì repo chỉ chứa hệ thống, không chứa dữ liệu sản phẩm/bí mật:", file=sys.stderr)
        for path, issues in bad.items():
            print(f"  {path}: {', '.join(issues)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
