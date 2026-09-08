"""Seeded fixture for competing risks: the cumulative incidence function.

TWO CAUSES, drawn from independent exponential clocks. Whichever fires first is what the patient is
observed to have; administrative censoring at the horizon takes anyone still event-free. That is a
LATENT-FAILURE-TIME construction, and it is used here for one reason: with constant cause-specific
hazards h1 and h2, the cumulative incidence of cause 1 has a closed form,

    F1(t) = h1 / (h1 + h2) * (1 - exp(-(h1 + h2) * t))

so the truth this entry recovers is arithmetic rather than a recording of what the code produced.

WHY THIS ENTRY EXISTS AT ALL. A Kaplan-Meier curve for cause 1 treats a death from cause 2 as
CENSORING -- as though that patient could still go on to have cause 1, when they cannot. It
therefore OVERSTATES cumulative incidence, and the overstatement grows with the competing hazard.
The fixture is built so the gap is large enough to see rather than argue about: cause 2 is more
common than cause 1. Both estimators are computed in every file, side by side, because the number
that matters here is the difference between them.

    1 - KM(t) = 1 - exp(-h1 * t)          the wrong one, and it is the one a survival package
                                          gives you by default if you code the competing event
                                          as censored
    F1(t)     = the closed form above     the right one

Stdlib only.
"""

import csv
import math
import random
from pathlib import Path

SEED = 20260908
N = 1200
H1 = 0.030          # cause-specific hazard for the event of interest, per month
H2 = 0.055          # the COMPETING cause, deliberately the larger of the two
HORIZON = 36.0

# TIMES ARE NOT ROUNDED TO A GRID HERE, unlike the Kaplan-Meier entry, and the reason is a property
# of one of the engines rather than a statistical one: lifelines' AalenJohansenFitter does not
# support tied event times and adds jitter when it finds them, which would make the two engines
# disagree for a reason that has nothing to do with the estimator. This entry's subject is the gap
# between two ESTIMATORS, not tie handling, so the fixture avoids ties instead of testing them.
# The Kaplan-Meier entry does the opposite, deliberately, because there ties are the point.


def cif1(t, h1=H1, h2=H2):
    """The closed form. Not estimated from anything -- this is the model's own answer."""
    return h1 / (h1 + h2) * (1 - math.exp(-(h1 + h2) * t))


def naive_km_incidence(t, h1=H1):
    """What 1 - KM(t) converges to when the competing event is treated as censoring."""
    return 1 - math.exp(-h1 * t)


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    for i in range(1, N + 1):
        t1 = -math.log(1.0 - rng.random()) / H1
        t2 = -math.log(1.0 - rng.random()) / H2
        t = min(t1, t2)
        # 0 = still event-free at the horizon, 1 = the event of interest, 2 = the competing event.
        status = 0 if t > HORIZON else (1 if t1 <= t2 else 2)
        obs = min(t, HORIZON)
        rows.append({"id": i, "time": round(obs, 8), "status": status})

    out = Path(__file__).with_name("fixture.csv")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "time", "status"])
        w.writeheader()
        w.writerows(rows)

    counts = {s: sum(1 for r in rows if r["status"] == s) for s in (0, 1, 2)}
    ev = [r["time"] for r in rows if r["status"] in (1, 2)]
    ties = len(ev) - len(set(ev))
    assert ties == 0, f"{ties} tied event times, which lifelines would jitter"
    print(f"wrote {out.name}: {len(rows)} rows")
    print(f"  cause 1 (of interest) {counts[1]}, cause 2 (competing) {counts[2]}, "
          f"censored at the horizon {counts[0]}")
    print(f"  THE COMPETING CAUSE IS THE MORE COMMON ONE, which is what makes the gap visible.")
    for t in (12.0, 24.0, 36.0):
        print(f"  t={t:5.1f}   CIF1 {cif1(t):.6f}   1-KM {naive_km_incidence(t):.6f}   "
              f"the naive curve overstates by {naive_km_incidence(t) - cif1(t):.6f}")
    print("  A Kaplan-Meier curve for cause 1 censors the competing death, as though that patient")
    print("  could still go on to have cause 1. They cannot. That is the whole error.")


if __name__ == "__main__":
    main()
