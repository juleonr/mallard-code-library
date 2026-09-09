"""Seeded fixture for linear regression with heteroskedasticity-consistent standard errors.

The outcome is linear in the predictors BY CONSTRUCTION, so the coefficients below are the
parameters ordinary least squares estimates -- not those of a process that merely resembles one.
That is what makes the recovery claim meaningful.

THE ERROR VARIANCE IS NOT CONSTANT, AND THAT IS THE ENTIRE POINT OF THIS FIXTURE. The two arms
have different spread, which is ordinary in clinical data: a treatment that helps some patients a
great deal and others not at all widens the treated arm. Under constant variance a robust estimator
converges to the classical one, so a homoskedastic fixture could not tell them apart at all and
pinning the option would be decoration.

Heteroskedasticity does NOT bias the coefficients. It makes the classical standard error wrong,
which is why this entry reports both: the point estimates recover the truth under either variance,
and only the inference differs. A reader who takes the classical interval here is not reading a
biased estimate, they are reading an interval with the wrong width.

Stdlib only.
"""

import csv
import random
from pathlib import Path

SEED = 20260908
N = 1200
BETA_INTERCEPT = 2.0
BETA_EXPOSURE = 0.8
BETA_COVARIATE = -0.5

# sd(eps | exposed). The exposed arm is more than three times as variable. Nothing else drives the
# variance, so the heteroskedasticity here is the plainest clinical kind: two arms, two spreads.
SD_BASE = 0.5
SD_EXPOSED_EXTRA = 1.2

# A HEAVY-TAILED COVARIATE WAS TRIED HERE AND REMOVED, which is worth recording because the
# reasoning for adding it sounded right. HC3 differs from HC0 only through LEVERAGE, so a mixture
# covariate (94% standard normal, 6% at four times the spread) was used to create some. Measured,
# it moved the exposure's HC0-to-HC3 gap from 2.31e-4 to 2.14e-4 -- that is, not at all, because
# the exposure is a BINARY column whose leverage barely depends on another covariate's tail. It
# cost a covariate estimate 2.7 robust standard errors from its true value. An intervention that
# does nothing for the thing it was aimed at and degrades something else is worth deleting rather
# than keeping because its rationale reads well.


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    for i in range(1, N + 1):
        exposed = 1 if rng.random() < 0.45 else 0
        covariate = rng.gauss(0.0, 1.0)
        eps = rng.gauss(0.0, SD_BASE + SD_EXPOSED_EXTRA * exposed)
        y = BETA_INTERCEPT + BETA_EXPOSURE * exposed + BETA_COVARIATE * covariate + eps
        rows.append({"id": i, "y": round(y, 6), "exposed": exposed,
                     "covariate": round(covariate, 6)})

    out = Path(__file__).with_name("fixture.csv")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "y", "exposed", "covariate"])
        w.writeheader()
        w.writerows(rows)

    n1 = sum(r["exposed"] for r in rows)
    print(f"wrote {out.name}: {len(rows)} rows, {n1} exposed, {len(rows) - n1} unexposed")

    # A crude check needing no model: the residual spread must actually differ by arm, or the
    # fixture does not exercise the option this entry pins.
    for arm in (0, 1):
        ys = [r["y"] for r in rows if r["exposed"] == arm]
        m = sum(ys) / len(ys)
        var = sum((v - m) ** 2 for v in ys) / (len(ys) - 1)
        print(f"  arm {arm}: n={len(ys):4d}  mean={m:+.4f}  sd={var ** 0.5:.4f}")
    print("  UNEQUAL SPREAD BY ARM is what makes a robust variance differ from the classical one.")


if __name__ == "__main__":
    main()
