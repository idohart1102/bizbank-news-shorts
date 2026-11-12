"""Đọc RSS các nguồn trong config/sources.yaml → raw_feed.json. Tất định, không dùng AI.

Lọc: trong `window_hours`, khớp ít nhất một từ khóa (so không dấu), bỏ trùng link. AI chỉ nhận danh sách đã lọc.
"""
import concurrent.futures
import email.utils
import html
import re
import time
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import yaml

from . import sources
from .config import ROOT, ensure_online

UA = "Mozilla/5.0 (compatible; news-video/1.0)"
VN = timezone(timedelta(hours=7))


def plain(text):
    """Bỏ dấu, chữ thường: 'Hóa đơn' → 'hoa don'."""
    text = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in text if unicodedata.category(c) != "Mn").lower()


def clean(text):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def parse_date(value):
    if not value:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(value.strip())
    except (TypeError, ValueError):
        parsed = None
        for parse in (lambda v: datetime.fromisoformat(v.replace("Z", "+00:00")),
                      lambda v: datetime.strptime(v, "%m/%d/%Y %I:%M:%S %p")):  # kiểu baochinhphu.vn, giờ VN
            try:
                parsed = parse(value.strip())
                break
            except ValueError:
                continue
        if parsed is None:
            return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=VN)


def fetch(url, timeout=20):
    ensure_online(f"tải RSS {url}")
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(10_000_000)  # theleader.vn ~5,4 MB
    if raw[:2] == b"\x1f\x8b":
        import gzip
        raw = gzip.decompress(raw)
    return raw


def parse_feed(raw, source):
    items = []
    try:  # báo VN hay khai sai encoding: nội dung hợp lệ UTF-8 thì luôn đọc là UTF-8
        root = ET.fromstring(re.sub(r"^\s*<\?xml[^>]*\?>", "", raw.decode("utf-8")))
    except UnicodeDecodeError:
        root = ET.fromstring(raw)
    for item in root.iter("item"):
        get = lambda tag: (item.findtext(tag) or "").strip()
        items.append({"title": clean(get("title")), "url": get("link"), "summary": clean(get("description"))[:400],
                      "published_at": parse_date(get("pubDate")), "publisher": source["name"], "tier": source["tier"],
                      "group": source.get("group", 0),
                      "image": (item.find("enclosure").get("url") if item.find("enclosure") is not None else None)})
    return items


def load_config():
    return yaml.safe_load((ROOT / "config" / "sources.yaml").read_text(encoding="utf-8"))


def source_guide():
    """Nhóm ưu tiên nguồn (danh sách của Sếp) để đưa vào prompt: vai trò từng nhóm + báo thuộc nhóm nào."""
    config = load_config()
    return {"Vai trò nhóm": {str(k): v for k, v in config.get("groups", {}).items()},
            "Báo theo nhóm": {s["name"]: {"group": s.get("group", 0), "tier": s["tier"], "url": s["url"]}
                              for s in config["press"]},
            "Nguồn ngoài đã được Sếp duyệt": [d["domain"] for d in sources.load_decisions()["approved"]],
            "Nguồn Sếp đã từ chối (không dùng)": [d["domain"] for d in sources.load_decisions()["rejected"]]}


def collect(now=None):
    config = load_config()
    now = now or datetime.now(VN)
    since = now - timedelta(hours=config.get("window_hours", 48))
    keywords = [re.compile(rf"\b{re.escape(plain(k))}\b") for k in config.get("keywords", [])]
    jobs = [(source, url) for source in config["press"] for url in source.get("rss", [])]
    items, report = [], []
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        futures = {pool.submit(fetch, url): (source, url) for source, url in jobs}
        for future in concurrent.futures.as_completed(futures):
            source, url = futures[future]
            try:
                parsed = parse_feed(future.result(), source)
            except Exception as error:  # một nguồn lỗi không chặn cả lần chạy
                report.append({"feed": url, "ok": False, "error": str(error)[:200]})
                continue
            report.append({"feed": url, "ok": True, "items": len(parsed)})
            items += parsed
    seen, kept = set(), []
    for item in sorted(items, key=lambda i: i["published_at"] or since, reverse=True):
        if not item["url"].startswith("http") or item["url"] in seen:
            continue
        if not item["published_at"] or item["published_at"] < since:
            continue
        haystack = plain(f"{item['title']} {item['summary']}")
        if keywords and not any(k.search(haystack) for k in keywords):
            continue
        seen.add(item["url"])
        kept.append({**item, "published_at": item["published_at"].isoformat()})
    return {"fetched_at": now.isoformat(), "window_hours": config.get("window_hours", 48), "feeds": report,
            "total": len(items), "items": kept}


if __name__ == "__main__":
    import json
    result = collect()
    print(json.dumps({k: v for k, v in result.items() if k != "items"}, ensure_ascii=False, indent=1))
    print(len(result["items"]), "tin sau lọc")
    for item in result["items"][:8]:
        print("-", item["publisher"], "|", item["title"][:90])
