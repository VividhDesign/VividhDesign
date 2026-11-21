"""Minimal web interface: paste or upload a document, get every citation checked.

Standard library only. ``pramaan serve`` then open http://127.0.0.1:8000.
"""

from __future__ import annotations

import base64
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources

from .corpus import SOURCE_NOTE, Corpus
from .documents import read_bytes
from .report import summary
from .verify import Verifier, check_text

MAX_BYTES = 15 * 1024 * 1024


def make_handler(verifier: Verifier, corpus: Corpus):
    index = resources.files("pramaan").joinpath("static/index.html").read_bytes()

    class Handler(BaseHTTPRequestHandler):
        server_version = "pramaan"

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if self.path in ("/", "/index.html"):
                return self._send(200, index, "text/html; charset=utf-8")
            if self.path == "/api/info":
                lo, hi = corpus.year_range
                info = {"judgments": len(corpus), "years": [lo, hi], "attested_citations": len(corpus.attest),
                        "source": SOURCE_NOTE}
                return self._send(200, json.dumps(info).encode(), "application/json")
            self._send(404, b"not found", "text/plain")

        def do_POST(self):  # noqa: N802
            if self.path != "/api/check":
                return self._send(404, b"not found", "text/plain")
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BYTES:
                return self._send(413, b'{"error":"document too large"}', "application/json")
            try:
                req = json.loads(self.rfile.read(n) or b"{}")
                if req.get("data_b64"):
                    text = read_bytes(req.get("filename") or "upload.txt", base64.b64decode(req["data_b64"]))
                else:
                    text = req.get("text") or ""
                findings = check_text(text, verifier, uncited=bool(req.get("uncited", True)))
            except Exception as e:  # report, don't crash the server
                return self._send(400, json.dumps({"error": str(e)}).encode(), "application/json")
            body = {"text": text, "summary": summary(findings), "findings": [f.as_dict() for f in findings]}
            self._send(200, json.dumps(body, ensure_ascii=False).encode(), "application/json")

        def log_message(self, fmt, *args):
            pass

    return Handler


def serve(corpus: Corpus, host: str = "127.0.0.1", port: int = 8000) -> None:
    verifier = Verifier(corpus)
    httpd = ThreadingHTTPServer((host, port), make_handler(verifier, corpus))
    print(f"Pramaan: {len(corpus)} judgments indexed. Open http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
