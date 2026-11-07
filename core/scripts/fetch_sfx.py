#!/usr/bin/env python3
"""Tải kho tiếng động theo assets/sfx/LICENSES.csv từ CDN Pixabay.

File mp3 không vào Git: giấy phép Pixabay không cho phân phối lại âm thanh dạng file rời,
nên repo chỉ giữ danh sách nguồn. Người nhận repo chạy lệnh này để có lại đúng bộ file
(kiểm sha256). --update ghi sha256, thời lượng, LUFS vào CSV sau lần tải đầu.
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SFX = ROOT / "assets" / "sfx"
CSV_PATH = SFX / "LICENSES.csv"
CDN = "https://cdn.pixabay.com/download/audio/"


def measure(path):
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True, check=True)
    loud = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                          capture_output=True, text=True)
    match = re.findall(r"I:\s+(-?[\d.]+) LUFS", loud.stderr)
    return round(float(probe.stdout.strip()), 2), (float(match[-1]) if match else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--update", action="store_true", help="ghi sha256/thời lượng/LUFS vào CSV")
    args = parser.parse_args()
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
    failed = []
    for row in rows:
        target = SFX / row["file"]
        if not target.exists():
            request = urllib.request.Request(CDN + row["cdn_path"], headers={"User-Agent": "news-video-sfx/1.0"})
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    data = response.read()
            except OSError as error:
                failed.append(f"{row['id']}: {error}")
                continue
            if not data.startswith((b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
                failed.append(f"{row['id']}: không phải mp3")
                continue
            target.write_bytes(data)
            row["downloaded_at"] = time.strftime("%Y-%m-%d")
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if row["sha256"] and row["sha256"] != digest and not args.update:
            failed.append(f"{row['id']}: sha256 khác bản đã ghi (nguồn đổi file?)")
        if args.update:
            row["sha256"] = digest
            row["duration_s"], row["lufs"] = measure(target)
    if args.update:
        with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        index = {r["id"]: {"file": r["file"], "category": r["category"], "duration_s": float(r["duration_s"]),
                           "lufs": float(r["lufs"]) if r["lufs"] else None} for r in rows if r["duration_s"]}
        (SFX / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(rows) - len(failed)}/{len(rows)} file sẵn sàng")
    if failed:
        print("\n".join(failed), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
