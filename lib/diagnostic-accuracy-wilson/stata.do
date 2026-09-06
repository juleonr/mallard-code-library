* Diagnostic accuracy against a reference standard, with Wilson intervals
* NOT EXECUTED IN CI. No Stata licence is attached to this repository.

import delimited "fixture.csv", clear varnames(1)

* PINNED: wilson is requested explicitly. ci proportions defaults to an exact (Clopper-Pearson)
* interval, which is a different and more conservative interval, not the one the R and Python
* files report. Agreement across languages requires asking for the same interval.
ci proportions test if disease == 1, wilson
ci proportions test if disease == 0, wilson

* diagt gives the full accuracy table if the user has installed it (ssc install diagt).
