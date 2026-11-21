# Contributing

Bug reports with a real citation that Pramaan gets wrong are the most useful contribution. Open an issue
with the citation exactly as written, what Pramaan said, and what is correct (with a link to the
judgment if possible). Each one becomes a test.

Good first areas:

* **Reporter formats** in `src/pramaan/citations.py`: add a pattern and a row to `tests/test_citations.py`.
* **Name abbreviations** (`ABBREVIATIONS` in `src/pramaan/names.py`): common forms like "MCGM" or "HUDA".
* **High Court coverage**: mining more of the open High Court dataset (`pramaan.mine.iter_hc_text_dir`).

Before sending a pull request:

```bash
pip install -e ".[dev]"
pytest -q
```

Changes that move the held-out numbers in the README must include the new `eval/results.json`, produced by
`python eval/evaluate.py` with an index whose attestations were mined only from judgments up to 2022.
