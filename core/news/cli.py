"""news: lệnh điều khiển hệ thống short tin tức."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

from . import lessons, pipeline, steps
from .config import Config
from .episode import Episode


def find_episode(cfg, name):
    if name == "last":
        candidates = sorted((p for p in cfg.data_dir.iterdir() if (p / "state.json").exists()), key=lambda p: p.stat().st_mtime)
        if not candidates:
            raise SystemExit("Chưa có tập nào")
        return Episode(candidates[-1])
    path = cfg.data_dir / name
    if not (path / "state.json").exists():
        raise SystemExit(f"Không có tập {name}")
    return Episode(path)


def cmd_run(cfg, args):
    with pipeline.Lock(cfg.data_dir):
        episode = find_episode(cfg, args.resume) if args.resume else Episode.create(
            cfg.data_dir, time.strftime("%Y-%m-%d-%H%M"), args.trigger)
        print(f"Tập: {episode.path}")
        pipeline.run(cfg, episode, until=args.until)
        if not args.no_distill:
            try:
                promoted = pipeline.distill(cfg, [episode.id])
                if promoted:
                    print(f"Bài học mới được áp dụng: {', '.join(promoted)}")
            except Exception as error:  # chưng cất lỗi không làm hỏng tập
                print(f"Chưng cất bài học lỗi: {error}", file=sys.stderr)
        print(f"Trạng thái: {episode.state['status']}" + (f" — {episode.state['blocker']}" if episode.state["blocker"] else ""))
        sys.exit(0 if episode.state["status"] in ("done", "paused") else 2)


def cmd_status(cfg, args):
    if args.episode:
        episode = find_episode(cfg, args.episode)
        print(json.dumps(episode.state, ensure_ascii=False, indent=1))
        return
    if not cfg.data_dir.exists():
        return print("Chưa có tập nào")
    for path in sorted(cfg.data_dir.iterdir())[-15:]:
        if (path / "state.json").exists():
            state = Episode(path).state
            print(f"{state['id']:45} {state['status']:12} {state.get('blocker') or ''}"[:160])


def cmd_feedback(cfg, args):
    episode = find_episode(cfg, args.episode)
    if args.step not in steps.ORDER:
        raise SystemExit(f"step phải thuộc: {', '.join(steps.ORDER)}")
    lessons.record(cfg, episode, args.step, "owner_feedback", [args.text], source="owner")
    print("Đã ghi góp ý. Lần chưng cất tới sẽ biến thành luật áp dụng ngay (góp ý của chủ kênh không cần lặp lại).")


def cmd_lessons(cfg, args):
    if args.action == "distill":
        print(f"Thăng hạng: {pipeline.distill(cfg) or 'không có'}")
    else:
        for c in lessons.load_candidates(cfg):
            print(f"{c['id']:14} {c['status']:9} {len(c['episodes'])} tập  {c['rule']}")


def cmd_doctor(cfg, args):
    ok = True

    def report(name, good, detail=""):
        nonlocal ok
        ok = ok and good
        print(f"{'✓' if good else '✗'} {name}" + (f": {detail}" if detail else ""))

    for name in ("ffmpeg", "ffprobe", "node", "npx"):
        report(name, bool(shutil.which(cfg.bin(name))), shutil.which(cfg.bin(name)) or "không thấy")
    sfx = json.loads((cfg.root / "assets/sfx/index.json").read_text(encoding="utf-8"))
    missing = [k for k, v in sfx.items() if not (cfg.root / "assets/sfx" / v["file"]).exists()]
    report("kho sfx", not missing, f"thiếu {len(missing)} file, chạy core/scripts/fetch_sfx.py" if missing else f"{len(sfx)} file")
    template = cfg.root / cfg.video["template"]
    report("template overlay", template.exists(), str(template) if template.exists() else "chưa có (dùng overlay tạm)")
    report("config/machine.yaml", (cfg.root / "config/machine.yaml").exists(), "dùng mặc định" if not (cfg.root / "config/machine.yaml").exists() else "")
    tts = cfg.machine["tts"]
    if tts["backend"] == "platform_tts":
        try:
            with urllib.request.urlopen(tts["platform_tts_url"] + "/health", timeout=5) as response:
                health = json.loads(response.read())
            report("tts", health.get("vbee_configured") and health.get("align_ready"), json.dumps(health))
        except OSError as error:
            report("tts", False, f"{tts['platform_tts_url']}: {error}")
    for role, conf in cfg.machine["agents"].items():
        binary = conf.get("bin")
        if conf["backend"].endswith("_cli") or conf.get("fallback", "").endswith("_cli"):
            report(f"agent {role} ({binary})", bool(shutil.which(binary or "")), shutil.which(binary or "") or "không thấy")
        if conf["backend"] == "router":
            try:
                urllib.request.urlopen(conf["url"].rstrip("/") + "/models", timeout=5)
                report(f"agent {role} router", True, conf["url"])
            except OSError as error:
                report(f"agent {role} router", False, str(error))
    hook = cfg.root / ".git/hooks/pre-commit"
    report("git hook guard_repo", hook.exists() and "guard_repo" in hook.read_text(), "chạy bin/bootstrap" if not hook.exists() else "")
    sys.exit(0 if ok else 1)


def main():
    parser = argparse.ArgumentParser(prog="news", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="chạy một tập (mới hoặc tiếp tục)")
    run.add_argument("--resume", metavar="TAP", help="tiếp tục tập (tên thư mục hoặc 'last')")
    run.add_argument("--until", choices=steps.ORDER, help="dừng sau bước này")
    run.add_argument("--dry", action="store_true", help="dữ liệu mẫu, không tốn tiền")
    run.add_argument("--trigger", default="manual", choices=["manual", "schedule"])
    run.add_argument("--no-distill", action="store_true")
    status = sub.add_parser("status", help="trạng thái các tập")
    status.add_argument("episode", nargs="?")
    feedback = sub.add_parser("feedback", help="góp ý của chủ kênh → bài học")
    feedback.add_argument("episode")
    feedback.add_argument("step")
    feedback.add_argument("text")
    les = sub.add_parser("lessons", help="bài học")
    les.add_argument("action", choices=["show", "distill"])
    sub.add_parser("doctor", help="kiểm máy đủ điều kiện chạy")
    args = parser.parse_args()
    if getattr(args, "dry", False):
        os.environ["NEWS_DRY"] = "1"
    cfg = Config()
    {"run": cmd_run, "status": cmd_status, "feedback": cmd_feedback, "lessons": cmd_lessons,
     "doctor": cmd_doctor}[args.command](cfg, args)


if __name__ == "__main__":
    main()
