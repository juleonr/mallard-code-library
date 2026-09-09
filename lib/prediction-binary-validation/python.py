"""Fixed-model validation, independent uncensored binary outcomes; no training here.
Unweighted complete-data point estimates. Add uncertainty and calibration curves for
real evaluation. Calibration regressions evaluate the fixed predictions, not update them.
"""
import numpy as np
import pandas as pd
from scipy.special import logit
from scipy.stats import rankdata
import statsmodels.api as sm

d = pd.read_csv("fixture.csv")
p, y = d.predicted.to_numpy(), d.outcome.to_numpy()
assert not d.isna().any().any() and set(y) == {0, 1}
assert np.isfinite(p).all() and ((p > 0) & (p < 1)).all()
lp = logit(p)
citl = sm.GLM(y, np.ones((len(y), 1)), offset=lp,
              family=sm.families.Binomial()).fit()
cal = sm.GLM(y, sm.add_constant(lp), family=sm.families.Binomial()).fit()
assert citl.converged and cal.converged
n1, n0 = int(y.sum()), int((1-y).sum())
# Direction is fixed: higher predicted probability means more likely outcome=1.
auc = (rankdata(p, method="average")[y == 1].sum() - n1*(n1+1)/2)/(n1*n0)
brier = np.mean((y-p)**2)
print("\n--- HARNESS ---")
for key, value in dict(auc=auc, brier=brier, calibration_in_large=citl.params[0],
                       calibration_intercept=cal.params[0], calibration_slope=cal.params[1],
                       n=len(y), events=n1).items():
    print(f"{key}={value:.10f}")
