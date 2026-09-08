* Two-sample comparison of means with unequal variances (Welch)
* NOT EXECUTED IN CI. No Stata licence is attached to this repository.

import delimited "fixture.csv", clear varnames(1)

* PINNED DEFAULT: unequal.
*
* Stata's bare `ttest y, by(arm)` is the POOLED test, as scipy's is. The unequal option is what
* matches R's t.test and scipy's equal_var=False: it uses Satterthwaite's degrees of freedom, which
* is the same approximation those two use.
*
* A NEARBY OPTION THAT IS NOT THIS ONE. Stata also has a `welch` option, and it is a DIFFERENT
* degrees-of-freedom formula (Welch 1947) rather than a synonym. On this fixture the two give
* 442.16 and 442.37 -- a difference of a fifth of a degree of freedom out of 442, which changes
* nothing. They separate in small samples, which is where anyone would be reading the df at all.
* `unequal` is the one that matches the other three languages here.
ttest y, by(arm) unequal

* The pooled test, for comparison only. On this fixture its standard error is 32% smaller, because
* the smaller arm is the more variable one.
ttest y, by(arm)
