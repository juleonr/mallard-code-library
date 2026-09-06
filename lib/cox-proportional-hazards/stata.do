* Cox proportional hazards regression
* NOT EXECUTED IN CI. No Stata licence is attached to this repository.

import delimited "fixture.csv", clear varnames(1)

stset time, failure(event == 1)

* PINNED DEFAULT: efron. Stata's stcox DEFAULTS TO BRESLOW, like SAS and unlike R and lifelines,
* so this option is what keeps the four languages reporting the same hazard ratio on tied data.
stcox exposed covariate, efron

* The proportional hazards assumption is checked, not assumed.
estat phtest, detail
