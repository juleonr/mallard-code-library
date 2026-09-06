* Modified Poisson regression for an adjusted RISK RATIO (Zou 2004)
* NOT EXECUTED IN CI. No Stata licence is attached to this repository.

import delimited "fixture.csv", clear varnames(1)

* PINNED DEFAULT, AND A KNOWN DIVERGENCE FROM THE R AND PYTHON FILES.
* Stata's vce(robust) for glm applies a finite-sample correction, so its standard error will not
* match HC0 from R and Python exactly. The point estimate is identical; only the SE differs. This
* is recorded rather than hidden: if Stata is ever executed here, the harness must compare its SE
* on a separate tolerance, or the file must ask for the uncorrected sandwich explicitly.
glm outcome exposed covariate, family(poisson) link(log) vce(robust)

display "--- HARNESS ---"
display "exposure_log_rr=" %20.10f _b[exposed]
display "exposure_se=" %20.10f _se[exposed]
display "covariate_beta=" %20.10f _b[covariate]
