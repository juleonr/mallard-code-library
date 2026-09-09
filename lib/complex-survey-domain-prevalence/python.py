"""Explicit WR Taylor variance for a ONE-STAGE stratified PSU ratio mean.
This is not a general survey package. No FPC, calibration/replicate weights,
multistage sampling or missing items. Do not substitute generic WLS standard errors.
"""
import numpy as np
import pandas as pd

d = pd.read_csv("fixture.csv")
assert not d.isna().any().any() and (d.weight > 0).all()
assert set(d.outcome).issubset({0, 1}) and set(d.domain).issubset({0, 1})


def ratio_mean(data, domain):
    # Domain indicator zeroes contributions but keeps EVERY sampled PSU in its stratum.
    denominator = np.sum(data.weight * domain)
    assert denominator > 0
    estimate = np.sum(data.weight * domain * data.outcome) / denominator
    linearized = data.weight * domain * (data.outcome - estimate) / denominator
    totals = data.assign(u=linearized).groupby(["stratum", "psu"], sort=True).u.sum()
    variance = 0.0
    for _, group in totals.groupby(level="stratum"):
        m = len(group)
        assert m >= 2, "Lonely PSU: resolve survey provider's variance policy"
        variance += m/(m-1) * np.sum((group-group.mean())**2)
    return float(estimate), float(np.sqrt(variance))


overall, overall_se = ratio_mean(d, np.ones(len(d)))
domain, domain_se = ratio_mean(d, d.domain.to_numpy())
print("\n--- HARNESS ---")
for key, value in dict(prevalence=overall, prevalence_se=overall_se,
                       domain_prevalence=domain, domain_prevalence_se=domain_se,
                       n=len(d), psus=len(d[["stratum", "psu"]].drop_duplicates()),
                       strata=d.stratum.nunique()).items():
    print(f"{key}={value:.10f}")
