"""Loopback Flycraft server: static files + Isaac sensory ticks.

Run from anywhere: python3 builds/flycraft/server.py
Binds 127.0.0.1:8770. Host/Origin checks match the rest of claude-pokee.
"""
import json
import os
import re
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from claude_pokee import client  # noqa: E402
from claude_pokee.client import IsaacError  # noqa: E402

STATIC = Path(__file__).resolve().parent
PORT = int(os.environ.get("FLYCRAFT_PORT") or 8770)

SYSTEM = (
    "You are a Drosophila central-complex toy (MaleCNS-inspired), NOT an MMO paladin "
    "and NOT waiting on quests. Always pick an immediate action from what you see. "
    "Reply with ONE JSON object only:\n"
    '{"forward":0.0,"strafe":0.0,"turn":0.0,"fire":0,"talk":0,"dart":0,"feed":0,'
    '"note":"<=10 words, fly inner speech"}\n'
    "forward/strafe/turn in [-1,1]; fire/talk/dart/feed are 0 or 1.\n"
    "Rules: (1) HUNGRY: turn toward nearest peach (foodAng sign: negative=left) and walk to it, then feed=1. "
    "(2) If peach/sugar closer than ~2m, feed=1, forward near 0. "
    "(3) Only dart if a hog is under ~3m or hp is low — never abandon a close peach for a distant hog. "
    "(4) Never idle. Never wait for a quest. "
    "(5) talk=1 only if a beetle is within ~2m. "
    "(6) fire=1 only if a hog is in melee AND you are not feeding."
)

MOTOR_RE = re.compile(r"\{[^{}]*\}", re.S)


def parse_motor(text):
    if not text:
        return None
    m = MOTOR_RE.search(text)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except ValueError:
        return None
    def num(k, lo, hi):
        try:
            v = float(data.get(k, 0))
        except (TypeError, ValueError):
            v = 0.0
        return max(lo, min(hi, v))
    def bit(k):
        return 1 if num(k, 0, 1) >= 0.5 else 0
    note = data.get("note") or ""
    if not isinstance(note, str):
        note = str(note)
    return {
        "forward": num("forward", -1, 1),
        "strafe": num("strafe", -1, 1),
        "turn": num("turn", -1, 1),
        "fire": bit("fire"),
        "talk": bit("talk"),
        "dart": bit("dart"),
        "feed": bit("feed"),
        "note": note.strip()[:140],
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def log_message(self, fmt, *args):
        sys.stderr.write("[flycraft] " + (fmt % args) + "\n")

    def _json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _refuse(self):
        why = client.local_request_error(self.headers)
        if why:
            self.close_connection = True
            self._json(403, {"error": why})
            return True
        return False

    def do_GET(self):
        if self._refuse():
            return
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            try:
                cfg = client.load_config()
                self._json(200, {"ok": True, "model": cfg["model"], "isaac": True})
            except IsaacError as exc:
                self._json(500, {"ok": False, "error": str(exc)})
            return
        super().do_GET()

    def do_POST(self):
        if self._refuse():
            return
        parsed = urlparse(self.path)
        if parsed.path != "/tick":
            self._json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > 80_000:
            self._json(413, {"error": "payload too large"})
            return
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            self._json(400, {"error": "bad json"})
            return
        senses = payload.get("senses") or {}
        see = payload.get("see") or ""
        if not isinstance(see, str):
            see = str(see)
        see = see[:1200]
        user = (
            "Sensory packet (photoreceptors, odor L/R, hunger, loom — act now):\n"
            + json.dumps(senses, separators=(",", ":"))[:2000]
            + "\n\nWhat the fly sees:\n"
            + see
        )
        started = time.time()
        try:
            result = client.chat(
                [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": user},
                ],
                max_tokens=180,
                temperature=0.35,
                timeout=55,
                stream=False,
            )
        except IsaacError as exc:
            self._json(502, {"ok": False, "error": str(exc)})
            return
        except Exception as exc:  # noqa: BLE001
            self._json(500, {"ok": False, "error": type(exc).__name__ + ": " + str(exc)})
            return
        motor = parse_motor(result.get("text") or "")
        if motor is None:
            motor = {
                "forward": 0.65,
                "strafe": 0,
                "turn": 0.2,
                "fire": 0,
                "talk": 0,
                "dart": 0,
                "feed": 0,
                "note": "searching the plume",
            }
        ms = int((time.time() - started) * 1000)
        self._json(200, {
            "ok": True,
            "motor": motor,
            "note": motor.get("note") or "",
            "ms": ms,
            "raw": (result.get("text") or "")[:400],
        })

    def translate_path(self, path):
        path = unquote(urlparse(path).path)
        if path == "/":
            path = "/index.html"
        rel = path.lstrip("/")
        full = (STATIC / rel).resolve()
        if STATIC.resolve() not in full.parents and full != STATIC.resolve():
            return str(STATIC / "index.html")
        return str(full)


def main():
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("Flycraft + Isaac on http://127.0.0.1:{}/".format(PORT))
    httpd.serve_forever()


if __name__ == "__main__":
    main()
