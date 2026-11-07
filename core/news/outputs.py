"""Đầu ra ra ngoài: thông báo và hàng chờ đăng bài. Cả hai mới ở dạng chờ đấu nối.

- Thông báo: luôn ghi <data>/notifications.jsonl; thêm thông báo macOS nếu bật.
  Telegram: đặt notify.telegram.enabled=true trong channel.yaml + TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID trong .env.
- Đăng bài: mỗi nền tảng một file <data>/outbox/<tap>.<platform>.json trạng thái pending_connection.
  Adapter nền tảng (core/news/publishers/<platform>.py, hàm publish(item) -> dict) viết sau; có adapter thì gửi.
"""
import importlib
import json
import os
import platform
import shutil
import subprocess
import urllib.parse
import urllib.request

from .episode import now, read_json, write_json


def notify(cfg, level, title, message, episode=None):
    entry = {"at": now(), "level": level, "title": title, "message": message, "episode": episode.id if episode else None}
    path = cfg.data_dir / "notifications.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if cfg.dry or os.environ.get("NEWS_NOTIFY") == "0":
        return
    telegram = cfg.channel.get("notify", {}).get("telegram", {})
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if telegram.get("enabled") and token and chat:
        data = urllib.parse.urlencode({"chat_id": chat, "text": f"[{level}] {title}\n{message}"}).encode()
        try:
            urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=15)
        except OSError:
            pass  # thông báo hỏng không được làm hỏng lần chạy
    if cfg.machine["notify"].get("macos") and platform.system() == "Darwin" and shutil.which("osascript"):
        script = f"display notification {json.dumps(message[:200])} with title {json.dumps('News video: ' + title)}"
        subprocess.run(["osascript", "-e", script], capture_output=True)


def enqueue(cfg, episode):
    """Xếp video vào hàng chờ cho từng nền tảng; gửi luôn nếu nền tảng đã có adapter và được bật."""
    publish = cfg.channel.get("publish", {})
    meta = read_json(episode.file("meta.json"))
    results = {}
    for name in publish.get("platforms", []):
        item = {"episode": episode.id, "platform": name, "video": str(episode.file("render/final.mp4")),
                "meta": meta, "status": "pending_connection", "queued_at": now(), "result": None}
        if publish.get("mode") == "live" and publish.get(name, {}).get("enabled"):
            try:
                adapter = importlib.import_module(f"news.publishers.{name}")
                item["result"], item["status"] = adapter.publish(item), "published"
            except Exception as error:  # adapter lỗi: giữ trong hàng chờ
                item["status"], item["result"] = "failed", str(error)[:300]
        write_json(cfg.data_dir / "outbox" / f"{episode.id}.{name}.json", item)
        results[name] = item["status"]
    return results
