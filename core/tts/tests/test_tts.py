"""Kiểm tra end-to-end bản thật của bin/tts với máy chủ KingCong giả, không tốn credit."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin" / "tts"
KEY = "kingcongapikey_" + "a" * 48
TEXT = "Đây là đoạn văn bản dùng để kiểm thử dịch vụ chuyển văn bản thành giọng nói, dài hơn một trăm ký tự theo đúng yêu cầu của KingCong."


class Fake:
    """Trạng thái máy chủ giả."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.creates = []
        self.polls = 0
        self.polls_until_done = 2
        self.create_mode = "ok"
        self.poll_mode = "ok"
        self.download_headers = []
        self.block_download = False


FAKE = Fake()


class Upstream(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, value, raw=None):
        body = raw if raw is not None else json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FAKE.creates.append({"path": self.path, "body": body, "key": self.headers.get("xi-api-key")})
        if FAKE.create_mode == "hang":
            self.connection.close()  # mất kết nối sau khi đã nhận yêu cầu
            return
        if FAKE.create_mode == "reject":
            self.send(403, {"message": "chưa nạp credit"})
            return
        self.send(200, {"status": "success", "task_id": f"task{len(FAKE.creates)}", "task_status": "pending",
                        "credit_cost": 221, "new_balance": 1000})

    def do_GET(self):
        if self.path.startswith("/v1/task/"):
            FAKE.polls += 1
            if FAKE.poll_mode == "fail":
                self.send(200, {"status": "success", "task_status": "failed", "error": "engine lỗi"})
            elif FAKE.poll_mode == "hold" or FAKE.polls < FAKE.polls_until_done:
                # Chỉ có status=success, không được hiểu nhầm thành đã xong.
                self.send(200, {"status": "success"})
            else:
                base = f"http://127.0.0.1:{self.server.server_port}"
                self.send(200, {"status": "success", "task_status": "done", "credit_cost": 225,
                                "audio_url": f"{base}/files/a.mp3", "srt_url": f"{base}/files/a.srt"})
        elif self.path.startswith("/files/"):
            FAKE.download_headers.append(self.headers.get("xi-api-key"))
            if FAKE.block_download:
                self.send(500, {})
            else:
                self.send(200, None, raw=b"ID3-audio" if self.path.endswith(".mp3") else b"1\n00:00 --> 00:01\nchao\n")
        elif self.path == "/v1/credits":
            self.send(200, {"status": "success", "data": {"credits": 250000}})
        else:
            self.send(404, {"message": "không có"})


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class TtsCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        threading.Thread(target=cls.upstream.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.upstream.shutdown()

    def setUp(self):
        FAKE.reset()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.port = free_port()
        self.env = {
            **os.environ, "TTS_ENV_FILE": "/nonexistent", "KINGCONG_API_KEY": KEY, "TTS_PORT": str(self.port), "TTS_DATA_DIR": self.tmp.name,
            "VBEE_APP_ID": "", "VBEE_TOKEN": "", "TTS_VBEE_KEYCHAIN_SERVICE": "bizbank-test-absent-" + Path(self.tmp.name).name,
            "KINGCONG_BASE_URL": f"http://127.0.0.1:{self.upstream.server_port}",
            "TTS_POLL_INTERVAL": "0.02", "TTS_POLL_TIMEOUT": "2", "TTS_KEYCHAIN_SERVICE": "bizbank-test-absent-" + Path(self.tmp.name).name,
        }
        self.start()
        self.addCleanup(self.stop)

    def start(self, env=None):
        self.process = subprocess.Popen([sys.executable, "-I", str(BIN), "serve"], env=env or self.env, stderr=subprocess.DEVNULL)
        for _ in range(200):
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.2):
                    return
            except OSError:
                time.sleep(0.02)
        self.fail("Dịch vụ không khởi động")

    def stop(self):
        self.process.kill()
        self.process.wait()

    def call(self, method, path, body=None, headers=None):
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        for name, value in (headers or {}).items():
            request.add_header(name, value)
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                raw = response.read()
                status = response.status
        except urllib.error.HTTPError as error:
            raw = error.read()
            status = error.code
        try:
            return status, json.loads(raw)
        except ValueError:
            return status, raw

    def wait(self, job_id, *states):
        for _ in range(300):
            _, job = self.call("GET", f"/v1/jobs/{job_id}")
            if job["state"] in states:
                return job
            time.sleep(0.02)
        self.fail(f"Job kẹt ở {job['state']}")

    def test_success_downloads_files_without_leaking_key(self):
        status, job = self.call("POST", "/v1/speech", {"text": TEXT, "project": "demo", "export_srt": True})
        self.assertEqual(status, 202)
        job = self.wait(job["id"], "done", "failed", "stalled")
        self.assertEqual(job["state"], "done", job["error"])
        self.assertEqual(job["credit_cost"], 225)
        self.assertEqual(self.call("GET", job["audio_url"])[1], b"ID3-audio")
        self.assertIn(b"chao", self.call("GET", job["srt_url"])[1])
        self.assertGreaterEqual(FAKE.polls, 2, "status=success không được coi là xong")
        create = FAKE.creates[0]
        self.assertEqual(create["key"], KEY)
        self.assertEqual(create["path"], "/v1/text-to-speech/BGC20Gf5f36lf17lw2Y1N")
        self.assertEqual(create["body"]["model_id"], "vieten_speech")
        self.assertNotIn("project", create["body"])
        self.assertEqual(FAKE.download_headers, [None, None])
        stored = b"".join(p.read_bytes() for p in Path(self.tmp.name).glob("jobs.sqlite3*"))
        self.assertNotIn(KEY.encode(), stored)
        self.assertNotIn(TEXT.encode(), stored)
        usage = self.call("GET", "/v1/usage")[1]["usage"]
        self.assertEqual(usage[0]["project"], "demo")
        self.assertEqual(usage[0]["credits"], 225)

    def test_voice_settings_are_forwarded_and_change_identity(self):
        base = {"text": TEXT, "project": "demo", "provider": "elevenlabs", "voice_id": "abc"}
        status, job = self.call("POST", "/v1/speech", {**base, "stability": 0.6, "similarity": 0.75})
        self.assertEqual(status, 202)
        self.wait(job["id"], "done", "failed", "stalled")
        self.assertEqual(FAKE.creates[0]["body"]["stability"], 0.6)
        self.assertEqual(FAKE.creates[0]["body"]["similarity"], 0.75)
        status, job = self.call("POST", "/v1/speech", {**base, "stability": 0.5, "similarity": 0.75})
        self.assertEqual(status, 202, "đổi thông số phải tạo job mới")
        self.wait(job["id"], "done", "failed", "stalled")
        self.assertEqual(self.call("POST", "/v1/speech", {**base, "stability": 2})[0], 400)
        status, job = self.call("POST", "/v1/speech", {**base})
        self.wait(job["id"], "done", "failed", "stalled")
        self.assertNotIn("stability", FAKE.creates[-1]["body"])

    def test_style_is_forwarded_validated_and_changes_reuse_identity(self):
        base = {"text": TEXT, "provider": "elevenlabs", "voice_id": "abc", "style": 0.1}
        status, first = self.call("POST", "/v1/speech", base)
        self.assertEqual(status, 202)
        self.wait(first["id"], "done")
        self.assertEqual(FAKE.creates[-1]["body"]["style"], 0.1)
        _, reused = self.call("POST", "/v1/speech", base)
        self.assertEqual(reused["id"], first["id"])
        _, changed = self.call("POST", "/v1/speech", {**base, "style": 0.2})
        self.assertNotEqual(changed["id"], first["id"])
        self.wait(changed["id"], "done")
        for invalid in (-0.1, 1.1, True, "0.1"):
            self.assertEqual(self.call("POST", "/v1/speech", {**base, "style": invalid})[0], 400)

    def test_identical_request_reuses_result_and_force_creates_new(self):
        _, first = self.call("POST", "/v1/speech", {"text": TEXT})
        self.wait(first["id"], "done")
        status, second = self.call("POST", "/v1/speech", {"text": TEXT, "project": "khac"})
        self.assertEqual((status, second["id"], second["reused"]), (200, first["id"], True))
        self.assertEqual(len(FAKE.creates), 1)
        status, third = self.call("POST", "/v1/speech", {"text": TEXT, "force": True})
        self.assertEqual(status, 202)
        self.assertNotEqual(third["id"], first["id"])
        self.wait(third["id"], "done")
        self.assertEqual(len(FAKE.creates), 2)
        status, other = self.call("POST", "/v1/speech", {"text": TEXT, "speed": 1.2})
        self.assertEqual(status, 202)

    def test_invalid_requests_never_reach_upstream(self):
        for body, code in (
            ({"text": "ngắn"}, "text_too_short"),
            ({"text": TEXT, "speed": 3}, "invalid_request"),
            ({"text": TEXT, "provider": "lạ"}, "invalid_request"),
            ({"text": TEXT, "provider": "elevenlabs"}, "invalid_request"),
            ({"text": TEXT, "voice_id": "../v1/credits"}, "invalid_request"),
            ({"text": TEXT, "with_transcript": True}, "invalid_request"),
            ({"text": TEXT, "export_srt": "yes"}, "invalid_request"),
        ):
            status, value = self.call("POST", "/v1/speech", body)
            self.assertEqual((status, value["error"]["code"]), (400, code), body)
        self.assertEqual(FAKE.creates, [])

    def test_rejects_browser_style_requests(self):
        status, _ = self.call("GET", "/health", headers={"Host": "evil.example"})
        self.assertEqual(status, 403)
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/v1/speech", data=json.dumps({"text": TEXT}).encode(),
                                         method="POST", headers={"Content-Type": "text/plain"})
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request, timeout=5)
        self.assertEqual(caught.exception.code, 415)
        self.assertEqual(FAKE.creates, [])

    def test_lost_connection_on_submit_is_not_retried(self):
        FAKE.create_mode = "hang"
        _, job = self.call("POST", "/v1/speech", {"text": TEXT})
        job = self.wait(job["id"], "uncertain", "failed", "done")
        self.assertEqual(job["state"], "uncertain")
        self.assertEqual(len(FAKE.creates), 1)
        status, value = self.call("POST", "/v1/speech", {"text": TEXT})
        self.assertEqual((status, value["error"]["code"]), (409, "needs_decision"))
        self.assertEqual(len(FAKE.creates), 1)
        FAKE.create_mode = "ok"
        status, forced = self.call("POST", "/v1/speech", {"text": TEXT, "force": True})
        self.assertEqual(status, 202)
        self.assertEqual(self.wait(forced["id"], "done", "failed")["state"], "done")

    def test_upstream_rejection_and_task_failure(self):
        FAKE.create_mode = "reject"
        _, job = self.call("POST", "/v1/speech", {"text": TEXT})
        job = self.wait(job["id"], "failed")
        self.assertIn("chưa nạp credit", job["error"])
        FAKE.create_mode = "ok"
        FAKE.poll_mode = "fail"
        status, retry = self.call("POST", "/v1/speech", {"text": TEXT})
        self.assertEqual(status, 202, "job failed không được chặn gửi lại")
        self.assertIn("engine lỗi", self.wait(retry["id"], "failed")["error"])

    def test_restart_resumes_polling_without_second_charge(self):
        FAKE.poll_mode = "hold"
        _, job = self.call("POST", "/v1/speech", {"text": TEXT})
        self.wait(job["id"], "polling")
        self.stop()
        FAKE.poll_mode = "ok"
        self.start()
        self.assertEqual(self.wait(job["id"], "done", "failed", "stalled")["state"], "done")
        self.assertEqual(len(FAKE.creates), 1)

    def test_stalled_job_can_resume(self):
        FAKE.block_download = True
        _, job = self.call("POST", "/v1/speech", {"text": TEXT})
        job = self.wait(job["id"], "stalled", "done")
        self.assertEqual(job["state"], "stalled")
        status, value = self.call("POST", "/v1/speech", {"text": TEXT})
        self.assertEqual(status, 409)
        FAKE.block_download = False
        status, _ = self.call("POST", f"/v1/jobs/{job['id']}/resume", {})
        self.assertEqual(status, 202)
        self.assertEqual(self.wait(job["id"], "done", "stalled")["state"], "done")
        self.assertEqual(len(FAKE.creates), 1)

    def test_missing_key_reports_clearly(self):
        self.stop()
        env = {name: value for name, value in self.env.items() if name != "KINGCONG_API_KEY"}
        self.start(env)
        self.assertFalse(self.call("GET", "/health")[1]["key_configured"])
        status, value = self.call("GET", "/v1/credits")
        self.assertEqual((status, value["error"]["code"]), (503, "no_api_key"))
        _, job = self.call("POST", "/v1/speech", {"text": TEXT})
        self.assertIn("API key", self.wait(job["id"], "failed")["error"])
        self.assertEqual(FAKE.creates, [])

    def test_proxy_passes_through(self):
        status, value = self.call("GET", "/v1/credits")
        self.assertEqual((status, value["data"]["credits"]), (200, 250000))

    def test_cli_say_writes_output_files(self):
        out = Path(self.tmp.name) / "ra" / "giong.mp3"
        result = subprocess.run([sys.executable, "-I", str(BIN), "say", TEXT, "--out", str(out), "--srt"],
                                env=self.env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(out.read_bytes(), b"ID3-audio")
        self.assertIn(b"chao", out.with_suffix(".srt").read_bytes())


if __name__ == "__main__":
    unittest.main()
