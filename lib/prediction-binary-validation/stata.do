* NOT EXECUTED. Fixed-model binary validation, independent complete unweighted data.
* Do not update the supplied predictions with the calibration model fitted below.
import delimited "fixture.csv", clear varnames(1)
assert inlist(outcome,0,1) & predicted>0 & predicted<1 & !missing(predicted)
generate double lp=logit(predicted)
glm outcome lp, family(binomial) link(logit)
glm outcome, family(binomial) link(logit) offset(lp)
roctab outcome predicted
generate double brier=(outcome-predicted)^2
summarize brier
* Point estimates need uncertainty and calibration curves before real interpretation.
