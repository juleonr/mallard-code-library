"""Controls for harness/check.py, the comparator that decides both claims for every entry.

IT HAD NONE UNTIL NOW, and its own docstring records why that matters: an earlier version
hardcoded exposure_log_or, covariate_beta and exposure_se, so the second entry -- which reports
exposure_log_rr -- had its primary estimate compared by NOTHING and would have been reported as
passing both claims. A comparator with no controls is the same shape as a `must_appear` block
nothing reads: a rule written down and never enforced.

Every control here is two-directional. A finding that cannot be made to fire, and cannot be made
to stay silent, says nothing about the entry it just passed.

Stdlib only, like the module it tests.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import compare, parse_harness_block  # noqa: E402

FAILED = []


def check(name, condition, detail=""):
    if condition:
        print(f"  ok    {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL  {name}" + (f"\n        {detail}" if detail else ""))


def fires(findings, fragment):
    return any(fragment in f for f in findings)


def main():
    print("parse_harness_block")

    # ONLY LINES AFTER THE MARKER ARE READ. An implementation that prints a summary table with an
    # equals sign in it must not have that parsed as a result.
    parsed = parse_harness_block(
        "beta = 9.9 in the printed summary\n--- HARNESS ---\nbeta=1.5\nlabel=exchangeable\n")
    check("a key=value line BEFORE the marker is not a result", parsed.get("beta") == 1.5)
    check("a non-numeric value survives as a string", parsed.get("label") == "exchangeable")

    for bad, why in [("no marker here\nbeta=1\n", "no marker"),
                     ("--- HARNESS ---\n\n", "empty block")]:
        try:
            parse_harness_block(bad)
            check(f"{why} raises", False, "it returned instead of raising")
        except ValueError:
            check(f"{why} raises", True)

    print("agreement")

    EXPECTED = {
        "truth": {"exposure_log_rr": 0.4},
        "agreement": {"tolerance_estimate": 1e-4, "tolerance_se": 1e-5},
        "recovery": {"tolerance_estimate": 0.2},
    }
    agree = {"r": {"exposure_log_rr": 0.40, "exposure_se": 0.10},
             "python": {"exposure_log_rr": 0.40, "exposure_se": 0.10}}
    check("two engines that agree produce no finding", compare(agree, EXPECTED) == [])

    # THE RECORDED REGRESSION. The field is named exposure_log_rr, which no enumerated list in an
    # earlier version of the comparator contained. If fields are enumerated rather than derived,
    # this disagreement is invisible and both claims are reported as holding.
    drift = {"r": {"exposure_log_rr": 0.40}, "python": {"exposure_log_rr": 0.55}}
    check("a disagreement on a field no list names IS caught",
          fires(compare(drift, EXPECTED), "AGREEMENT exposure_log_rr"), compare(drift, EXPECTED))

    # _se fields get the tighter tolerance, and the two are genuinely different numbers.
    se_drift = {"r": {"exposure_se": 0.100000}, "python": {"exposure_se": 0.100050}}
    est_same = {"r": {"exposure_beta": 0.100000}, "python": {"exposure_beta": 0.100050}}
    check("a 5e-5 gap on an _se field exceeds tolerance_se",
          fires(compare(se_drift, EXPECTED), "AGREEMENT exposure_se"))
    check("the same gap on an estimate does not exceed tolerance_estimate",
          not fires(compare(est_same, EXPECTED), "AGREEMENT exposure_beta"))

    # TWO ENGINES SHARING NO FIELD is the failure that looks most like success: nothing disagrees.
    disjoint = {"r": {"alpha": 1.0}, "python": {"beta": 1.0}}
    check("two engines sharing no field is reported, not silently passed",
          fires(compare(disjoint, EXPECTED), "shared NO field"))

    one = compare({"r": {"exposure_log_rr": 0.40}}, EXPECTED)
    check("one engine reports the agreement claim as untested",
          fires(one, "only one engine executed"))
    check("and one engine makes no agreement finding of its own",
          not any(f.startswith("AGREEMENT") for f in one))
    check("no engine at all is a finding", fires(compare({}, EXPECTED), "no executed implementation"))

    print("per-key agreement tolerances")

    LOOSE = {
        "truth": {},
        "agreement": {"tolerance_estimate": 1e-4, "tolerance_se": 1e-5,
                      "tolerance_by_key": {"alpha": 1e-3}},
        "recovery": {"tolerance_estimate": 0.2},
    }
    pair = {"r": {"alpha": 0.1849411436, "beta": 0.1849411436},
            "python": {"alpha": 0.1847036384, "beta": 0.1847036384}}
    out = compare(pair, LOOSE)
    # The SAME spread on two keys, one loosened and one not. A single tolerance could not produce
    # both answers, which is what makes this feature testable at all.
    check("the loosened key passes at its own tolerance", not fires(out, "AGREEMENT alpha"), out)
    check("the same spread on an unlisted key still fails", fires(out, "AGREEMENT beta"), out)
    check("a per-key agreement tolerance no engine emitted is named",
          fires(compare(pair, {**LOOSE, "agreement": {**LOOSE["agreement"],
                                                      "tolerance_by_key": {"alfa": 1e-3}}}),
                "no engine emitted"))
    check("and a correctly spelled one is not",
          not fires(out, "no engine emitted"))
    check("an agreement tolerance_by_key that is not an object is reported",
          fires(compare(pair, {**LOOSE, "agreement": {**LOOSE["agreement"],
                                                      "tolerance_by_key": "1e-3"}}),
                "agreement.tolerance_by_key is not an object"))
    # AND IT STILL REJECTS A REAL DIFFERENCE. Loosening alpha to 1e-3 must not admit the gap a
    # wrong working correlation produces, which on the real entry is 0.185 against 0.
    check("a loosened key still catches a structurally different answer",
          fires(compare({"r": {"alpha": 0.1849411436}, "python": {"alpha": 0.0}}, LOOSE),
                "AGREEMENT alpha"))

    print("recovery")

    off = {"r": {"exposure_log_rr": 0.9}, "python": {"exposure_log_rr": 0.9}}
    check("an estimate outside the recovery tolerance IS caught",
          fires(compare(off, EXPECTED), "RECOVERY exposure_log_rr"))
    near = {"r": {"exposure_log_rr": 0.55}, "python": {"exposure_log_rr": 0.55}}
    check("an estimate inside it is not", not fires(compare(near, EXPECTED), "RECOVERY"))

    # A TRUTH KEY NO ENGINE REPORTS IS NAMED. A skipped check and a passing one look identical
    # from outside, which is the whole reason this note exists.
    check("a truth key no engine reported is named as unchecked",
          fires(compare(agree, {**EXPECTED, "truth": {"exposure_log_rr": 0.4, "typo_key": 1.0}}),
                "truth names 'typo_key'"))

    print("per-key recovery tolerances")

    TWO = {
        "truth": {"conditional_log_or": 0.6931, "cluster_sd": 0.8},
        "agreement": {"tolerance_estimate": 1e-4, "tolerance_se": 1e-5},
        "recovery": {"tolerance_estimate": 0.90, "tolerance_by_key": {"cluster_sd": 0.45}},
    }
    # The log odds ratio is 0.75 off, inside its own 0.90; the SD is 0.60 off, outside its 0.45.
    # One tolerance could not have produced both answers, which is the point of the feature.
    got = {"r": {"conditional_log_or": 1.4431, "cluster_sd": 0.2}}
    out = compare(got, TWO)
    check("the loose key passes under its own tolerance",
          not fires(out, "RECOVERY conditional_log_or"), out)
    check("the tight key fails under its own tolerance",
          fires(out, "RECOVERY cluster_sd"), out)
    check("and the message quotes the tolerance that applied", fires(out, "> 0.45"), out)

    # SCOPE. A per-key tolerance naming a key truth does not have constrains nothing, and reads
    # exactly like a check that passed.
    typo = {**TWO, "recovery": {"tolerance_estimate": 0.9,
                                "tolerance_by_key": {"cluster_sdd": 0.45}}}
    check("a per-key tolerance matching no truth key is named",
          fires(compare(got, typo), "which truth does not"))
    check("and a correctly spelled one is not",
          not fires(compare(got, TWO), "which truth does not"))
    check("a tolerance_by_key that is not an object is reported rather than ignored in silence",
          fires(compare(got, {**TWO, "recovery": {"tolerance_estimate": 0.9,
                                                  "tolerance_by_key": [1, 2]}}),
                "is not an object"))

    print()
    if FAILED:
        print(f"{len(FAILED)} control(s) failed:")
        for name in FAILED:
            print(f"  - {name}")
        return 1
    print("all controls passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
