# Competing risks: the cumulative incidence function
#
# The Python equivalent of the R file beside this one. Both estimators are computed, because the
# number that matters here is the gap between them.

import pandas as pd
from lifelines import AalenJohansenFitter, KaplanMeierFitter

d = pd.read_csv("fixture.csv")

# PINNED: event_of_interest=1, and the OTHER codes are competing events rather than censoring.
# AalenJohansenFitter takes the full status column, so cause 2 stays a cause; passing a 0/1
# indicator instead would make it censoring and give the naive curve under a different name.
ajf = AalenJohansenFitter(calculate_variance=False)
ajf.fit(d["time"], d["status"], event_of_interest=1)

# THE NAIVE CURVE, computed ON PURPOSE. This is the line to delete from your own analysis.
kmf = KaplanMeierFitter()
kmf.fit(d["time"], (d["status"] == 1).astype(int))

cif = ajf.cumulative_density_
at = lambda t: float(cif.asof(t).iloc[0])

print("cumulative incidence of cause 1 (Aalen-Johansen), and the naive 1 - KM beside it")
for t in (12.0, 24.0, 36.0):
    naive = 1 - float(kmf.predict(t))
    print(f"  t={t:4.0f}   CIF {at(t):.6f}   1-KM {naive:.6f}   "
          f"the naive curve overstates by {naive - at(t):.6f}")

print("\n--- HARNESS ---")
print(f"cif1_12={at(12.0):.10f}")
print(f"cif1_24={at(24.0):.10f}")
print(f"cif1_36={at(36.0):.10f}")
print(f"naive_incidence_36={1 - float(kmf.predict(36.0)):.10f}")
print(f"n_cause1={int((d['status'] == 1).sum())}")
print(f"n_cause2={int((d['status'] == 2).sum())}")
print(f"n={len(d)}")
