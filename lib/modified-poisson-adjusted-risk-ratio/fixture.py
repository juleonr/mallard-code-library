"""Seeded fixture for an adjusted RISK RATIO from a binary outcome.

The outcome is generated from a LOG-LINK risk model, so the true risk ratio is exp(beta) exactly.
That matters: modified Poisson regression (Zou 2004) fits a log-link Poisson to binary data and
takes a robust variance, and it targets precisely the parameter this generator uses. The truth is
therefore a property of the data, not of any implementation of the analysis.

The intercept is chosen so the fitted probability stays well below 1 across the covariate range. A
log link does not constrain it, and a generator that quietly produced p > 1 would be constructing
data no risk model can represent.

Stdlib only, so it runs anywhere.
"""

import csv
import math
import random
from pathlib import Path

SEED = 20260906
N = 3000

BETA0 = math.log(0.10)      # baseline risk 10%
BETA_EXPOSURE = math.log(1.5)   # true RISK RATIO of exactly 1.5
BETA_COVARIATE = 0.2


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    max_p = 0.0
    for i in range(1, N + 1):
        exposed = 1 if rng.random() < 0.40 else 0
        covariate = rng.gauss(0.0, 1.0)
        p = math.exp(BETA0 + BETA_EXPOSURE * exposed + BETA_COVARIATE * covariate)
        max_p = max(max_p, p)
        if p >= 1.0:
            raise SystemExit(f"generator produced p={p:.3f}; a risk model cannot represent that")
        rows.append({"id": i, "exposed": exposed, "covariate": round(covariate, 6),
                     "outcome": 1 if rng.random() < p else 0})

    out = Path(__file__).with_name("fixture.csv")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "exposed", "covariate", "outcome"])
        w.writeheader()
        w.writerows(rows)

    ev = sum(r["outcome"] for r in rows)
    r1 = sum(r["outcome"] for r in rows if r["exposed"] == 1) / max(1, sum(1 for r in rows if r["exposed"] == 1))
    r0 = sum(r["outcome"] for r in rows if r["exposed"] == 0) / max(1, sum(1 for r in rows if r["exposed"] == 0))
    print(f"wrote {out.name}: {len(rows)} rows, {ev} events ({100*ev/len(rows):.1f}%)")
    print(f"  max fitted risk: {max_p:.3f}  (must stay under 1)")
    print(f"  crude risk ratio: {r1/r0:.4f}   true: {math.exp(BETA_EXPOSURE):.4f}")


if __name__ == "__main__":
    main()
