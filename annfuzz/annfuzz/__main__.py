"""Run every property against every adapter: python -m annfuzz [library ...] [--property name ...]"""

import argparse
import json
import sys
import time
import traceback
import warnings

from .adapters import ALL, EXTRA
from .properties import PROPERTIES


def main(argv=None):
    p = argparse.ArgumentParser(prog="annfuzz")
    p.add_argument("libraries", nargs="*")
    p.add_argument("--property", action="append", default=[])
    p.add_argument("--metric", action="append", default=[])
    p.add_argument("--json", default=None)
    args = p.parse_args(argv)
    warnings.filterwarnings("ignore")
    results = []
    pool = ALL + [A for A in EXTRA if A.name in args.libraries]
    for A in pool:
        if args.libraries and A.name not in args.libraries:
            continue
        for metric in args.metric or ["l2", "cos", "ip"]:
            if not A.supports(metric):
                continue
            for prop in PROPERTIES:
                if args.property and prop.__name__ not in args.property:
                    continue
                t = time.time()
                try:
                    findings = prop(A, metric)
                except Exception as e:  # noqa: BLE001
                    findings = [f"CRASH {type(e).__name__}: {str(e)[:120]}"]
                    traceback.print_exc(limit=1, file=sys.stderr)
                status = "FIND" if findings else "ok"
                results.append({"library": A.name, "metric": metric, "property": prop.__name__,
                                "status": status, "findings": findings, "seconds": round(time.time() - t, 2)})
                print(f"[{status:4}] {A.name:12} {metric:3} {prop.__name__:28} {'; '.join(findings)[:300]}", flush=True)
    if args.json:
        with open(args.json, "w") as f:
            json.dump(results, f, indent=1)


if __name__ == "__main__":
    main()
