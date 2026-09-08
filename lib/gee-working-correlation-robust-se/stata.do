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
* On this fixture the two differ by 78%, so the same estimate carries an interval 44% too narrow.
* This is the direction that matters: the model-based error is the SMALLER one, so the mistake
* makes a result look more certain than it is rather than less.

import delimited "fixture.csv", clear

xtset clinic

xtgee outcome exposed x, family(binomial) link(logit) corr(exchangeable) vce(robust)
estat wcorrelation

* The model-based standard error, printed beside it rather than instead of it.
xtgee outcome exposed x, family(binomial) link(logit) corr(exchangeable)

* And the independence working correlation, which is what the other three languages give you by
* default. The point estimate moves because cluster sizes vary.
xtgee outcome exposed x, family(binomial) link(logit) corr(independent) vce(robust)
