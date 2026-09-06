* Mixed-effects logistic regression for a cluster-randomised binary outcome
* NOT EXECUTED IN CI. No Stata licence is attached to this repository.

import delimited "fixture.csv", clear varnames(1)

* PINNED DEFAULT: intpoints. melogit defaults to 7 adaptive quadrature points; naming it keeps the
* estimate reproducible across versions and comparable with the R file's nAGQ = 10.
melogit outcome exposed || cluster:, intpoints(10)

* The cluster-conditional odds ratio, which is NOT what a GEE (xtgee, population-averaged) reports.
melogit, or
