"""CLI: ``python -m axm certify SPEC.json [-o OUT.lean]``.

Exit codes (fail closed): 0 = certified, 2 = certificate failed (in subset but
the model can cross the threshold), 3 = refused (out of subset), 4 = malformed
spec. On ``certified`` with ``-o``, the kernel-checkable Lean artifact is written
to the given path; otherwise it is printed to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys

from .certify import SpecError, certify

_EXIT = {"certified": 0, "failed": 2, "refused": 3}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="axm", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("certify", help="certify a PK/PD model spec")
    c.add_argument("spec", help="path to a JSON model spec, or '-' for stdin")
    c.add_argument("-o", "--out", help="write emitted Lean here (else stdout)")
    c.add_argument("--lean-only", action="store_true",
                   help="on success print only the Lean, nothing else")
    args = p.parse_args(argv)

    raw = sys.stdin.read() if args.spec == "-" else open(args.spec).read()
    try:
        spec = json.loads(raw)
        outcome = certify(spec)
    except SpecError as e:
        print(f"malformed spec: {e}", file=sys.stderr)
        return 4
    except json.JSONDecodeError as e:
        print(f"malformed spec: not valid JSON: {e}", file=sys.stderr)
        return 4

    if outcome.ok and args.lean_only:
        sys.stdout.write(outcome.lean or "")
        return 0

    tag = outcome.status.upper()
    print(f"[{tag}] {outcome.detail.get('name', 'model')}: {outcome.reason}",
          file=sys.stderr)

    if outcome.ok:
        assert outcome.lean is not None
        if args.out:
            with open(args.out, "w") as f:
                f.write(outcome.lean)
            print(f"wrote kernel-checkable certificate to {args.out}",
                  file=sys.stderr)
        else:
            sys.stdout.write(outcome.lean)

    return _EXIT[outcome.status]


if __name__ == "__main__":
    raise SystemExit(main())
