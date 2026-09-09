"""Seeded fixture for a MARGINAL log odds ratio estimated on clustered binary data.

THE TRUTH IS A MARGINAL PARAMETER, AND IT IS EXACT.

That is the whole design of this generator, and it is what separates this entry from
mixed-effects-logistic-clustered. A random-intercept generator gives a CONDITIONAL odds ratio, and
GEE targets the marginal one, which is attenuated toward the null by a factor nobody can write down
in closed form. An entry whose truth came from a random-intercept generator would be asking GEE to
recover a parameter it does not estimate, and the recovery claim would be measuring the attenuation
rather than the implementation.

So the outcome is drawn from the MARGINAL model directly:

    p_ij = expit(b0 + b1*exposed_ij + b2*x_ij)
    Y_ij = 1{ Z_ij < Phi^-1(p_ij) },  Z_ij = sqrt(rho)*U_j + sqrt(1-rho)*E_ij

with U_j and E_ij standard normal. Z_ij is then standard normal MARGINALLY whatever rho is, so
P(Y_ij = 1) = p_ij exactly, and b1 is the marginal log odds ratio by construction. The latent
correlation rho induces the within-cluster association without touching the marginal mean, which is
the one thing a random intercept cannot do.

Two further properties the fixture needs, both deliberate:

  EXPOSURE HAS A CLUSTER-LEVEL COMPONENT. Some clinics prescribe more than others. Without it the
  exposure contrast is essentially within-cluster and the naive-against-robust gap this entry exists
  to show is a rounding difference. MEASURED, on a WORKING-INDEPENDENCE fit -- the structure R,
  statsmodels and PROC GENMOD all default to -- the sandwich-to-model-based ratio for the exposure
  coefficient is 1.022 at CLUSTER_EXPOSURE_SD = 0.9. At 2.5 it is 1.785 on this seed and above 1.3
  on 98% of the 200 calibration seeds. Under an EXCHANGEABLE working correlation the same ratio is
  much smaller, because a model-based variance computed under the right structure already carries
  the correlation; README.md has both. Recorded rather than asserted, because the rationale for a
  smaller spread reads perfectly well and produces an entry that demonstrates nothing.

  CLUSTER SIZES VARY WIDELY (8 to 40). The two working correlations coincide exactly in one classic
  case -- equal cluster sizes with a purely CLUSTER-LEVEL covariate -- and this fixture is away from
  it on both counts, so the choice of structure reaches the estimate rather than only the standard
  error. MEASURED: geepack gives 0.5874 exchangeable against 0.5727 independence. The statement is
  put that way round on purpose: unequal sizes do not by themselves prove the estimates must differ,
  they remove the condition under which they must agree.

  Size is drawn independently of exposure and outcome. Cluster size that CARRIES information about
  the outcome makes the two working correlations target genuinely DIFFERENT estimands, which is real
  (Seaman and colleagues on informative cluster size) and is not the subject of this entry.

Stdlib only, so it runs anywhere. statistics.NormalDist supplies the inverse normal CDF.
"""

import csv
import math
import random
from pathlib import Path
from statistics import NormalDist

SEED = 20260908
N_CLUSTERS = 90
MIN_SIZE, MAX_SIZE = 8, 40

B0 = math.log(0.20 / 0.80)      # marginal baseline risk 20% at x = 0, unexposed
B_EXPOSURE = math.log(2.0)      # true MARGINAL odds ratio of exactly 2.0
B_COVARIATE = 0.30

RHO = 0.25                      # latent within-cluster correlation
CLUSTER_EXPOSURE_SD = 2.5       # how much clinics differ in how often they expose

NORM = NormalDist()


def expit(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    pid = 0
    for j in range(1, N_CLUSTERS + 1):
        size = rng.randint(MIN_SIZE, MAX_SIZE)
        u = rng.gauss(0.0, 1.0)                       # shared latent, drives within-cluster ties
        clinic_pref = rng.gauss(0.0, CLUSTER_EXPOSURE_SD)   # this clinic's prescribing tendency
        for _ in range(size):
            pid += 1
            exposed = 1 if rng.random() < expit(clinic_pref) else 0
            x = rng.gauss(0.0, 1.0)
            p = expit(B0 + B_EXPOSURE * exposed + B_COVARIATE * x)
            z = math.sqrt(RHO) * u + math.sqrt(1.0 - RHO) * rng.gauss(0.0, 1.0)
            y = 1 if z < NORM.inv_cdf(p) else 0
            rows.append({"id": pid, "clinic": j, "exposed": exposed,
                         "x": round(x, 6), "outcome": y})

    out = Path(__file__).with_name("fixture.csv")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "clinic", "exposed", "x", "outcome"])
        w.writeheader()
        w.writerows(rows)

    sizes = {}
    for r in rows:
        sizes[r["clinic"]] = sizes.get(r["clinic"], 0) + 1
    ev = sum(r["outcome"] for r in rows)
    n1 = sum(1 for r in rows if r["exposed"] == 1)
    r1 = sum(r["outcome"] for r in rows if r["exposed"] == 1) / n1
    r0 = sum(r["outcome"] for r in rows if r["exposed"] == 0) / (len(rows) - n1)
    crude = math.log((r1 / (1 - r1)) / (r0 / (1 - r0)))

    # The observed within-clinic correlation of the OUTCOME, which is not rho -- rho is on the
    # latent scale and the binary version is always smaller. Printed because the entry's readers
    # will look for an ICC and the two numbers are not the same one.
    gm = ev / len(rows)
    num = den = 0.0
    for j, n_j in sizes.items():
        ys = [r["outcome"] for r in rows if r["clinic"] == j]
        for a in range(len(ys)):
            for b in range(a + 1, len(ys)):
                num += (ys[a] - gm) * (ys[b] - gm)
                den += 1
    pair_cov = num / den
    icc_binary = pair_cov / (gm * (1 - gm))

    print(f"wrote {out.name}: {len(rows)} rows in {N_CLUSTERS} clinics "
          f"(sizes {min(sizes.values())}-{max(sizes.values())})")
    print(f"  events {ev} ({100 * ev / len(rows):.1f}%), exposed {n1} ({100 * n1 / len(rows):.1f}%)")
    print(f"  crude log OR {crude:.4f}   true MARGINAL log OR {B_EXPOSURE:.4f}")
    print(f"  latent rho {RHO}, observed binary within-clinic ICC {icc_binary:.4f}")


if __name__ == "__main__":
    main()
