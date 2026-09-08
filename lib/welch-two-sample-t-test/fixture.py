"""Seeded fixture for a two-sample comparison of means with unequal variances.

The two arms are drawn from normal distributions with DIFFERENT STANDARD DEVIATIONS and
DIFFERENT SIZES, and the smaller arm is the more variable one. Both of those are deliberate.

WHY UNEQUAL VARIANCE. Under equal variance the pooled and Welch tests agree to within rounding,
so a fixture with equal spread cannot tell them apart and pinning the option would be decoration.

WHY THE SMALLER ARM IS THE MORE VARIABLE ONE. This is the direction that matters clinically. When
the smaller group has the larger variance the pooled test is ANTI-CONSERVATIVE: it reports a
standard error about a third too small and a p value too extreme, so it manufactures significance.
Reverse the two and the pooled test is merely conservative, which loses power but does not invent
findings. A fixture built the safe way round would exercise the same arithmetic and demonstrate the
harmless failure.

This shape is ordinary in clinical data: a small treated arm in which the drug helps some patients
a great deal and others not at all, against a large, stable control arm.

Stdlib only.
"""

import csv
import random
from pathlib import Path

SEED = 20260908
N_CONTROL = 1200
N_TREATED = 400
MEAN_CONTROL = 10.0
MEAN_TREATED = 11.0          # a true mean difference of exactly 1.0
SD_CONTROL = 2.0
SD_TREATED = 5.0             # the SMALLER arm, and 2.5 times as variable


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    i = 0
    for arm, n, mean, sd in ((0, N_CONTROL, MEAN_CONTROL, SD_CONTROL),
                             (1, N_TREATED, MEAN_TREATED, SD_TREATED)):
        for _ in range(n):
            i += 1
            rows.append({"id": i, "arm": arm, "y": round(rng.gauss(mean, sd), 6)})

    # Shuffled, so nothing depends on the file being ordered by arm. An implementation that reads
    # "the first 1200 rows" instead of the arm column fails visibly rather than by luck.
    rng.shuffle(rows)
    for k, r in enumerate(rows, start=1):
        r["id"] = k

    out = Path(__file__).with_name("fixture.csv")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "arm", "y"])
        w.writeheader()
        w.writerows(rows)

    print(f"wrote {out.name}: {len(rows)} rows")
    stats = {}
    for arm in (0, 1):
        ys = [r["y"] for r in rows if r["arm"] == arm]
        m = sum(ys) / len(ys)
        var = sum((v - m) ** 2 for v in ys) / (len(ys) - 1)
        stats[arm] = (len(ys), m, var)
        print(f"  arm {arm}: n={len(ys):4d}  mean={m:.6f}  sd={var ** 0.5:.6f}")

    (n0, m0, v0), (n1, m1, v1) = stats[0], stats[1]
    welch_se = (v1 / n1 + v0 / n0) ** 0.5
    pooled_var = ((n1 - 1) * v1 + (n0 - 1) * v0) / (n1 + n0 - 2)
    pooled_se = (pooled_var * (1 / n1 + 1 / n0)) ** 0.5
    print(f"  observed difference: {m1 - m0:.6f}   true difference: "
          f"{MEAN_TREATED - MEAN_CONTROL:.1f}")
    print(f"  Welch SE  {welch_se:.6f}")
    print(f"  pooled SE {pooled_se:.6f}   -- {100 * (1 - pooled_se / welch_se):.1f}% SMALLER, "
          f"which is the whole point of this fixture")


if __name__ == "__main__":
    main()
