* An average treatment effect by inverse-probability-of-treatment weighting.
*
* NOT EXECUTED. No Stata licence is available to this library, so nothing here has been run and
* nothing here is checked by the agreement claim. The pinned strings are the only guard.
*
* STATA HAS THE SHARPEST VERSION OF THIS ENTRY'S TRAP, because it makes you name the weight type
* and only one of the three is right here.
*
*   fweight  frequency weights -- the observation stands for w identical participants. Standard
*            errors are computed as though the study had sum(w) participants. On this fixture that
*            is about 4000 either way for stabilized weights, but the SEs are still wrong, and with
*            unstabilized weights it is nonsense.
*   aweight  analytic weights -- inverse-variance precision, the right shape for a group mean of
*            known size, and NOT what an inverse-probability weight is.
*   pweight  sampling probability weights -- what an IPTW weight actually is. Stata REQUIRES a
*            robust variance with pweight and gives it automatically, which is the one place a
*            package's default protects you here.
*
* R has ONE `weights =` argument whose meaning is chosen by the family (prior precision for
* gaussian, a count for binomial). statsmodels has TWO (var_weights, freq_weights). Stata has
* three. The same intent, spelled three ways, with different variances behind each.

import delimited "fixture.csv", clear

* Stage one: the propensity model. Its job is balance, not prediction.
logit treated l
predict ps, pr

* Stabilized weights: the marginal treatment probability over the conditional one.
quietly summarize treated
local ptreat = r(mean)
generate double w = cond(treated == 1, `ptreat' / ps, (1 - `ptreat') / (1 - ps))

* A LINEAR model on a binary outcome, so the coefficient is a RISK DIFFERENCE. A weighted logit
* here would estimate a marginal odds ratio, which is a different quantity.
regress outcome treated [pweight=w], vce(robust)

* The same regression unweighted, to put a number on what the weighting bought.
regress outcome treated

* Balance is the check that matters, and it is on the WEIGHTED sample, not the raw one. A
* propensity model with a good c-statistic and poor balance is a worse model here, not a better one.
quietly summarize l if treated == 1 [aweight=w]
quietly summarize l if treated == 0 [aweight=w]
