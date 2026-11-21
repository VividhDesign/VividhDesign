"""Command line: ``pramaan sync | mine | check | serve``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__


def _corpus(args):
    from .corpus import Corpus

    return Corpus(Path(args.db) if args.db else None)


def cmd_sync(args) -> int:
    from .corpus import sync

    sync(Path(args.db) if args.db else None)
    return 0


def cmd_mine(args) -> int:
    from itertools import chain

    from .mine import iter_hc_text_dir, iter_text_dir, mine, save

    corpus = _corpus(args)
    years = None
    if args.years:
        lo, _, hi = args.years.partition("-")
        years = range(int(lo), int(hi or lo) + 1)
    texts = list(iter_text_dir(Path(args.text_dir), years))
    through = max((int(p.split("_")[0]) for p, _ in texts if p.split("_")[0].isdigit()), default=None)
    stream = chain(texts, iter_hc_text_dir(Path(args.hc_dir))) if args.hc_dir else texts
    rows = mine(stream, corpus, workers=args.workers)
    save(rows, corpus.db_path, through=through)
    return 0


def cmd_check(args) -> int:
    from .documents import read_document
    from .quotes import TextSource
    from .report import to_html, to_json, to_terminal
    from .verify import Verifier, check_text

    if args.file == "-":
        text, name = sys.stdin.read(), "stdin"
    else:
        p = Path(args.file)
        text, name = read_document(p), p.name
    v = Verifier(_corpus(args), TextSource(allow_network=not args.offline), check_quotes=not args.no_quotes)
    findings = check_text(text, v, uncited=not args.cited_only)
    if args.json:
        print(to_json(findings, name))
    else:
        print(to_terminal(findings, show_ok=not args.problems_only))
    if args.html:
        Path(args.html).write_text(to_html(findings, name))
        print(f"\nHTML report written to {args.html}", file=sys.stderr)
    return 1 if any(f.risk == "high" for f in findings) else 0


def cmd_serve(args) -> int:
    from .server import serve

    serve(_corpus(args), host=args.host, port=args.port)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pramaan", description="Catch fake and wrong case citations in Indian legal documents.")
    ap.add_argument("--version", action="version", version=f"pramaan {__version__}")
    ap.add_argument("--db", help="judgment index (default: $PRAMAAN_DB or ~/.cache/pramaan/sc.sqlite)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sync", help="download Supreme Court metadata and build the index")
    s.set_defaults(fn=cmd_sync)

    m = sub.add_parser("mine", help="mine citation attestations from a directory of judgment texts")
    m.add_argument("text_dir")
    m.add_argument("--years", help="e.g. 2010-2022")
    m.add_argument("--hc-dir", help="also mine High Court judgment texts from this directory")
    m.add_argument("--workers", type=int, default=1)
    m.set_defaults(fn=cmd_mine)

    c = sub.add_parser("check", help="check every citation in a document (.txt .md .pdf .docx, or - for stdin)")
    c.add_argument("file")
    c.add_argument("--json", action="store_true", help="print JSON instead of a readable report")
    c.add_argument("--html", metavar="OUT", help="also write a self-contained HTML report")
    c.add_argument("--no-quotes", action="store_true", help="skip checking quoted passages")
    c.add_argument("--offline", action="store_true", help="never download judgment text")
    c.add_argument("--cited-only", action="store_true", help="ignore case names that carry no reporter citation")
    c.add_argument("--problems-only", action="store_true", help="hide verified citations")
    c.set_defaults(fn=cmd_check)

    v = sub.add_parser("serve", help="run the web interface")
    v.add_argument("--host", default="127.0.0.1")
    v.add_argument("--port", type=int, default=8000)
    v.set_defaults(fn=cmd_serve)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
