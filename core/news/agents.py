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
import urllib.error
import urllib.request
from pathlib import Path

from .checks import schema, validate_schema
from .config import ROOT
from .episode import write_text


class AgentError(Exception):
    pass


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
               "--model", conf["model"], "--json-schema", json.dumps(schema(schema_name)),
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


def router(conf, prompt, schema_name, workdir, tools, timeout):
    """API kiểu OpenAI chat completions (9router hoặc nhà cung cấp khác)."""
    body = {"model": conf["model"], "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": schema_name, "schema": schema(schema_name), "strict": True}}}
    headers = {"Content-Type": "application/json"}
    key = os.environ.get(conf.get("key_env", "ROUTER_API_KEY"))
    if key:
        headers["Authorization"] = f"Bearer {key}"
    request = urllib.request.Request(conf["url"].rstrip("/") + "/chat/completions",
                                     data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise AgentError(f"router HTTP {error.code}: {error.read()[:300]!r}") from None
    except OSError as error:
        raise AgentError(f"router không gọi được: {error}") from None
    return extract_json(payload["choices"][0]["message"]["content"])


def codex_cli(conf, prompt, schema_name, workdir, tools, timeout):
    """Codex tác tử: được ghi file trong thư mục tập (tải ảnh), trả JSON theo schema."""
    schema_file = Path(workdir) / "logs" / f".schema-{schema_name}.json"
    last = Path(workdir) / "logs" / f".codex-{schema_name}-{int(time.time())}.txt"
    write_text(schema_file, json.dumps(schema(schema_name)))
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


def run(cfg, episode, role, step, context, schema_name, tools=(), timeout=900, agentic=False):
    conf = dict(cfg.machine["agents"][role])
    backend = conf.get("agentic_backend", "codex_cli") if agentic else conf["backend"]
    prompt = build_prompt(step, context)
    stamp = time.strftime("%H%M%S")
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
        problems = validate_schema(schema_name, result)
        write_text(log_dir / f"{stamp}-{step}-{role}.{name}.json", json.dumps(result, ensure_ascii=False, indent=1))
        if problems:
            errors.append(f"{name}: sai schema: {problems[:3]}")
            continue
        return result
    raise AgentError("; ".join(errors))
