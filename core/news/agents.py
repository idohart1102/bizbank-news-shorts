"""Gọi AI headless qua adapter. Mọi lần gọi ghi prompt + kết quả vào <tap>/logs/agents/.

Vai trò:
- claude: chọn tin, viết, duyệt, plan, QC, gói, chưng cất bài học.
- codex: xử lý văn bản tư liệu (router, không cần duyệt web) và việc cần tác tử (codex_cli: tìm/tải ảnh).
Backend chọn trong config/machine.yaml; thêm backend mới chỉ cần thêm một hàm vào BACKENDS.
"""
import json
import os
import subprocess
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path

from .checks import schema, validate_schema
from .config import ROOT, ensure_online
from .episode import write_text


class AgentError(Exception):
    pass


# Trường chỉ để mô tả, AI hay bỏ sót khi không ép được schema (tìm web qua router): tự điền "" thay vì bỏ cả kết quả.
SOFT_FIELDS = {"asset_search": {"why", "credit", "subject"}}


def fill_soft_fields(schema_name, value, node=None):
    soft = SOFT_FIELDS.get(schema_name)
    if not soft:
        return value
    node = node or agent_schema(schema_name)
    if isinstance(value, dict) and node.get("type") == "object":
        for key in node.get("required", []):
            if key in soft and key not in value:
                value[key] = ""
        for key, child in node.get("properties", {}).items():
            if key in value:
                fill_soft_fields(schema_name, value[key], child)
    elif isinstance(value, list) and "items" in node:
        for item in value:
            fill_soft_fields(schema_name, item, node["items"])
    return value


def agent_schema(name):
    """Schema gửi cho AI: bỏ $schema/title (Claude CLI chỉ nhận draft mặc định)."""
    return {k: v for k, v in schema(name).items() if k not in ("$schema", "title")}


def extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    start = text.find("{")
    if start < 0:
        raise AgentError("Kết quả không có JSON")
    return json.loads(text[start:text.rfind("}") + 1])


def claude_cli(conf, prompt, schema_name, workdir, tools, timeout):
    command = [conf.get("bin", "claude"), "-p", "--output-format", "json", "--no-session-persistence",
               "--model", conf["model"], "--json-schema", json.dumps(agent_schema(schema_name)),
               "--permission-mode", "dontAsk", "--tools", ",".join(tools) if tools else ""]
    if conf.get("max_budget_usd"):
        command += ["--max-budget-usd", str(conf["max_budget_usd"])]
    out = subprocess.run(command, input=prompt, capture_output=True, text=True, timeout=timeout, cwd=workdir)
    if out.returncode != 0:
        raise AgentError(f"claude thoát mã {out.returncode}: {(out.stderr or out.stdout).strip()[-300:]}")
    payload = json.loads(out.stdout)
    if payload.get("is_error"):
        raise AgentError(f"claude báo lỗi: {str(payload.get('result'))[:300]}")
    return payload.get("structured_output") or extract_json(payload.get("result", ""))


_ROUTER_KEY = {}


def router_key(conf):
    """Key 9router: biến môi trường (NINEROUTER_API_KEY) hoặc đọc (chỉ đọc) key đang bật trong DB của 9router.
    Giống cách dự án Tiền Sử làm; không ghi key ra file/log. Nhiều key bật: NINEROUTER_KEY_NAME chọn tên."""
    for name in (conf.get("key_env", "NINEROUTER_API_KEY"), "NINEROUTER_API_KEY", "ROUTER_API_KEY"):
        if os.environ.get(name):
            return os.environ[name]
    db = Path(os.path.expanduser(conf.get("key_db", "~/.9router/db/data.sqlite")))
    if "key" not in _ROUTER_KEY:
        if not db.exists():
            raise AgentError(f"router: không có key (đặt NINEROUTER_API_KEY trong .env hoặc có {db})")
        import sqlite3
        connection = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        name = os.environ.get("NINEROUTER_KEY_NAME")
        query = "select key from apiKeys where isActive=1" + (" and name=?" if name else "") + " order by createdAt limit 1"
        row = connection.execute(query, (name,) if name else ()).fetchone()
        connection.close()
        if not row:
            raise AgentError("router: không có key 9router đang bật")
        _ROUTER_KEY["key"] = row[0]
    return _ROUTER_KEY["key"]


def router_post(conf, path, body, timeout):
    request = urllib.request.Request(conf["url"].rstrip("/") + path, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {router_key(conf)}"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise AgentError(f"router HTTP {error.code}: {error.read()[:300]!r}") from None
    except OSError as error:
        raise AgentError(f"router không gọi được: {error}") from None


def router(conf, prompt, schema_name, workdir, tools, timeout):
    """API kiểu OpenAI. Có tool web_search thì dùng Responses API (tìm web), không thì chat completions."""
    if "web_search" in tools:
        # Responses API có web_search không ép được schema: đưa schema vào prompt để AI trả đủ trường.
        prompt += "\n\n## JSON schema bắt buộc\n" + json.dumps(agent_schema(schema_name), ensure_ascii=False)
        body = {"model": conf["model"], "input": prompt, "tools": [{"type": "web_search"}]}
        payload = router_post(conf, "/responses", body, timeout)
        text = payload.get("output_text") or "".join(
            c.get("text", "") for o in payload.get("output", []) if o.get("type") == "message" for c in o.get("content", []))
        return extract_json(text)
    body = {"model": conf["model"], "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": schema_name, "schema": agent_schema(schema_name), "strict": True}}}
    payload = router_post(conf, "/chat/completions", body, timeout)
    return extract_json(payload["choices"][0]["message"]["content"])


def generate_image(cfg, prompt, size="1024x1536", transparent=False):
    """Ảnh minh họa AI qua 9router (model cấu hình agents.codex.image_model). Trả bytes PNG."""
    ensure_online("tạo ảnh AI")
    import base64
    conf = cfg.machine["agents"]["codex"]
    body = {"model": conf.get("image_model", "cx/gpt-image-2.6-sunburst"), "prompt": prompt, "size": size, "n": 1,
            "output_format": "png"}
    if transparent:
        body["background"] = "transparent"
    data = router_post(conf, "/images/generations", body, 300)["data"][0]
    if data.get("b64_json"):
        return base64.b64decode(data["b64_json"])
    with urllib.request.urlopen(data["url"], timeout=120) as response:
        return response.read()


def codex_cli(conf, prompt, schema_name, workdir, tools, timeout):
    """Codex tác tử: được ghi file trong thư mục tập (tải ảnh), trả JSON theo schema."""
    tag = uuid.uuid4().hex[:6]  # gọi song song: mỗi lượt file riêng, không đè nhau
    schema_file = Path(workdir) / "logs" / f".schema-{schema_name}-{tag}.json"
    last = Path(workdir) / "logs" / f".codex-{schema_name}-{int(time.time())}-{tag}.txt"
    write_text(schema_file, json.dumps(agent_schema(schema_name)))
    command = [conf.get("bin", "codex"), "exec", "--skip-git-repo-check", "--ephemeral", "-s", "workspace-write",
               "-C", str(workdir), "--output-schema", str(schema_file), "-o", str(last), *conf.get("cli_args", []), "-"]
    out = subprocess.run(command, input=prompt, capture_output=True, text=True, timeout=timeout)
    if out.returncode != 0 or not last.exists():
        raise AgentError(f"codex thoát mã {out.returncode}: {out.stderr.strip()[-300:]}")
    return extract_json(last.read_text(encoding="utf-8"))


BACKENDS = {"claude_cli": claude_cli, "router": router, "codex_cli": codex_cli}


def build_prompt(step, context):
    """Ghép prompt: skill của bước + luật bài học của bước + dữ liệu đầu vào."""
    parts = [(ROOT / "core" / "prompts" / f"{step}.md").read_text(encoding="utf-8")]
    rules = ROOT / "lessons" / "rules" / f"{step}.md"
    if rules.exists() and rules.read_text(encoding="utf-8").strip():
        parts.append("## Bài học đã rút ra (bắt buộc tuân theo)\n" + rules.read_text(encoding="utf-8"))
    for title, value in context.items():
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=1)
        parts.append(f"## {title}\n{text}")
    parts.append("Chỉ trả về một JSON object đúng schema, không giải thích thêm.")
    return "\n\n".join(parts)


def run(cfg, episode, role, step, context, schema_name, tools=(), timeout=900, agentic=False, label=None):
    ensure_online(f"gọi AI ({role}/{step})")
    conf = dict(cfg.machine["agents"][role])
    backend = conf.get("agentic_backend", "codex_cli") if agentic else conf["backend"]
    prompt = build_prompt(step, context)
    stamp = time.strftime("%H%M%S") + (f"-{label}" if label else "")
    log_dir = episode.file("logs/agents")
    write_text(log_dir / f"{stamp}-{step}-{role}.prompt.md", prompt)
    attempts = [backend] + ([conf["fallback"]] if conf.get("fallback") and conf["fallback"] != backend else [])
    errors = []
    for name in attempts:
        try:
            result = BACKENDS[name](conf, prompt, schema_name, str(episode.path), list(tools), timeout)
        except (AgentError, subprocess.TimeoutExpired, ValueError, KeyError) as error:
            errors.append(f"{name}: {error}")
            continue
        problems = validate_schema(schema_name, fill_soft_fields(schema_name, result))
        write_text(log_dir / f"{stamp}-{step}-{role}.{name}.json", json.dumps(result, ensure_ascii=False, indent=1))
        if problems:
            errors.append(f"{name}: sai schema: {problems[:3]}")
            continue
        return result
    raise AgentError("; ".join(errors))
