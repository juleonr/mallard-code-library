* NOT EXECUTED. One-stage stratified PSU sample, linearized variance without FPC.
import delimited "fixture.csv", clear varnames(1)
assert !missing(weight,stratum,psu,outcome,domain) & weight>0
assert inlist(outcome,0,1) & inlist(domain,0,1)
egen long psu_unique=group(stratum psu)
svyset psu_unique [pweight=weight], strata(stratum) vce(linearized) singleunit(missing)
svy: mean outcome
svy, subpop(domain): mean outcome
* Never drop rows outside the domain before svyset. Resolve lonely-PSU policy.
