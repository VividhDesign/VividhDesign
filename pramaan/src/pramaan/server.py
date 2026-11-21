"""Web interface and JSON API.

Standard library only. ``pramaan serve`` then open http://127.0.0.1:8000.

Self-hosted, it is open to anyone who can reach it. For a hosted service, set:

* ``PRAMAAN_API_KEYS="key1:5000,key2:500"``: API keys with daily request limits
  (a key without ``:limit`` gets 1000/day). Send as ``Authorization: Bearer key1``
  or ``X-API-Key: key1``.
* ``PRAMAAN_FREE_PER_DAY=30``: requests per day per IP address without a key (the
  web page uses this). Defaults to 30 when keys are set, unlimited otherwise.
* ``PRAMAAN_USAGE_LOG=/var/log/pramaan.jsonl``: one line per request (key, time,
  citations checked), for billing.
"""

from __future__ import annotations

import base64
import json
import os
import threading
import time
from collections import defaultdict
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from typing import Optional

from .corpus import SOURCE_NOTE, Corpus
from .documents import read_bytes
from .report import summary
from .verify import Verifier, check_text

MAX_BYTES = 15 * 1024 * 1024
DEFAULT_KEY_LIMIT = 1000


def parse_keys(spec: Optional[str]) -> dict[str, int]:
    keys = {}
    for item in (spec or "").split(","):
        item = item.strip()
        if not item:
            continue
        key, _, limit = item.partition(":")
        keys[key] = int(limit) if limit.isdigit() else DEFAULT_KEY_LIMIT
    return keys


class Quota:
    """Per-day request counters for API keys and for anonymous IP addresses."""

    def __init__(self, keys: dict[str, int], free_per_day: Optional[int], usage_log: Optional[str] = None):
        self.keys = keys
        self.free = free_per_day
        self.usage_log = usage_log
        self.day = date.today()
        self.used: dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()

    def take(self, api_key: Optional[str], ip: str) -> tuple[bool, Optional[int], str]:
        """Consume one request. Returns ``(allowed, remaining, who)``."""
        with self.lock:
            if date.today() != self.day:
                self.day, self.used = date.today(), defaultdict(int)
            if api_key is not None:
                if api_key not in self.keys:
                    return False, None, "invalid key"
                who, limit = f"key:{api_key}", self.keys[api_key]
            else:
                who, limit = f"ip:{ip}", self.free
            if limit is not None and self.used[who] >= limit:
                return False, 0, who
            self.used[who] += 1
            return True, (None if limit is None else limit - self.used[who]), who

    def log(self, who: str, n_citations: int, n_high: int) -> None:
        if not self.usage_log or not who.startswith("key:"):
            return
        line = json.dumps({"t": int(time.time()), "key": who[4:], "citations": n_citations, "high": n_high})
        with self.lock, open(self.usage_log, "a") as f:
            f.write(line + "\n")


def quota_from_env() -> Quota:
    keys = parse_keys(os.environ.get("PRAMAAN_API_KEYS"))
    free_env = os.environ.get("PRAMAAN_FREE_PER_DAY")
    free = int(free_env) if free_env and free_env.isdigit() else (30 if keys else None)
    return Quota(keys, free, os.environ.get("PRAMAAN_USAGE_LOG"))


def make_handler(verifier: Verifier, corpus: Corpus, quota: Optional[Quota] = None):
    index = resources.files("pramaan").joinpath("static/index.html").read_bytes()
    quota = quota or Quota({}, None)

    class Handler(BaseHTTPRequestHandler):
        server_version = "pramaan"

        def _send(self, code: int, body: bytes, ctype: str, extra: Optional[dict] = None) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj, extra: Optional[dict] = None) -> None:
            self._send(code, json.dumps(obj, ensure_ascii=False).encode(), "application/json", extra)

        def _api_key(self) -> Optional[str]:
            auth = self.headers.get("Authorization") or ""
            if auth.lower().startswith("bearer "):
                return auth[7:].strip()
            return self.headers.get("X-API-Key")

        def _ip(self) -> str:
            fwd = self.headers.get("X-Forwarded-For")
            return fwd.split(",")[0].strip() if fwd else self.client_address[0]

        def do_GET(self):  # noqa: N802
            if self.path in ("/", "/index.html"):
                return self._send(200, index, "text/html; charset=utf-8")
            if self.path == "/api/info":
                lo, hi = corpus.year_range
                return self._json(200, {"judgments": len(corpus), "years": [lo, hi],
                                        "attested_citations": len(corpus.attest), "source": SOURCE_NOTE})
            if self.path == "/healthz":
                return self._send(200, b"ok", "text/plain")
            self._send(404, b"not found", "text/plain")

        def do_POST(self):  # noqa: N802
            if self.path != "/api/check":
                return self._send(404, b"not found", "text/plain")
            allowed, remaining, who = quota.take(self._api_key(), self._ip())
            limit_hdr = {} if remaining is None else {"X-RateLimit-Remaining": str(remaining)}
            if not allowed:
                if who == "invalid key":
                    return self._json(401, {"error": "invalid API key"})
                return self._json(429, {"error": "daily limit reached; use an API key for more"}, limit_hdr)
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BYTES:
                return self._json(413, {"error": "document too large"})
            try:
                req = json.loads(self.rfile.read(n) or b"{}")
                if req.get("data_b64"):
                    text = read_bytes(req.get("filename") or "upload.txt", base64.b64decode(req["data_b64"]))
                else:
                    text = req.get("text") or ""
                findings = check_text(text, verifier, uncited=bool(req.get("uncited", True)))
            except Exception as e:  # report, don't crash the server
                return self._json(400, {"error": str(e)})
            s = summary(findings)
            quota.log(who, s["total"], s["high"])
            self._json(200, {"text": text, "summary": s, "findings": [f.as_dict() for f in findings]}, limit_hdr)

        def log_message(self, fmt, *args):
            pass

    return Handler


def serve(corpus: Corpus, host: str = "127.0.0.1", port: int = 8000) -> None:
    verifier = Verifier(corpus)
    quota = quota_from_env()
    httpd = ThreadingHTTPServer((host, port), make_handler(verifier, corpus, quota))
    mode = f"{len(quota.keys)} API keys, {quota.free} free requests/day per IP" if quota.keys else "open access"
    print(f"Pramaan: {len(corpus)} judgments indexed ({mode}). Open http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
