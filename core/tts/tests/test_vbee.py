"""Kiểm tra provider Vbee của bin/tts với máy chủ Vbee giả và bộ căn phụ đề giả, không tốn credit."""
import json
import base64
import os
import socket
import stat
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
APP_ID = "app-1234-abcd"
# Token tổng hợp cho server giả; không phải credential thực.
TOKEN = '.'.join(base64.urlsafe_b64encode(x).decode().rstrip('=') for x in (b'{"alg":"HS256"}', b'{"sub":"test"}', b'synthetic-signature'))
TEXT = "Từ ngày một tháng bảy, hộ kinh doanh phải xuất hóa đơn điện tử."
# Bộ căn giả: chép văn bản vào SRT để kiểm tra service truyền đúng text.
ALIGN_STUB = """#!/bin/sh
while [ $# -gt 0 ]; do
  case "$1" in --text) TEXT="$2"; shift;; --out) OUT="$2"; shift;; esac
  shift
done
printf '1\\n00:00:00,000 --> 00:00:01,000\\n' > "$OUT"
cat "$TEXT" >> "$OUT"
"""


class Fake:
    def reset(self):
        self.creates, self.polls, self.final = [], 0, "COMPLETED"


FAKE = Fake()
FAKE.reset()


class Upstream(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, value, raw=None):
        body = raw if raw is not None else json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        if self.headers.get("Authorization") != f"Bearer {TOKEN}" or self.headers.get("App-Id") != APP_ID:
            self.send(401, {"error": {"code": "UNAUTHORIZED", "message": "Invalid token"}})
            return False
        return True

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FAKE.creates.append(body)
        if self.authorized():
            self.send(200, {"requestId": f"req-{len(FAKE.creates)}", "status": "PROCESSING"})

    def do_GET(self):
        if self.path.startswith("/files/"):
            self.send(200, None, raw=b"ID3-vbee")
            return
        if not self.authorized():
            return
        if self.path.startswith("/v1/tts/requests/"):
            FAKE.polls += 1
            if FAKE.polls < 2:
                self.send(200, {"requestId": "x", "status": "PROCESSING"})
            elif FAKE.final == "FAILED":
                self.send(200, {"requestId": "x", "status": "FAILED", "error_message": "giọng lỗi"})
            else:
                link = f"http://127.0.0.1:{self.server.server_port}/files/v.mp3"
                self.send(200, {"requestId": "x", "status": "COMPLETED", "audioLink": link})
        elif self.path.startswith("/voices"):
            self.send(200, {"status": 1, "result": {"pagination": {"has_next_page": False}, "voices": [
                {"code": "hn_female_ngochuyen_full_48k-fhg", "name": "HN - Ngọc Huyền"},
                {"code": "sg_male_trungkien_vdts_48k-fhg", "name": "SG - Trung Kiên"}]}})
        else:
            self.send(404, {})


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class VbeeCase(unittest.TestCase):
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
        stub = Path(self.tmp.name) / "align-python"
        stub.write_text(ALIGN_STUB)
        stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
        base = f"http://127.0.0.1:{self.upstream.server_port}"
        self.port = free_port()
        self.env = {
            **os.environ, "TTS_ENV_FILE": "/nonexistent", "TTS_PORT": str(self.port), "TTS_DATA_DIR": self.tmp.name + "/data",
            "VBEE_APP_ID": APP_ID, "VBEE_TOKEN": TOKEN, "VBEE_BASE_URL": base, "VBEE_VOICES_URL": base + "/voices",
            "KINGCONG_BASE_URL": base,  # cho phép tải file http từ máy chủ giả
            "TTS_ALIGN_PYTHON": str(stub), "TTS_POLL_INTERVAL": "0.02", "TTS_POLL_TIMEOUT": "2",
            "TTS_KEYCHAIN_SERVICE": "bizbank-test-absent-" + Path(self.tmp.name).name, "TTS_VBEE_KEYCHAIN_SERVICE": "bizbank-test-absent-" + Path(self.tmp.name).name,
        }
        self.start()
        self.addCleanup(self.stop)

    def start(self, env=None):
        self.process = subprocess.Popen([sys.executable, "-I", str(BIN), "serve"], env=env or self.env,
                                        stderr=subprocess.DEVNULL)
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

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                raw = response.read()
                return response.status, (json.loads(raw) if raw[:1] == b"{" else raw)
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    def wait(self, job_id, *states):
        for _ in range(250):
            _, job = self.call("GET", f"/v1/jobs/{job_id}")
            if job["state"] in states:
                return job
            time.sleep(0.02)
        self.fail(f"Job không tới {states}: {job}")

    def test_speech_with_local_srt(self):
        status, job = self.call("POST", "/v1/speech", {"text": TEXT, "provider": "vbee", "export_srt": True,
                                                       "speed": 1.1, "project": "news-video"})
        self.assertEqual(status, 202)
        job = self.wait(job["id"], "done", "failed", "stalled", "uncertain")
        self.assertEqual(job["state"], "done", job["error"])
        self.assertIsNone(job["error"])
        sent = FAKE.creates[0]
        self.assertEqual((sent["voiceCode"], sent["mode"], sent["speed"]), ("hn_female_ngochuyen_full_48k-fhg", "async", 1.1))
        self.assertTrue(sent["webhookUrl"].startswith("https://") and ".invalid/" in sent["webhookUrl"])
        self.assertEqual(self.call("GET", job["audio_url"])[1], b"ID3-vbee")
        self.assertIn(TEXT.encode(), self.call("GET", job["srt_url"])[1])
        leftovers = [p.name for p in Path(self.env["TTS_DATA_DIR"], "media").iterdir() if "txt" in p.name]
        self.assertEqual(leftovers, [], "không được giữ text trên đĩa")

    def test_srt_added_later_without_second_charge(self):
        _, job = self.call("POST", "/v1/speech", {"text": TEXT, "provider": "vbee"})
        job = self.wait(job["id"], "done", "failed")
        self.assertIsNone(job["srt_url"])
        status, again = self.call("POST", "/v1/speech", {"text": TEXT, "provider": "vbee", "export_srt": True})
        self.assertEqual((status, again["id"], again["reused"]), (200, job["id"], True))
        again = self.wait(job["id"], "done")
        while not again["srt_url"]:
            again = self.wait(job["id"], "done")
        self.assertEqual(len(FAKE.creates), 1)

    def test_pauses_map_to_client_pause(self):
        _, job = self.call("POST", "/v1/speech", {"text": TEXT, "provider": "vbee",
                                                  "pauses": {"sentence": 0.1, "paragraph": 0}})
        self.wait(job["id"], "done")
        self.assertEqual(FAKE.creates[0]["clientPause"], {"paragraphBreak": 0.0, "sentenceBreak": 0.1})
        status, again = self.call("POST", "/v1/speech", {"text": TEXT, "provider": "vbee"})
        self.assertEqual(status, 202, "khác pauses là yêu cầu khác")
        for bad in ({"sentence": 0.01}, {"lạ": 1}, "0.1"):
            status, value = self.call("POST", "/v1/speech", {"text": TEXT, "provider": "vbee", "pauses": bad})
            self.assertEqual(status, 400, bad)

    def test_rejects_unsupported_settings(self):
        for body in ({"pitch": 1.2}, {"vol": 0.5}, {"speed": 2.0}, {"stability": 0.5}, {"model_id": "x"}):
            status, value = self.call("POST", "/v1/speech", {"text": TEXT, "provider": "vbee", **body})
            self.assertEqual((status, value["error"]["code"]), (400, "invalid_request"), body)
        self.assertEqual(FAKE.creates, [])

    def test_upstream_failure_and_bad_token(self):
        FAKE.final = "FAILED"
        _, job = self.call("POST", "/v1/speech", {"text": TEXT, "provider": "vbee"})
        self.assertIn("giọng lỗi", self.wait(job["id"], "failed")["error"])
        self.stop()
        self.start({**self.env, "VBEE_TOKEN": TOKEN + "x"})
        _, job = self.call("POST", "/v1/speech", {"text": TEXT + " ", "provider": "vbee"})
        self.assertIn("401", self.wait(job["id"], "failed")["error"])

    def test_missing_credentials(self):
        self.stop()
        self.start({name: value for name, value in self.env.items() if name != "VBEE_TOKEN"})
        self.assertFalse(self.call("GET", "/health")[1]["vbee_configured"])
        _, job = self.call("POST", "/v1/speech", {"text": TEXT, "provider": "vbee"})
        self.assertIn("tts key set --provider vbee", self.wait(job["id"], "failed")["error"])
        self.assertEqual(FAKE.creates, [])

    def test_voice_search(self):
        status, value = self.call("GET", "/v1/voices?provider=vbee&search=ng%E1%BB%8Dc")
        self.assertEqual(status, 200)
        self.assertEqual([v["code"] for v in value["voices"]], ["hn_female_ngochuyen_full_48k-fhg"])


if __name__ == "__main__":
    unittest.main()
