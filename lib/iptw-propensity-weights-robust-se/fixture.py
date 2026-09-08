"""Seeded fixture for an ATE estimated by inverse-probability-of-treatment weighting.

THE TRUTH IS A POPULATION QUANTITY, DEFINED BEFORE ANY ESTIMATOR EXISTS.

Potential outcomes are drawn for every patient from

    P(Y(a) = 1 | L) = expit(b0 + b1*a + b2*L),   L ~ N(0, 1)

and treatment from P(A = 1 | L) = expit(a0 + a1*L), so L confounds and nothing else does. Only
Y(A) is written to the file; the counterfactual column is discarded, as it is in life.

The average treatment effect is then

    ATE = E_L[expit(b0 + b1 + b2 L)] - E_L[expit(b0 + b2 L)]

which is an integral against a standard normal, not a property of any fitting procedure. It is
evaluated below by 60-node Gauss-Hermite quadrature to about 1e-12, so `truth` is arithmetic. That
matters here more than usual: IPTW targets the ATE, matching without replacement targets the ATT,
and the two are different numbers on this data -- an entry whose truth came from one estimator
would be scoring the other for disagreeing.

THE FIXTURE IS BUILT SO CONFOUNDING IS LARGE AND POSITIVITY IS SAFE.

  CONFOUNDING IS LARGE. The crude risk difference is far from the ATE, so an analysis that ignores
  L, or weights incorrectly, lands somewhere visibly wrong rather than somewhere plausible. A
  fixture where adjustment barely moves the estimate cannot tell a correct weighting from none.

  POSITIVITY HOLDS WITH ROOM. a1 is chosen so the propensity score stays away from 0 and 1:
  MEASURED on the committed seed it spans [0.081, 0.935], and the largest weight implied by the
  TRUE propensity is 10.5 unstabilized, 5.30 stabilized.

  THOSE ARE NOT THE WEIGHTS THE ANALYSIS USES, and the difference is worth keeping straight. This
  generator knows the true propensity; the analysis files estimate it, and their largest stabilized
  weight is 4.47 on this seed -- reported as the harness key max_stabilized_weight. The generator
  prints what it knows and the analysis reports what it computed; quoting one as the other would
  misdescribe the fixture in whichever direction happened to flatter it. Extreme weights are a real problem in real data, but an entry whose fixture produced them
  would be testing an implementation's TRIMMING defaults rather than its weighting, and trimming is
  a separate decision that belongs to a separate entry. The generator asserts both bounds, so a
  future edit to a1 that quietly walks into the extreme-weight regime fails rather than passes.

  The cost of that choice is recorded rather than hidden: at a1 = 0.9 the confounding is larger
  (crude 0.288 against the true 0.146) and the largest weight is 23.5; at 0.65 the crude estimate is
  0.245, still overstating the effect by 68%, with a largest weight of 10.5. The weaker treatment
  model was taken because the entry is about weighting, not about surviving bad weights.

Stdlib only. statistics.NormalDist is not needed here; the quadrature nodes are computed the same
way the mixed-effects calibration does it, by Golub-Welsch on the Hermite Jacobi matrix.
"""

import csv
import math
import random
from pathlib import Path

SEED = 20260908
N = 4000

A0, A1 = 0.0, 0.65         # treatment model: P(A=1|L) = expit(A0 + A1*L)
B0, B1, B2 = -1.2, 0.8, 1.1   # outcome model on the LOGIT scale, for both potential outcomes


def expit(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


def hermite_nodes(n: int):
    """Gauss-Hermite nodes and weights for a standard normal, by Golub-Welsch."""
    d = [0.0] * n
    e = [math.sqrt(k / 2.0) for k in range(1, n)] + [0.0]
    z = [1.0] + [0.0] * (n - 1)
    for l in range(n):
        it = 0
        while True:
            m = l
            while m < n - 1:
                if abs(e[m]) <= 1e-16 * (abs(d[m]) + abs(d[m + 1])):
                    break
                m += 1
            if m == l:
                break
            it += 1
            if it > 60:
                raise RuntimeError("quadrature did not converge")
            g = (d[l + 1] - d[l]) / (2 * e[l])
            r = math.hypot(g, 1.0)
            g = d[m] - d[l] + e[l] / (g + (r if g >= 0 else -r))
            s = c = 1.0
            p = 0.0
            broke = False
            for i in range(m - 1, l - 1, -1):
                f = s * e[i]
                b = c * e[i]
                r = math.hypot(f, g)
                e[i + 1] = r
                if r == 0.0:
                    d[i + 1] -= p
                    e[m] = 0.0
                    broke = True
                    break
                s, c = f / r, g / r
                g = d[i + 1] - p
                r = (d[i] - g) * s + 2.0 * c * b
                p = s * r
                d[i + 1] = g + p
                g = c * r - b
                zf = z[i + 1]
                z[i + 1] = s * z[i] + c * zf
                z[i] = c * z[i] - s * zf
            d[l] -= p
            e[l] = g
            e[m] = 0.0
            if broke:
                continue
    idx = sorted(range(n), key=lambda i: d[i])
    return ([math.sqrt(2.0) * d[i] for i in idx],
            [z[i] ** 2 for i in idx])          # weights already sum to 1 for the normal


def true_ate() -> tuple:
    nodes, wts = hermite_nodes(60)
    tot = sum(wts)
    e1 = sum(w * expit(B0 + B1 + B2 * t) for t, w in zip(nodes, wts)) / tot
    e0 = sum(w * expit(B0 + B2 * t) for t, w in zip(nodes, wts)) / tot
    return e1 - e0, e1, e0


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    ps_lo, ps_hi = 1.0, 0.0
    for i in range(1, N + 1):
        L = rng.gauss(0.0, 1.0)
        ps = expit(A0 + A1 * L)
        ps_lo, ps_hi = min(ps_lo, ps), max(ps_hi, ps)
        a = 1 if rng.random() < ps else 0
        # Both potential outcomes are drawn; only the observed one is written out.
        y1 = 1 if rng.random() < expit(B0 + B1 + B2 * L) else 0
        y0 = 1 if rng.random() < expit(B0 + B2 * L) else 0
        rows.append({"id": i, "treated": a, "L": round(L, 6), "outcome": y1 if a else y0,
                     "ps": ps})   # kept for the generator's own checks; NOT written to the file

    wmax = max(1.0 / (r["ps"] if r["treated"] else 1.0 - r["ps"]) for r in rows)
    if not (0.05 < ps_lo and ps_hi < 0.96):
        raise SystemExit(f"propensity range [{ps_lo:.3f}, {ps_hi:.3f}] breaks the positivity margin "
                         f"this fixture is built to keep")
    if wmax > 15.0:
        raise SystemExit(f"largest weight {wmax:.1f} is in the extreme-weight regime this fixture "
                         f"deliberately stays out of; that is a trimming entry, not this one")

    out = Path(__file__).with_name("fixture.csv")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "treated", "L", "outcome"],
                           extrasaction="ignore")   # ps is the generator's, not the analyst's
        w.writeheader()
        w.writerows(rows)

    ate, e1, e0 = true_ate()
    n1 = sum(r["treated"] for r in rows)
    p1 = sum(r["outcome"] for r in rows if r["treated"] == 1) / n1
    p0 = sum(r["outcome"] for r in rows if r["treated"] == 0) / (len(rows) - n1)
    print(f"wrote {out.name}: {len(rows)} rows, {n1} treated ({100 * n1 / len(rows):.1f}%)")
    pt = n1 / len(rows)
    wstab = max((pt / r["ps"]) if r["treated"] else ((1 - pt) / (1 - r["ps"])) for r in rows)
    print(f"  propensity range [{ps_lo:.3f}, {ps_hi:.3f}]  (positivity margin held)")
    print(f"  largest weight: unstabilized {wmax:.1f}, stabilized {wstab:.2f}")
    print(f"  TRUE ATE (risk difference) {ate:.10f}   E[Y(1)]={e1:.6f}  E[Y(0)]={e0:.6f}")
    print(f"  CRUDE risk difference      {p1 - p0:.6f}   confounded by {abs(p1 - p0 - ate):.4f}")


if __name__ == "__main__":
    main()
