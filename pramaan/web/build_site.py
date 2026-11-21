"""Build the static, in-browser site (for GitHub Pages or any static host).

    pramaan sync                       # builds the index
    python web/build_site.py --db ~/.cache/pramaan/sc.sqlite --out site

The site runs the Python package in the browser with Pyodide, so documents are
checked on the user's own machine. Output: index.html, the pramaan and pypdf
wheels, and the gzipped index (~5 MB).
"""

from __future__ import annotations

import argparse
import gzip
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js"

HEAD = """<meta name="description" content="Free, open-source checker that catches fake and wrong case citations in Indian legal documents. Runs in your browser; nothing is uploaded.">
<meta property="og:title" content="Pramaan: catch fake case citations before they reach a court">
<meta property="og:description" content="Checks every Supreme Court citation in a petition, brief or order against the open record of 38,000+ judgments. Free, open-source, private.">
<script src="{pyodide}"></script>
<script>
window.PRAMAAN_STATIC = true;
window.PRAMAAN_WHEELS = {wheels};
window.PRAMAAN_INDEX = "sc.sqlite.gz";
</script>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="index built by `pramaan sync`")
    ap.add_argument("--out", default="site")
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    with tempfile.TemporaryDirectory() as td:
        subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "-q", "-w", td, str(ROOT)], check=True)
        subprocess.run([sys.executable, "-m", "pip", "download", "--no-deps", "--only-binary", ":all:", "-q",
                        "-d", td, "pypdf>=4"], check=True)
        wheels = []
        for w in sorted(Path(td).glob("*.whl")):
            shutil.copy(w, out / w.name)
            wheels.append(w.name)

    with open(args.db, "rb") as src, gzip.open(out / "sc.sqlite.gz", "wb", compresslevel=9) as dst:
        shutil.copyfileobj(src, dst)

    page = (ROOT / "src" / "pramaan" / "static" / "index.html").read_text()
    head = HEAD.format(pyodide=PYODIDE, wheels="[" + ", ".join(f'"{w}"' for w in wheels) + "]")
    page = page.replace("</title>", "</title>\n" + head, 1)
    (out / "index.html").write_text(page)
    (out / ".nojekyll").write_text("")
    size = sum(p.stat().st_size for p in out.iterdir()) / 1e6
    print(f"Built {out}/ ({size:.1f} MB): {', '.join(sorted(p.name for p in out.iterdir()))}")


if __name__ == "__main__":
    main()
