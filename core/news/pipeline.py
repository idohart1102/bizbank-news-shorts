"""Máy trạng thái: chạy các bước theo thứ tự, bỏ qua bước đã xong, quay vòng khi trượt cổng.

Trạng thái tập: running → done | needs_human | failed. Chạy lại `news run --resume <tap>` thì tiếp đúng chỗ.
needs_human: hệ thống tự dừng ở cổng an toàn (hết vòng sửa, hết ngân sách, bước chưa xây, credit không rõ).
"""
import json
import os
import time
import traceback
from pathlib import Path

from . import lessons, outputs, steps
from .episode import Episode, hash_files, now, write_json, write_text


class Lock:
    """Chỉ một lần chạy tại một thời điểm (lịch 10:30/19:00 và chạy tay không chồng nhau)."""

    def __init__(self, data_dir):
        self.path = Path(data_dir) / ".lock"

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            pid = int(self.path.read_text().split()[0] or 0)
            try:
                os.kill(pid, 0)
                raise SystemExit(f"Đang có lần chạy khác (pid {pid}). Bỏ qua.")
            except ProcessLookupError:
                pass  # khóa cũ của tiến trình đã chết
        self.path.write_text(f"{os.getpid()} {now()}")
        return self

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)


def input_hash(ctx, step):
    files = [ctx.ep.file(name) for name in step.inputs] + [steps.ROOT / "lessons" / "rules" / f"{step.name}.md"]
    feedback = ctx.ep.file(f"qa/feedback_{step.name}.json")
    return hash_files(files + [feedback], base=ctx.ep.path)


def outputs_exist(ctx, step):
    return all(ctx.ep.file(name).exists() for name in step.outputs)


def stop(ctx, status, blocker):
    ctx.ep.state["status"], ctx.ep.state["blocker"] = status, blocker
    ctx.ep.save()
    ctx.ep.log(f"DỪNG {status}: {blocker}")
    level = "error" if status == "failed" else "warn"
    outputs.notify(ctx.cfg, level, f"{ctx.ep.id}: {status}", blocker, ctx.ep)


def run(cfg, episode, until=None):
    ctx = steps.Ctx(cfg, episode)
    episode.state["status"], episode.state["blocker"] = "running", None
    episode.save()
    index = 0
    while index < len(steps.ORDER):
        step = steps.BY_NAME[steps.ORDER[index]]
        st = episode.step(step.name)
        digest = input_hash(ctx, step)
        if st["state"] == "done" and st.get("input_hash") == digest and outputs_exist(ctx, step):
            index += 1
            continue
        if step.paid and cfg.enforce_budget:
            budget = cfg.channel.get("budget", {}).get("vbee_chars_per_day", 0)
            need = len(ctx.ep.file("script_tts.txt").read_text(encoding="utf-8"))
            if budget and steps.chars_today(cfg) + need > budget:
                return stop(ctx, "needs_human", f"Vượt ngân sách Vbee hôm nay ({steps.chars_today(cfg)}+{need} > {budget} ký tự)")
        st.update(state="running", started_at=now())
        st["attempts"] += 1
        episode.save()
        episode.log(f"→ {step.name} (lần {st['attempts']}, vòng {st['rounds']})")
        try:
            step.run(ctx)
            errors = step.check(ctx)
        except steps.NotReady as error:
            st["state"] = "blocked"
            return stop(ctx, "needs_human", str(error))
        except Exception as error:  # lỗi kỹ thuật: thử lại một lần rồi dừng
            write_text(episode.file(f"logs/{step.name}-error.txt"), traceback.format_exc())
            st["state"], st["error"] = "error", str(error)[:500]
            if st["attempts"] < 2 and not step.paid:
                episode.save()
                continue
            return stop(ctx, "failed", f"{step.name}: {error}")
        if errors:
            lessons.record(cfg, episode, step.name, f"check_{step.name}", errors)
            st["rounds"] += 1
            st["last_errors"] = errors[:10]
            target = step.retry_to or step.name
            if st["rounds"] >= step.max_rounds:
                st["state"] = "failed_gate"
                return stop(ctx, "needs_human", f"{step.name} trượt {st['rounds']} vòng: " + "; ".join(errors[:3]))
            write_json(episode.file(f"qa/feedback_{target}.json"), errors)
            episode.log(f"✗ {step.name}: {len(errors)} lỗi → làm lại từ {target}")
            st["state"] = "retry"
            for name in steps.ORDER[steps.ORDER.index(target):]:
                if name != step.name:
                    episode.step(name)["state"] = "pending"
            episode.save()
            index = steps.ORDER.index(target)
            continue
        st.update(state="done", input_hash=input_hash(ctx, step), finished_at=now(), error=None)
        episode = ctx.ep  # bước pick có thể đổi tên thư mục
        episode.save()
        episode.log(f"✓ {step.name}")
        if until and step.name == until:
            episode.state["status"] = "paused"
            episode.save()
            return
        index += 1
    episode.state["status"] = "done"
    episode.save()
    write_report(ctx)
    outputs.notify(cfg, "info", f"{ctx.ep.id}: xong", "Video đã vào hàng chờ đăng", ctx.ep)


def write_report(ctx):
    state = ctx.ep.state
    lines = [f"# Báo cáo {state['id']}", "", f"- Trạng thái: {state['status']}", f"- Bắt đầu: {state['created_at']}",
             f"- Kết thúc: {state['updated_at']}", "", "| Bước | Trạng thái | Lần chạy | Vòng sửa |", "|---|---|---|---|"]
    lines += [f"| {name} | {s['state']} | {s['attempts']} | {s['rounds']} |" for name, s in state["steps"].items()]
    write_text(ctx.ep.file("report.md"), "\n".join(lines) + "\n")


def distill(cfg, episode_ids=None):
    """Chưng cất sự kiện chưa xử lý thành ứng viên bài học (Claude). Chạy sau mỗi lần chạy, không chặn luồng."""
    from . import agents
    events = [e for e in lessons.load_events(cfg) if not e["distilled"] and (not episode_ids or e["episode"] in episode_ids)]
    if not events or cfg.dry:
        return []
    holder = Episode(cfg.data_dir / "_lessons")
    holder.state = {"id": "_lessons"}
    (holder.path / "logs").mkdir(parents=True, exist_ok=True)
    existing = [{k: c[k] for k in ("id", "step", "rule", "status")} for c in lessons.load_candidates(cfg)]
    result = agents.run(cfg, holder, "claude", "distill", {"Sự kiện mới": events, "Ứng viên đã có": existing},
                        "lesson_candidates")
    owner = any(e["source"] == "owner" for e in events)
    promoted = lessons.merge_candidates(cfg, result["candidates"], sorted({e["episode"] for e in events if e["episode"]}),
                                        "owner" if owner else "gate")
    path = lessons.events_dir(cfg) / "events.jsonl"
    marked = [dict(e, distilled=True) if e in events else e for e in lessons.load_events(cfg)]
    write_text(path, "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in marked))
    return promoted
