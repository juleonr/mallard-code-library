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

* A CORRECTION TO AN EARLIER VERSION OF THIS COMMENT. It claimed the interval had to be built on
* specificity because "the Wilson interval is asymmetric, so complementing its bounds does not give
* specificity's". That is FALSE, and a cross-lab reviewer caught it. The Wilson interval IS
* equivariant under complementation: its centre is (x + z^2/2)/(n + z^2), which maps to 1 - centre
* when x -> n - x, and its half-width depends on x only through x(n-x)/n, which is unchanged. So
* CI(1-p) = [1 - U(p), 1 - L(p)] exactly, boundary cases included. Verified numerically at
* 9/10, 1/10, 50/100, 603/2000, 0/20, 20/20 and 3/7.
*
* The reason to estimate specificity directly is therefore simpler and is about the REPORT, not the
* arithmetic: the old code printed the false-positive rate under the label "specificity". A reader
* comparing it with the R and Python output sees 0.10 where they see 0.90. Complementing by hand
* afterwards would give the right numbers, and would be one more step for a reader to get wrong.

* diagt gives the full accuracy table if the user has installed it (ssc install diagt).
