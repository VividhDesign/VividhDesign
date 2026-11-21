# Pramaan API

One endpoint checks every case citation in a document. Use it to check an AI-drafted petition before
your user files it, to screen incoming filings, or to build citation checks into a drafting tool.

* **Base URL:** your deployment. Self-host with `docker build -t pramaan . && docker run -p 8000:8000 pramaan`,
  or ask for a hosted key.
* **Auth:** `Authorization: Bearer <key>` (or `X-API-Key: <key>`). Without a key, a small daily
  allowance per IP applies.
* **Limits:** each key has a daily request limit. The `X-RateLimit-Remaining` header shows what is left.
  Documents up to 15 MB.

## `POST /api/check`

Send either text:

```bash
curl -s https://YOUR-HOST/api/check \
  -H "Authorization: Bearer $PRAMAAN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Reliance is placed on Sarbjit Singh v. Union Bank of India, (2022) 7 SCC 464."}'
```

or a file (PDF, DOCX or TXT), base64-encoded:

```bash
curl -s https://YOUR-HOST/api/check \
  -H "Authorization: Bearer $PRAMAAN_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"filename\": \"petition.pdf\", \"data_b64\": \"$(base64 -w0 petition.pdf)\"}"
```

Optional field: `"uncited": false` ignores case names that carry no reporter citation.

### Response

```json
{
  "summary": {"total": 1, "high": 1, "review": 0, "ok": 0, "skipped": 0},
  "findings": [
    {
      "reference": "Sarbjit Singh v. Union Bank of India, (2022) 7 SCC 464",
      "case_name": "Sarbjit Singh v. Union Bank of India",
      "citations": ["(2022) 7 SCC 464"],
      "span": [17, 75],
      "status": "NOT_FOUND",
      "headline": "No such Supreme Court judgment found",
      "risk": "high",
      "message": "No Supreme Court judgment with these parties was found, ...",
      "match": null,
      "suggestions": [],
      "quotes": []
    }
  ],
  "text": "…the document text that was checked…"
}
```

| Field | Meaning |
|---|---|
| `risk` | `high`: open evidence contradicts the citation. `review`: could not be confirmed. `ok`: verified. `skip`: not a Supreme Court citation. |
| `status` | `VERIFIED`, `CASE_FOUND`, `WRONG_CITATION`, `YEAR_MISMATCH`, `NOT_FOUND`, `QUOTE_NOT_FOUND`, `QUOTE_PARTIAL`, `UNVERIFIED`, `OUT_OF_SCOPE` |
| `span` | Character offsets of the reference in `text`, for highlighting. |
| `match` | The judgment the citation was matched to (title, date, SCR and neutral citations, PDF link), when there is one. |
| `quotes` | For each quoted passage: `status` (`FOUND`, `PARTIAL`, `NOT_FOUND`, `UNCHECKED`) and `score`, the share of its phrasing found in the judgment. |

**Suggested handling in a drafting product:**
* **Block or warn** on `high`.
* **Show** `review` items to the user with the message.
* **Never** silently rewrite a citation.

## Other endpoints

* `GET /api/info`: index size and coverage.
* `GET /healthz`: liveness check.

## Errors

| Code | Meaning |
|---|---|
| 400 | The document could not be read. |
| 401 | Invalid API key. |
| 413 | Document too large. |
| 429 | Daily limit reached. |

## Operating a hosted instance

```bash
docker run -p 8000:8000 \
  -e PRAMAAN_API_KEYS="acme:5000,lawfirm-x:500" \
  -e PRAMAAN_FREE_PER_DAY=30 \
  -e PRAMAAN_USAGE_LOG=/data/usage.jsonl -v /srv/pramaan:/data \
  pramaan
```

* The usage log has one line per keyed request (key, time, citations, high-risk count), enough for
  monthly invoices.
* Document text is never written to disk.
* Rebuild the image weekly to pick up new judgments.
