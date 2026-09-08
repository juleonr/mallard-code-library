# Two-sample comparison of means with unequal variances (Welch)
#
# The Python equivalent of the R file beside this one, and the language where the default is most
# dangerous: scipy runs the POOLED test unless told otherwise.

import numpy as np
import pandas as pd
from scipy import stats

d = pd.read_csv("fixture.csv")

# Selected by the arm COLUMN, not by position; the fixture is shuffled.
treated = d.loc[d["arm"] == 1, "y"].to_numpy()
control = d.loc[d["arm"] == 0, "y"].to_numpy()

# PINNED DEFAULT: equal_var=False, the Welch test.
#
# scipy.stats.ttest_ind DEFAULTS TO equal_var=True, the pooled test, so the shortest correct-looking
# line in Python -- ttest_ind(treated, control) -- runs a different test from the shortest
# correct-looking line in R. On this fixture that costs 32% of the standard error, in the direction
# that manufactures significance.
welch = stats.ttest_ind(treated, control, equal_var=False)
pooled = stats.ttest_ind(treated, control, equal_var=True)

# The standard errors are computed from the sample variances rather than recovered by dividing the
# difference by the t statistic. Both are correct here; the explicit form is what a reader can check
# against the formula, and it does not silently inherit a sign or a scaling from the test object.
n1, n0 = len(treated), len(control)
v1, v0 = treated.var(ddof=1), control.var(ddof=1)
welch_se = np.sqrt(v1 / n1 + v0 / n0)
pooled_var = ((n1 - 1) * v1 + (n0 - 1) * v0) / (n1 + n0 - 2)
pooled_se = np.sqrt(pooled_var * (1 / n1 + 1 / n0))

print("Welch (unequal variances)")
print(f"  t = {welch.statistic:.6f}  df = {welch.df:.4f}  p = {welch.pvalue:.6g}")
print("pooled, FOR COMPARISON ONLY -- it assumes the arms have the same spread")
print(f"  t = {pooled.statistic:.6f}  df = {pooled.df:.4f}  p = {pooled.pvalue:.6g}")

print("\n--- HARNESS ---")
print(f"mean_difference={treated.mean() - control.mean():.10f}")
print(f"mean_treated={treated.mean():.10f}")
print(f"mean_control={control.mean():.10f}")
print(f"difference_se={welch_se:.10f}")
print(f"difference_se_pooled={pooled_se:.10f}")
print(f"welch_df={welch.df:.10f}")
print(f"pooled_df={float(pooled.df):.10f}")
print(f"t_welch={welch.statistic:.10f}")
print(f"n_treated={n1}")
print(f"n_control={n0}")
