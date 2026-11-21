import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from pramaan.corpus import Corpus, build_db
from pramaan.server import Quota, make_handler, parse_keys
from pramaan.verify import Verifier

RECORDS = [
    dict(title="MANEKA GANDHI versus UNION OF INDIA", petitioner="MANEKA GANDHI", respondent="UNION OF INDIA",
         decision_date="25-01-1978", path="1978_2_621_776", nc_display="1978INSC16", year="1978"),
]


@pytest.fixture()
def server(tmp_path):
    db = tmp_path / "sc.sqlite"
    build_db(RECORDS, db)
    corpus = Corpus(db)
    log = tmp_path / "usage.jsonl"
    quota = Quota(parse_keys("paid:3"), free_per_day=1, usage_log=str(log))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Verifier(corpus), corpus, quota))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}", log
    httpd.shutdown()


def post(url, body, key=None):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(url + "/api/check", data=json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r), r.headers
    except urllib.error.HTTPError as e:
        return e.code, json.load(e), e.headers


def test_parse_keys():
    assert parse_keys("a:10, b") == {"a": 10, "b": 1000}
    assert parse_keys(None) == {}


def test_free_tier_then_limit(server):
    url, _ = server
    code, body, _ = post(url, {"text": "Maneka Gandhi v. Union of India, [1978] 2 SCR 621."})
    assert code == 200 and body["findings"][0]["status"] == "VERIFIED"
    code, body, _ = post(url, {"text": "x"})
    assert code == 429


def test_api_key_quota_and_usage_log(server):
    url, log = server
    for _ in range(3):
        code, body, headers = post(url, {"text": "Maneka Gandhi v. Union of India, [1978] 2 SCR 621."}, key="paid")
        assert code == 200
    assert headers["X-RateLimit-Remaining"] == "0"
    assert post(url, {"text": "x"}, key="paid")[0] == 429
    assert post(url, {"text": "x"}, key="wrong")[0] == 401
    lines = [json.loads(x) for x in log.read_text().splitlines()]
    assert len(lines) == 3 and lines[0]["key"] == "paid" and lines[0]["citations"] == 1


def test_page_and_health(server):
    url, _ = server
    assert b"Pramaan" in urllib.request.urlopen(url + "/").read()
    assert urllib.request.urlopen(url + "/healthz").read() == b"ok"
