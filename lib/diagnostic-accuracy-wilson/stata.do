* Diagnostic accuracy against a reference standard, with Wilson intervals
* NOT EXECUTED IN CI. No Stata licence is attached to this repository.

import delimited "fixture.csv", clear varnames(1)

* PINNED: wilson is requested explicitly. ci proportions defaults to an exact (Clopper-Pearson)
* interval, which is a different and more conservative interval, not the one the R and Python
* files report. Agreement across languages requires asking for the same interval.

* SENSITIVITY is the proportion testing POSITIVE among the diseased, so `test` is the variable.
ci proportions test if disease == 1, wilson

* SPECIFICITY is the proportion testing NEGATIVE among the non-diseased, so it needs its own
* variable. `ci proportions test if disease == 0` estimates the proportion testing POSITIVE in that
* group -- the FALSE-POSITIVE RATE, which is 1 - specificity. The same command is right on the line
* above and wrong here, because sensitivity happens to be a test == 1 proportion and specificity is
* a test == 0 proportion. On this fixture, where specificity is 0.90, it would print 0.10.
generate byte negtest = (test == 0)
ci proportions negtest if disease == 0, wilson

* AND THE INTERVAL HAS TO BE BUILT ON SPECIFICITY ITSELF, not recovered from the false-positive
* rate afterwards. The Wilson interval is asymmetric about the point estimate, so complementing the
* bounds of an interval for 1 - p does not give the interval for p. Estimating the right proportion
* is what makes the bounds right, not just the point estimate.

* diagt gives the full accuracy table if the user has installed it (ssc install diagt).
