"""Compare an entry's executed implementations against each other and against the truth.

Two independent claims, per expected.json:

  AGREEMENT  every executed language produced the same estimates on identical rows.
             Tight, because with the same data any real gap is a package default.

  RECOVERY   those estimates are close to the parameter the fixture actually used.
             Loose, because an estimate carries sampling error. It exists to catch
             implementations that agree with each other on the same wrong model.

Neither claim implies the other, and reporting one as if it were both is the failure mode this
whole library is built to avoid. Agreement alone passes four identical mistakes. Recovery alone
passes a default mismatch smaller than sampling error.

Stdlib only, so it runs anywhere -- including an environment with no scientific stack, which is
where it was written and tested.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

HARNESS_MARKER = "--- HARNESS ---"


def parse_harness_block(stdout: str) -> dict:
    """Pull key=value pairs from the block each implementation prints.

    Only lines AFTER the marker are read. An implementation that prints a summary table
    containing an equals sign earlier in its output must not have that parsed as a result,
    which is exactly the sort of thing that makes a check quietly wrong.
    """
    if HARNESS_MARKER not in stdout:
        raise ValueError(f"no {HARNESS_MARKER!r} block in output")
    tail = stdout.split(HARNESS_MARKER, 1)[1]
    out = {}
    for line in tail.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        try:
            out[key] = float(value)
        except ValueError:
            out[key] = value
    if not out:
        raise ValueError("harness block is empty")
    return out


def compare(results: dict, expected: dict) -> list:
    """Return a list of findings. Empty means both claims hold."""
    findings = []
    langs = sorted(results)

    if not langs:
        return ["no executed implementation produced output at all"]
    if len(langs) == 1:
        # Not a failure, but it must be said: with one engine there is no agreement claim to make,
        # and reporting a pass here would overstate what ran.
        findings.append(
            f"NOTE only one engine executed ({langs[0]}); the agreement claim was not tested")

    # --- agreement ---
    agree = expected.get("agreement", {})
    tol_lor = float(agree.get("tolerance_log_or", 1e-6))
    tol_se = float(agree.get("tolerance_se", 1e-5))
    fields = [("exposure_log_or", tol_lor), ("covariate_beta", tol_lor), ("exposure_se", tol_se)]

    for field, tol in fields:
        present = {l: results[l][field] for l in langs if field in results[l]}
        if len(present) < 2:
            continue
        lo, hi = min(present.values()), max(present.values())
        if abs(hi - lo) > tol:
            spread = ", ".join(f"{l}={v:.10f}" for l, v in sorted(present.items()))
            findings.append(
                f"AGREEMENT {field}: spread {abs(hi - lo):.3e} exceeds {tol:.0e} -- {spread}. "
                f"On identical rows this is a package default, not rounding.")

    # --- recovery ---
    truth = expected.get("truth", {})
    rec_tol = float(expected.get("recovery", {}).get("tolerance_log_or", 0.5))
    for field in ("exposure_log_or", "covariate_beta"):
        if field not in truth:
            continue
        for lang in langs:
            if field not in results[lang]:
                continue
            got, want = results[lang][field], float(truth[field])
            if abs(got - want) > rec_tol:
                findings.append(
                    f"RECOVERY {field} in {lang}: got {got:.6f}, fixture used {want:.6f}, "
                    f"off by {abs(got - want):.6f} > {rec_tol}. The model fitted may not be the "
                    f"model the fixture generated.")
    return findings


def fixture_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entry", required=True, help="directory of the library entry")
    ap.add_argument("--output", action="append", default=[], metavar="LANG=FILE",
                    help="a language's captured stdout, repeatable")
    args = ap.parse_args(argv)

    entry = Path(args.entry)
    expected = json.loads((entry / "expected.json").read_text())

    results = {}
    for spec in args.output:
        lang, _, file = spec.partition("=")
        try:
            results[lang] = parse_harness_block(Path(file).read_text())
        except (OSError, ValueError) as exc:
            print(f"FAIL {lang}: {exc}")
            return 1

    findings = compare(results, expected)

    fixture = entry / expected.get("fixture", "fixture.csv")
    print(f"entry:   {entry.name}")
    print(f"fixture: {fixture.name}  sha256 {fixture_digest(fixture)[:16]}")
    print(f"engines: {', '.join(sorted(results)) or 'none'}")

    real = [f for f in findings if not f.startswith("NOTE")]
    for f in findings:
        print(("  " if f.startswith("NOTE") else "  FAIL ") + f)
    if not real:
        # THE SUMMARY MAY NOT CLAIM MORE THAN WAS TESTED. With one engine there is no agreement
        # claim, and an earlier version of this printed "implementations agree" two lines under a
        # note saying the agreement claim was not tested. A check that overstates its own result is
        # the exact failure this library is built to catch, committed inside the checker.
        if len(results) >= 2:
            print("  both claims hold: implementations agree, and agree with the fixture's parameters")
        else:
            print("  recovery holds. AGREEMENT UNTESTED: it needs two executed engines.")
    return 1 if real else 0


if __name__ == "__main__":
    sys.exit(main())
