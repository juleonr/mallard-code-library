* Marginal logistic regression by GEE, on binary outcomes clustered within clinic.
*
* NOT EXECUTED. No Stata licence is available to this library, so nothing here has been run and
* nothing here is checked by the agreement claim. The pinned strings are the only guard.
*
* STATA IS THE ODD ONE OUT IN BOTH DIRECTIONS, WHICH IS WHY THIS ENTRY EXISTS.
*
* corr(exchangeable) is Stata's DEFAULT and is written out anyway. R's geeglm, statsmodels and
* SAS's PROC GENMOD all default to INDEPENDENCE. A file translated from any of those three by
* deleting what looked like a redundant option changes the working correlation silently.
*
* vce(robust) is NOT Stata's default. xtgee reports the MODEL-BASED standard error unless asked,
* while geeglm's summary, statsmodels' .bse and GENMOD's REPEATED table all report the sandwich.
* The model-based error is the SMALLER one, so the mistake makes a result look more certain than it
* is rather than less.
*
* HOW MUCH SMALLER DEPENDS ON THE WORKING CORRELATION, and the two defaults interact. Stata's own
* pair -- exchangeable structure, model-based variance -- is the mild case, because a model-based
* variance computed under the right correlation already carries most of it. The severe case is
* INDEPENDENCE with a model-based error, which is what you get by taking R's default structure and
* Stata's default variance. No package defaults to that pair; a file translated between them does.
* README.md carries both ratios as measured on this fixture.

import delimited "fixture.csv", clear

xtset clinic

xtgee outcome exposed x, family(binomial) link(logit) corr(exchangeable) vce(robust)
estat wcorrelation

* The model-based standard error, printed beside it rather than instead of it.
xtgee outcome exposed x, family(binomial) link(logit) corr(exchangeable)

* And the independence working correlation, which is what the other three languages give you by
* default. The point estimate moves because cluster sizes vary.
xtgee outcome exposed x, family(binomial) link(logit) corr(independent) vce(robust)
