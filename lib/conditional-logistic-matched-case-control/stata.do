* Conditional logistic regression for a 1:m matched case-control study
* NOT EXECUTED IN CI. No Stata licence is attached to this repository yet, so this file is
* structurally linted and reviewed, never run. See the repository README.

import delimited "fixture.csv", clear varnames(1)

* PINNED DEFAULT: clogit reports coefficients unless asked otherwise. The log-odds scale is what
* the harness compares, so no "or" option is used here; add it when reading the output by eye.
clogit case exposed covariate, group(set_id)

display "--- HARNESS ---"
display "exposure_log_or=" %20.10f _b[exposed]
display "exposure_se=" %20.10f _se[exposed]
display "covariate_beta=" %20.10f _b[covariate]
