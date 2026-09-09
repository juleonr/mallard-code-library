* Rate regression on overdispersed counts with unequal follow-up
* NOT EXECUTED IN CI. No Stata licence is attached to this repository.

import delimited "fixture.csv", clear varnames(1)

* PINNED DEFAULT 1: exposure(person_time).
*
* STATA IS THE ODD ONE OUT AND THIS IS THE LINE TO READ TWICE. exposure() takes the person-time
* ITSELF and logs it for you. offset() takes the LOG of the person-time. R, SAS and statsmodels all
* use the offset convention, so a file translated from any of them by swapping the keyword fits a
* model with exp(person_time) where person_time belongs. It runs. It converges. It answers a
* different question, and nothing in the output says so.
*
* PINNED DEFAULT 2: vce(robust). A Poisson model assumes variance equals mean, and these counts
* have a variance 2.4 times their mean. The coefficients stay consistent under that; the
* model-based standard errors do not.
poisson events exposed covariate, exposure(person_time) vce(robust) irr

* The model-based standard errors, for comparison only.
poisson events exposed covariate, exposure(person_time) irr

* The negative binomial alternative. Stata reports the dispersion as alpha, which is the
* RECIPROCAL of the theta R's glm.nb reports and the same quantity SAS calls k.
nbreg events exposed covariate, exposure(person_time) irr
