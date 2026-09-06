"""Seeded fixture for diagnostic accuracy against a reference standard.

Disease status is drawn first, then the test result CONDITIONAL on it, with fixed sensitivity and
specificity. Those two numbers are therefore properties of the generator, not of any estimator: a
2x2 table read off this data estimates exactly the parameters used to build it.

Prevalence is set well away from 0.5 on purpose. Sensitivity and specificity do not depend on it,
so a fixture at 50% prevalence would let an implementation that quietly computed predictive values
instead still land near the truth. At 30% they separate clearly.

Stdlib only.
"""

import csv
import random
from pathlib import Path

SEED = 20260906
N = 2000
PREVALENCE = 0.30
SENSITIVITY = 0.85
SPECIFICITY = 0.90


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    for i in range(1, N + 1):
        disease = 1 if rng.random() < PREVALENCE else 0
        if disease:
            test = 1 if rng.random() < SENSITIVITY else 0
        else:
            test = 0 if rng.random() < SPECIFICITY else 1
        rows.append({"id": i, "disease": disease, "test": test})

    out = Path(__file__).with_name("fixture.csv")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "disease", "test"])
        w.writeheader()
        w.writerows(rows)

    tp = sum(1 for r in rows if r["disease"] == 1 and r["test"] == 1)
    fn = sum(1 for r in rows if r["disease"] == 1 and r["test"] == 0)
    tn = sum(1 for r in rows if r["disease"] == 0 and r["test"] == 0)
    fp = sum(1 for r in rows if r["disease"] == 0 and r["test"] == 1)
    print(f"wrote {out.name}: {len(rows)} rows")
    print(f"  2x2  TP={tp} FP={fp} FN={fn} TN={tn}")
    print(f"  observed sensitivity {tp/(tp+fn):.4f}  (true {SENSITIVITY})")
    print(f"  observed specificity {tn/(tn+fp):.4f}  (true {SPECIFICITY})")
    print(f"  observed prevalence  {(tp+fn)/len(rows):.4f}  (true {PREVALENCE})")


if __name__ == "__main__":
    main()
