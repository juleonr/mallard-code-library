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
import math
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
        if not key or key in out:
            raise ValueError(f"empty or duplicate harness key: {key!r}")
        try:
            out[key] = float(value)
        except ValueError:
            out[key] = value
        if isinstance(out[key], float) and not math.isfinite(out[key]):
            raise ValueError(f"non-finite harness result: {key}")
    if not out:
        raise ValueError("harness block is empty")
    return out


def compare(results: dict, expected: dict) -> list:
    """Return a list of findings. Empty means both claims hold.

    FIELDS ARE DERIVED, NEVER ENUMERATED. An earlier version of this function hardcoded
    exposure_log_or, covariate_beta and exposure_se. The second entry added to this library
    reports exposure_log_rr, which matched none of them, so the harness compared NOTHING for the
    primary estimate and would have reported both claims as holding. A check that quietly asserts
    its own scope is the exact failure this library was built to catch, committed inside the
    checker. Agreement now covers every numeric key two engines both emitted; recovery covers
    every numeric key `truth` states, whatever any of them happen to be called.
    """
    findings = []
    langs = sorted(results)

    def numeric(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def tolerance(value, name):
        try:
            result = float(value)
            if isinstance(value, bool) or not math.isfinite(result) or result < 0:
                raise ValueError()
            return result
        except (TypeError, ValueError):
            findings.append(f"invalid tolerance {name}: must be finite and nonnegative")
            return 0.0

    if not langs:
        return ["no executed implementation produced output at all"]
    if len(langs) == 1:
        # Not a failure, but it must be said: with one engine there is no agreement claim to make,
        # and reporting a pass here would overstate what ran.
        findings.append(
            f"NOTE only one engine executed ({langs[0]}); the agreement claim was not tested")

    agree = expected.get("agreement", {})
    tol_est = tolerance(agree.get("tolerance_estimate", 1e-6), "agreement.tolerance_estimate")
    tol_se = tolerance(agree.get("tolerance_se", 1e-5), "agreement.tolerance_se")
    # PER-KEY AGREEMENT TOLERANCES, for the case where two engines implement a quantity that is
    # not uniquely defined. gee-working-correlation-robust-se is it: geepack and statsmodels
    # estimate the exchangeable working correlation with their own moment estimators, and the
    # model-based variance is computed FROM that correlation, so it inherits the difference.
    # Loosening a key here is an admission that has to be argued in expected.json, not a way of
    # making a disagreement go away -- which is why an unused key is reported below.
    agree_by_key = agree.get("tolerance_by_key", {})
    if not isinstance(agree_by_key, dict):
        findings.append("agreement.tolerance_by_key is not an object; it was ignored")
        agree_by_key = {}

    # --- agreement: every numeric key at least two engines both reported ---
    keys = sorted({k for l in langs for k, v in results[l].items() if numeric(v)})
    compared = 0
    for field in keys:
        present = {l: results[l][field] for l in langs
                   if numeric(results[l].get(field))}
        for lang in langs:
            if lang not in present:
                findings.append(f"missing numeric output {field!r} in {lang}; every engine must emit the same numeric keys")
            elif not math.isfinite(present[lang]):
                findings.append(f"non-finite output {field!r} in {lang}")
        if len(present) < 2:
            continue
        compared += 1
        tol = tolerance(agree_by_key.get(
            field, tol_se if field.endswith("_se") else tol_est), f"agreement.{field}")
        lo, hi = min(present.values()), max(present.values())
        if abs(hi - lo) > tol:
            spread = ", ".join(f"{l}={v:.10f}" for l, v in sorted(present.items()))
            findings.append(
                f"AGREEMENT {field}: spread {abs(hi - lo):.3e} exceeds {tol:.0e} -- {spread}. "
                f"On identical rows this is a package default, not rounding.")
    # A LOOSENED KEY NO ENGINE EMITS constrains nothing and reads like a check that passed --
    # the same shape as the recovery guard below and as this function's own hardcoded-field bug.
    emitted = {k for l in langs for k in results[l]}
    for named in sorted(set(agree_by_key) - emitted):
        findings.append(
            f"agreement.tolerance_by_key names {named!r}, which no engine emitted; "
            f"it constrains nothing and is probably a typo")
    if len(langs) >= 2 and compared == 0:
        findings.append(
            "two engines ran but shared NO field, so the agreement claim covered nothing. "
            "Every implementation of an entry must emit the same harness keys.")

    # --- recovery: every numeric key the fixture states a truth for ---
    truth = expected.get("truth", {})
    recovery = expected.get("recovery", {})
    rec_tol = tolerance(recovery.get("tolerance_estimate", 0.5), "recovery.tolerance_estimate")
    # PER-KEY TOLERANCES, because one number cannot serve two parameters measured on different
    # scales. mixed-effects-logistic-clustered is the case: with exposure allocated at the cluster
    # level its conditional log odds ratio needs a tolerance of 0.90 to cover the real sampling
    # distribution, and applying that same 0.90 to the between-cluster SD -- whose whole miss
    # distribution tops out at 0.40 -- would make that check pass whatever it was handed.
    by_key = recovery.get("tolerance_by_key", {})
    if not isinstance(by_key, dict):
        findings.append("recovery.tolerance_by_key is not an object; it was ignored")
        by_key = {}
    # A KEY THAT MATCHES NOTHING IS NAMED. A typo here would silently apply no tolerance at all
    # and read exactly like a check that passed -- the same shape as the hardcoded field names
    # this function's docstring records.
    for named in sorted(set(by_key) - set(truth)):
        findings.append(
            f"recovery.tolerance_by_key names {named!r}, which truth does not; "
            f"it constrains nothing and is probably a typo")
    for field, want_raw in truth.items():
        if isinstance(want_raw, bool) or not isinstance(want_raw, (int, float)):
            continue
        if not math.isfinite(want_raw):
            findings.append(f"non-finite truth {field!r}")
        seen_in = [l for l in langs if numeric(results[l].get(field))]
        if not seen_in:
            # A truth key no engine reports is either a derived convenience value (an odds ratio
            # printed beside the log odds ratio) or a typo. Named either way: a silently skipped
            # check and a passing one look identical from outside.
            findings.append(f"truth names {field!r} but no engine reported it; recovery was not checked")
            continue
        tol = tolerance(by_key.get(field, rec_tol), f"recovery.{field}")
        for lang in seen_in:
            got, want = results[lang][field], float(want_raw)
            if abs(got - want) > tol:
                findings.append(
                    f"RECOVERY {field} in {lang}: got {got:.6f}, fixture used {want:.6f}, "
                    f"off by {abs(got - want):.6f} > {tol}. The model fitted may not be the "
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

    # A MACHINE-READABLE ROLLUP LINE, so CI can report which entries actually tested which claim.
    # A single-engine entry passes, correctly, but its guarantee is weaker than a two-engine one
    # and nothing downstream could see that from an exit code alone.
    agreement = "tested" if len(results) >= 2 else "UNTESTED"
    real_findings = [f for f in findings if not f.startswith("NOTE")]
    print(f"SUMMARY|{entry.name}|{','.join(sorted(results)) or 'none'}|{agreement}|"
          f"{'FAIL' if real_findings else 'pass'}")

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
