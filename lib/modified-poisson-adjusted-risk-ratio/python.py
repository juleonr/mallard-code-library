# Modified Poisson regression for an adjusted RISK RATIO (Zou 2004)
#
# The Python equivalent of the R file beside this one. Same model, same robust variance flavour.

import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

d = pd.read_csv("fixture.csv")

model = smf.glm("outcome ~ exposed + covariate", data=d,
                family=sm.families.Poisson(link=sm.families.links.Log()))

# PINNED DEFAULT: cov_type="HC0", matching the R file. statsmodels defaults to the model-based
# (nonrobust) covariance for GLM, which for a log-link Poisson fitted to binary data is simply
# wrong: the Poisson variance assumption does not hold and the intervals are not usable.
result = model.fit(cov_type="HC0")

print("estimates (log scale, HC0 robust)")
print(result.summary())

print("\n--- HARNESS ---")
print(f"exposure_log_rr={result.params['exposed']:.10f}")
print(f"exposure_se={result.bse['exposed']:.10f}")
print(f"covariate_beta={result.params['covariate']:.10f}")
print(f"n={len(d)}")
