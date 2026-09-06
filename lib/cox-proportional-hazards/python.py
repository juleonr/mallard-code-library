# Cox proportional hazards regression
#
# The Python equivalent of the R file beside this one. lifelines rather than statsmodels: lifelines
# is the maintained survival library and implements Efron's tie handling, which is what the R file
# pins.

import pandas as pd
from lifelines import CoxPHFitter

d = pd.read_csv("fixture.csv")

# PINNED DEFAULT: Efron tie handling. lifelines uses Efron and has no option to change it, which
# happens to match the R file's explicit ties="efron". That is worth stating rather than relying
# on: if lifelines ever gained a Breslow option with a different default, this file would silently
# stop matching, and the agreement check is what would catch it.
cph = CoxPHFitter()
cph.fit(d[["time", "event", "exposed", "covariate"]], duration_col="time", event_col="event")

print("estimates")
cph.print_summary()

print("\n--- HARNESS ---")
print(f"exposure_log_hr={cph.params_['exposed']:.10f}")
print(f"exposure_se={cph.standard_errors_['exposed']:.10f}")
print(f"covariate_beta={cph.params_['covariate']:.10f}")
print(f"n_events={int(d['event'].sum())}")
