"""Duyệt nguồn ngoài danh sách ưu tiên (config/sources.yaml).

Nguồn có tên miền trong danh sách hoặc đã được Sếp duyệt (config/sources_approved.yaml) thì dùng được.
Nguồn lạ: tập dừng ở needs_human, yêu cầu ghi vào <data>/source_requests.jsonl; Sếp duyệt bằng
`bin/news sources approve <tên miền>` hoặc từ chối bằng `bin/news sources reject <tên miền>`.
"""
import json
import time
from urllib.parse import urlparse

import yaml

from .config import ROOT

APPROVED = ROOT / "config" / "sources_approved.yaml"


def domain(url):
    host = urlparse(url if "://" in url else f"https://{url}").netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def load_decisions():
    data = yaml.safe_load(APPROVED.read_text(encoding="utf-8")) if APPROVED.exists() else None
    data = data or {}
    return {"approved": data.get("approved") or [], "rejected": data.get("rejected") or []}


def listed_domains():
    config = yaml.safe_load((ROOT / "config" / "sources.yaml").read_text(encoding="utf-8"))
    return {domain(s["url"]) for s in config["press"]}


def matches(host, domains):
    return any(host == d or host.endswith("." + d) for d in domains)


def status(url):
    host = domain(url)
    decisions = load_decisions()
    if matches(host, {d["domain"] for d in decisions["rejected"]}):
        return "rejected"
    if matches(host, listed_domains()):
        return "listed"
    if matches(host, {d["domain"] for d in decisions["approved"]}):
        return "approved"
    return "pending"


def review(cfg, episode_id, sources):
    """Trả (lỗi với nguồn bị từ chối, danh sách tên miền đang chờ duyệt). Ghi yêu cầu duyệt cho nguồn lạ."""
    errors, pending = [], {}
    for source in sources:
        state = status(source["url"])
        if state == "rejected":
            errors.append(f"Nguồn {domain(source['url'])} đã bị Sếp từ chối, bỏ nguồn này hoặc chọn tin khác")
        elif state == "pending":
            pending.setdefault(domain(source["url"]), source)
    if pending:
        path = cfg.data_dir / "source_requests.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        waiting = {r["domain"] for r in read_requests(cfg)}
        with path.open("a", encoding="utf-8") as handle:
            for host, source in pending.items():
                if host not in waiting:
                    handle.write(json.dumps({"domain": host, "url": source["url"], "publisher": source.get("publisher"),
                                             "episode": episode_id, "at": time.strftime("%Y-%m-%dT%H:%M:%S")},
                                            ensure_ascii=False) + "\n")
    return errors, sorted(pending)


def read_requests(cfg):
    path = cfg.data_dir / "source_requests.jsonl"
    if not path.exists():
        return []
    requests = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in requests if status(r["url"]) == "pending"]


def decide(host, verdict, note=""):
    host = domain(host)
    decisions = load_decisions()
    for key in ("approved", "rejected"):
        decisions[key] = [d for d in decisions[key] if d["domain"] != host]
    decisions[verdict].append({"domain": host, "date": time.strftime("%Y-%m-%d"), "note": note})
    header = "# Nguồn ngoài danh sách ưu tiên đã được Sếp duyệt/từ chối. Sửa qua `bin/news sources approve|reject`.\n"
    APPROVED.write_text(header + yaml.safe_dump(decisions, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return host
