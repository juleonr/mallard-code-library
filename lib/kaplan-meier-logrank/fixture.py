"""Seeded fixture for Kaplan-Meier estimation and the log-rank test.

Survival times are drawn from an EXPONENTIAL model whose hazard is baseline * exp(Xb), so the two
arms have proportional hazards by construction and the log-rank test -- which is the score test of
exactly that model -- is the test with the most power against this alternative. That matters: the
log-rank is not a general "are these curves different" test, and a fixture whose curves cross would
be testing it outside what it is for.

TWO PROPERTIES ARE DELIBERATE.

CENSORING IS HEAVY AND INDEPENDENT, from a competing uniform draw as well as the administrative
horizon. Kaplan-Meier exists to use partially observed follow-up; a fixture where almost everyone
is observed to fail would be estimated nearly as well by ignoring censoring altogether, and the
step estimator would not be doing any work.

TIMES ARE ROUNDED TO A GRID, and this is inherited from the Cox entry for the same reason: real
follow-up is recorded in whole days or months, and tied EVENT times are what make a tie convention
matter. Here they matter for the log-rank statistic rather than for a partial likelihood.

THE MEDIAN IS INSIDE THE OBSERVED RANGE IN BOTH ARMS, checked below. A Kaplan-Meier median is
undefined when the curve never reaches 0.5, and every language reports that differently -- R gives
NA, lifelines gives inf. An entry whose fixture hit that case would be comparing two spellings of
"undefined" and calling it agreement.

Stdlib only.
"""

import csv
import math
import random
from pathlib import Path

SEED = 20260908
N = 900
BASELINE_HAZARD = 0.06
BETA_EXPOSURE = math.log(1.8)     # a true HAZARD RATIO of exactly 1.8
HORIZON = 24.0                    # administrative censoring, in months
DROPOUT_RATE = 0.02               # independent loss to follow-up
GRID = 0.5                        # follow-up recorded to the half month, so event times TIE


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    for i in range(1, N + 1):
        exposed = 1 if rng.random() < 0.5 else 0
        rate = BASELINE_HAZARD * math.exp(BETA_EXPOSURE * exposed)
        t_event = -math.log(1.0 - rng.random()) / rate
        # Loss to follow-up, independent of the event process, so it does not bias the estimator.
        t_drop = -math.log(1.0 - rng.random()) / DROPOUT_RATE
        t_obs = min(t_event, t_drop, HORIZON)
        event = 1 if (t_event <= t_drop and t_event <= HORIZON) else 0
        rows.append({"id": i, "time": round(round(t_obs / GRID) * GRID, 4),
                     "event": event, "exposed": exposed})

    out = Path(__file__).with_name("fixture.csv")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "time", "event", "exposed"])
        w.writeheader()
        w.writerows(rows)

    ev = sum(r["event"] for r in rows)
    print(f"wrote {out.name}: {len(rows)} rows, {ev} events, {len(rows) - ev} censored "
          f"({100 * (len(rows) - ev) / len(rows):.1f}% censored)")

    for arm in (0, 1):
        sub = [r for r in rows if r["exposed"] == arm]
        e = sum(r["event"] for r in sub)
        pt = sum(r["time"] for r in sub)
        print(f"  arm {arm}: n={len(sub):4d}  events={e:4d}  person-months={pt:8.1f}  "
              f"rate={e / pt:.5f}/month")
        # The Kaplan-Meier median must EXIST in this arm, or every language spells its absence
        # differently and the comparison is between two spellings of "undefined".
        print(f"           median reachable: {km_median(sub) is not None}"
              f"  (KM median {km_median(sub)})")

    ev_times = [r["time"] for r in rows if r["event"] == 1]
    print(f"  TIED EVENT times: {len(ev_times) - len(set(ev_times))} of {len(ev_times)} events "
          f"share a time with another")


def km_median(rows):
    """Kaplan-Meier median from first principles, so the fixture can check its own precondition."""
    times = sorted({r["time"] for r in rows if r["event"] == 1})
    s, at_risk = 1.0, len(rows)
    for t in times:
        d = sum(1 for r in rows if r["time"] == t and r["event"] == 1)
        n = sum(1 for r in rows if r["time"] >= t)
        if n == 0:
            break
        s *= (1 - d / n)
        if s <= 0.5:
            return t
    return None


if __name__ == "__main__":
    main()
