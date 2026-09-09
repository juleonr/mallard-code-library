"""An average treatment effect by inverse-probability-of-treatment weighting.

The same four points the R file makes, from the other side. The fourth is the one that differs:

`weights=` in R's glm means a PRIOR PRECISION weight for gaussian and a COUNT for binomial, one
argument with two meanings chosen by the family. statsmodels splits them -- `var_weights` and
`freq_weights` -- and makes the caller pick. For IPTW the answer is var_weights: the weights are
not counts, and `freq_weights` reports a standard error computed as though the study had sum(w)
participants. WLS's `weights` argument is the var_weights sense, which is why it is used here.

The propensity model's job is BALANCE, not prediction. A model chosen to maximise discrimination
can be worse for the estimate than one that is merely correct.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm

d = pd.read_csv("fixture.csv")

ps_fit = sm.GLM.from_formula("treated ~ L", data=d, family=sm.families.Binomial()).fit()
e = ps_fit.fittedvalues

p_treat = d["treated"].mean()
w = np.where(d["treated"] == 1, p_treat / e, (1.0 - p_treat) / (1.0 - e))

X = sm.add_constant(d[["treated"]].astype(float))
y = d["outcome"].astype(float)

out = sm.WLS(y, X, weights=w).fit()
robust = sm.WLS(y, X, weights=w).fit(cov_type="HC0")

crude = sm.OLS(y, X).fit()

print("--- HARNESS ---")
print(f"ate_iptw={out.params['treated']:.10f}")
print(f"ate_se_robust={robust.bse['treated']:.10f}")
print(f"ate_se_model={out.bse['treated']:.10f}")
print(f"ate_crude={crude.params['treated']:.10f}")
print(f"ps_beta_L={ps_fit.params['L']:.10f}")
print(f"mean_stabilized_weight={w.mean():.10f}")
print(f"max_stabilized_weight={w.max():.10f}")
print(f"n={len(d)}")
