"""Cơ chế bài học.

sự kiện (local, không vào Git) → chưng cất (Claude) → lessons/candidates.yaml → thăng hạng → lessons/rules/<step>.md
- Ứng viên được thăng hạng khi xuất hiện ở ≥ PROMOTE_AFTER tập khác nhau, hoặc đến từ góp ý của chủ kênh.
- Luật không được chứa link, tên tập, nội dung tin (chặn bằng guard_repo.py).
- Bài học không được nới luật cứng; chỉ docs/decisions.md đổi được luật cứng.
"""
import json
import re

import yaml

from .config import ROOT
from .episode import now, write_text

PROMOTE_AFTER = 2
STEP_ALIASES = {"collect-news": "collect", "pick-stories": "pick", "write-script": "write", "review-script": "review",
                "gather-assets": "assets", "plan-edit": "plan", "qc-video": "qc"}  # tên skill → tên bước
LESSONS = ROOT / "lessons"
FORBIDDEN = re.compile(r"https?://|\b\d{4}-\d{2}-\d{2}-|episodes/", re.I)


def events_dir(cfg):
    return cfg.data_dir / "_lessons"


def record(cfg, episode, step, gate, errors, source="gate"):
    """Ghi một sự kiện khi cổng trượt hoặc chủ kênh góp ý."""
    event = {"at": now(), "episode": episode.id if episode else None, "step": step, "gate": gate,
             "source": source, "errors": list(errors)[:20], "distilled": False}
    path = events_dir(cfg) / "events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    if episode:
        with episode.file("lessons.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def load_events(cfg):
    path = events_dir(cfg) / "events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_candidates(cfg):
    """Bản đầy đủ (có mã tập làm bằng chứng) chỉ nằm ở local."""
    path = events_dir(cfg) / "candidates.yaml"
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("candidates", []) if path.exists() else []


def save_candidates(cfg, candidates):
    dump = lambda value: yaml.safe_dump({"candidates": value}, allow_unicode=True, sort_keys=False)
    write_text(events_dir(cfg) / "candidates.yaml", dump(candidates))
    write_text(LESSONS / "candidates.yaml", dump(public_candidates(candidates)))  # vào Git, không có mã tập


def merge_candidates(cfg, new_items, episode_ids, source):
    """Gộp kết quả chưng cất vào candidates.yaml; trả danh sách id được thăng hạng."""
    candidates = load_candidates(cfg)
    by_id = {c["id"]: c for c in candidates}
    promoted = []
    for item in new_items:
        if FORBIDDEN.search(item["rule"]):
            continue  # luật phải tổng quát
        item = dict(item, step=STEP_ALIASES.get(item["step"], item["step"]))
        target = by_id.get(item.get("merge_with") or "")
        if not target:
            target = {"id": f"{item['step']}-{len(candidates) + 1:03d}", "step": item["step"], "rule": item["rule"],
                      "why": item["why"], "episodes": [], "from_owner": False, "status": "candidate",
                      "first_seen": now()[:10]}
            candidates.append(target)
            by_id[target["id"]] = target
        target["episodes"] = sorted(set(target["episodes"]) | set(episode_ids))
        target["from_owner"] = target["from_owner"] or source == "owner"
        target["last_seen"] = now()[:10]
        if target["status"] == "candidate" and (len(target["episodes"]) >= PROMOTE_AFTER or target["from_owner"]):
            target["status"] = "active"
            promoted.append(target["id"])
    save_candidates(cfg, candidates)
    write_rules(candidates)
    return promoted


def write_rules(candidates):
    """lessons/rules/<step>.md chỉ chứa luật active; không ghi id tập (dữ liệu sản phẩm)."""
    steps = {}
    for c in candidates:
        if c["status"] == "active":
            steps.setdefault(c["step"], []).append(c)
    for step, items in steps.items():
        lines = [f"- [{c['id']}] {c['rule']} (vì: {c['why']})" for c in items]
        write_text(LESSONS / "rules" / f"{step}.md", "\n".join(lines) + "\n")


def public_candidates(candidates):
    """Bản đưa vào Git: bỏ danh sách tập, chỉ giữ số lần gặp."""
    return [{**{k: v for k, v in c.items() if k != "episodes"}, "evidence": len(c.get("episodes", []))}
            for c in candidates]
