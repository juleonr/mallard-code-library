* Competing risks: the cumulative incidence function
* NOT EXECUTED IN CI. No Stata licence is attached to this repository.

import delimited "fixture.csv", clear varnames(1)

stset time, failure(status == 1)

* PINNED: stcompet builds the cumulative incidence function, treating status 2 as a COMPETING
* event rather than as censoring. The stset above declares status 1 the failure, which on its own
* would make status 2 censoring and give the naive curve -- so the compet1() option is not a
* refinement, it is what makes this the right estimator.
stcompet cif = ci, compet1(2)

* THE NAIVE CURVE, ON PURPOSE, so the gap is a number rather than a warning in a comment. This is
* the line to delete from your own analysis: it censors the competing death, as though that patient
* could still go on to have cause 1.
sts list, at(12 24 36) failure

list time cif if inrange(time, 11.9, 12.1) | inrange(time, 23.9, 24.1) | inrange(time, 35.5, 36)

* A regression on this scale is stcrreg, the Fine-Gray subdistribution model, which answers a
* different question from a cause-specific stcox. Neither is in this entry.
