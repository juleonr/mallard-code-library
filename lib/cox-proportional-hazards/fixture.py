"""Seeded fixture for Cox proportional hazards regression.

Survival times are drawn from an EXPONENTIAL model whose hazard is baseline * exp(Xb). That is a
proportional hazards model by construction, so the betas below are the parameters a Cox model
estimates, not merely those of a process that resembles one. Cox conditions the baseline hazard
away, so its value cannot affect the recovered betas; leaving it in the generator is a check that
an implementation really is fitting a proportional hazards model and not a parametric one with the
baseline soaked into the coefficients.

Censoring is ADMINISTRATIVE: everyone still at risk at the horizon is censored there. Independent
of the outcome, so it does not bias the estimate, and heavy enough that an implementation ignoring
the event indicator entirely would be visibly wrong.

TIMES ARE ROUNDED TO A GRID, AND THAT IS THE POINT OF THIS FIXTURE. The first version drew
continuous exponential times, which produced 714 tied times -- every one of them a CENSORING tie
at the horizon. Tied censoring times never invoke a tie-handling method; only tied EVENT times do.
So the fixture could not test `ties=`, which is the default this entry exists to pin, and the pin
would have been decoration. Real follow-up is recorded in whole days or months anyway, so rounding
to a grid is both more realistic and what makes Efron and Breslow actually diverge.

Stdlib only.
"""

import csv
import math
import random
from pathlib import Path

SEED = 20260906
N = 1500
BASELINE_HAZARD = 0.05
BETA_EXPOSURE = math.log(1.6)     # true HAZARD RATIO of exactly 1.6
BETA_COVARIATE = 0.3
HORIZON = 12.0                    # administrative censoring time
GRID = 0.1                        # follow-up recorded to this resolution, so event times TIE


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    for i in range(1, N + 1):
        exposed = 1 if rng.random() < 0.45 else 0
        covariate = rng.gauss(0.0, 1.0)
        rate = BASELINE_HAZARD * math.exp(BETA_EXPOSURE * exposed + BETA_COVARIATE * covariate)
        t = -math.log(1.0 - rng.random()) / rate
        event = 1 if t <= HORIZON else 0
        observed = min(t, HORIZON)
        observed = round(round(observed / GRID) * GRID, 4)
        rows.append({"id": i, "time": observed,
                     "event": event, "exposed": exposed, "covariate": round(covariate, 6)})

    out = Path(__file__).with_name("fixture.csv")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "time", "event", "exposed", "covariate"])
        w.writeheader()
        w.writerows(rows)

    ev = sum(r["event"] for r in rows)
    # A crude check needing no model: among the exposed the event rate should be higher.
    e1 = [r for r in rows if r["exposed"] == 1]
    e0 = [r for r in rows if r["exposed"] == 0]
    rate1 = sum(r["event"] for r in e1) / sum(r["time"] for r in e1)
    rate0 = sum(r["event"] for r in e0) / sum(r["time"] for r in e0)
    print(f"wrote {out.name}: {len(rows)} rows, {ev} events ({100*ev/len(rows):.1f}%), "
          f"{len(rows)-ev} censored")
    print(f"  crude rate ratio (events per person-time): {rate1/rate0:.4f}   true HR "
          f"{math.exp(BETA_EXPOSURE):.4f}")
    ev_times = [r["time"] for r in rows if r["event"] == 1]
    tied_events = len(ev_times) - len(set(ev_times))
    print(f"  TIED EVENT times: {tied_events} of {len(ev_times)} events share a time with another")
    print(f"  (tied EVENTS are what make ties= matter; tied CENSORINGS do not)")


if __name__ == "__main__":
    main()
