"""Một tập = một thư mục dữ liệu + state.json. Ghi file luôn qua file tạm để không hỏng khi bị ngắt."""
import hashlib
import json
import os
import time
from pathlib import Path


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=1) + "\n")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def hash_files(paths, base=None):
    """Mã băm nội dung; tên file tính tương đối theo `base` để đổi tên thư mục tập không làm chạy lại."""
    digest = hashlib.sha256()
    for path in sorted(str(p) for p in paths):
        name = os.path.relpath(path, base) if base else path
        digest.update(name.encode())
        p = Path(path)
        if p.is_file():
            with p.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(chunk)
        else:
            digest.update(b"<missing>")
    return digest.hexdigest()[:16]


class Episode:
    def __init__(self, path):
        self.path = Path(path)
        self.state_path = self.path / "state.json"
        self.state = read_json(self.state_path) if self.state_path.exists() else None

    @classmethod
    def create(cls, data_dir, stamp, trigger):
        path = Path(data_dir) / stamp
        suffix = 1
        while path.exists():
            suffix += 1
            path = Path(data_dir) / f"{stamp}-{suffix}"
        for sub in ("qa", "audio", "assets", "render", "logs"):
            (path / sub).mkdir(parents=True, exist_ok=True)
        episode = cls(path)
        episode.state = {"id": path.name, "slug": None, "status": "running", "trigger": trigger,
                         "created_at": now(), "updated_at": now(), "steps": {}, "blocker": None}
        episode.save()
        return episode

    @property
    def id(self):
        return self.state["id"]

    def file(self, relative):
        return self.path / relative

    def save(self):
        self.state["updated_at"] = now()
        write_json(self.state_path, self.state)

    def step(self, name):
        return self.state["steps"].setdefault(name, {"state": "pending", "attempts": 0, "rounds": 0})

    def log(self, message):
        line = f"{now()} {message}\n"
        with (self.path / "logs" / "run.log").open("a", encoding="utf-8") as handle:
            handle.write(line)

    def rename_with_slug(self, slug):
        """Thêm slug vào tên thư mục sau khi chọn tin: <ngày>-<giờ>-<slug>."""
        safe = "".join(c if c.isalnum() or c == "-" else "-" for c in slug.lower()).strip("-")[:40]
        if not safe or self.path.name.endswith(safe):
            return
        base = self.path.name
        if self.state.get("slug") and base.endswith("-" + self.state["slug"]):
            base = base[: -len(self.state["slug"]) - 1]  # chọn lại tin: thay slug cũ
        target = self.path.with_name(f"{base}-{safe}")
        os.replace(self.path, target)
        self.path, self.state_path = target, target / "state.json"
        self.state["slug"], self.state["id"] = safe, target.name
        self.save()
