* Linear regression with heteroskedasticity-consistent standard errors
* NOT EXECUTED IN CI. No Stata licence is attached to this repository.

import delimited "fixture.csv", clear varnames(1)

* PINNED DEFAULT: vce(hc3).
*
* Stata's familiar `, robust` is NOT this. It is HC1, the HC0 sandwich scaled by n/(n-k), and it
* is what almost every Stata example in print uses. R defaults to HC3 and SAS to HC0, so the three
* languages disagree by default while every one of them prints the words "robust standard errors".
regress y exposed covariate, vce(hc3)

* The classical fit, for comparison only. The test that follows is the one that says whether its
* constant-variance assumption holds. It does not on this fixture, by construction.
regress y exposed covariate
estat hettest, rhs iid
