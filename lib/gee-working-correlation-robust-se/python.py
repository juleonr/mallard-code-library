"""Marginal logistic regression by GEE, on binary outcomes clustered within clinic.

The same three defaults the R file pins, from the other side:

1. cov_struct=Exchangeable(). statsmodels DEFAULTS TO Independence(), so `sm.GEE(...).fit()` with
   no cov_struct is a different model from Stata's bare `xtgee`, which is exchangeable.

2. groups= does the clustering, and unlike geepack statsmodels does not need the rows sorted. The
   sort in the R file is not paranoia about this one: it is required there and not here, which is
   itself the kind of difference a translated file loses.

3. Both standard errors. `.bse` is the sandwich; the model-based one has to be asked for by name.
"""

import pandas as pd
import statsmodels.api as sm
from statsmodels.genmod.cov_struct import Exchangeable, Independence

d = pd.read_csv("fixture.csv")

model = sm.GEE.from_formula("outcome ~ exposed + x", groups="clinic", data=d,
                            family=sm.families.Binomial(), cov_struct=Exchangeable())
fit = model.fit()

se_robust = fit.standard_errors(cov_type="robust")
se_naive = fit.standard_errors(cov_type="naive")

ind = sm.GEE.from_formula("outcome ~ exposed + x", groups="clinic", data=d,
                          family=sm.families.Binomial(), cov_struct=Independence()).fit()

alpha = model.cov_struct.dep_params
alpha = float(alpha) if not hasattr(alpha, "__len__") else float(alpha[0])

print("--- HARNESS ---")
print(f"exposure_log_or={fit.params['exposed']:.10f}")
print(f"exposure_se_robust={se_robust['exposed']:.10f}")
print(f"exposure_se_naive={se_naive['exposed']:.10f}")
print(f"covariate_beta={fit.params['x']:.10f}")
print(f"exposure_log_or_independence={ind.params['exposed']:.10f}")
print(f"alpha_exchangeable={alpha:.10f}")
