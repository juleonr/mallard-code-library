# Linear regression with heteroskedasticity-consistent standard errors
#
# The Python equivalent of the R file beside this one. The point estimates do not depend on the
# variance estimator, so every fit below reports the same coefficients; only the standard errors
# differ.

import pandas as pd
import statsmodels.api as sm

d = pd.read_csv("fixture.csv")

X = sm.add_constant(d[["exposed", "covariate"]])
mod = sm.OLS(d["y"], X)

# PINNED DEFAULT: cov_type="HC3", to match the R file's vcovHC(type = "HC3").
#
# statsmodels is the one package here with NO robust default: a bare .fit() returns the classical
# variance, which assumes constant error variance and is wrong on this fixture by construction.
# Writing .fit() and calling the result robust is the mistake this line exists to prevent.
res = mod.fit(cov_type="HC3")

# The same ladder the R file prints, so the two can be compared rung by rung.
res_hc0 = mod.fit(cov_type="HC0")
res_hc1 = mod.fit(cov_type="HC1")
res_classical = mod.fit()

print("estimates with HC3 standard errors")
print(res.summary())
print("\nclassical standard errors, for comparison ONLY -- they assume constant variance")
print(res_classical.bse)

print("\n--- HARNESS ---")
print(f"intercept={res.params['const']:.10f}")
print(f"exposure_beta={res.params['exposed']:.10f}")
print(f"covariate_beta={res.params['covariate']:.10f}")
print(f"exposure_se={res.bse['exposed']:.10f}")
print(f"covariate_se={res.bse['covariate']:.10f}")
print(f"exposure_se_hc0={res_hc0.bse['exposed']:.10f}")
print(f"exposure_se_hc1={res_hc1.bse['exposed']:.10f}")
print(f"exposure_se_classical={res_classical.bse['exposed']:.10f}")
print(f"n={len(d)}")
