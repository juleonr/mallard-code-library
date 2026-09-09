* Two-by-two table: chi-square, Fisher's exact test and the odds ratio
* NOT EXECUTED IN CI. No Stata licence is attached to this repository.

import delimited "fixture.csv", clear varnames(1)

* STATA IS ALREADY ON THE PINNED SIDE OF THIS ONE, AND THE FILE SAYS SO RATHER THAN LEAVING IT TO
* BE INFERRED. The chi2 option gives the UNCORRECTED Pearson chi-square, and Stata has no
* continuity correction here to switch off. R's chisq.test and scipy's chi2_contingency both apply
* one by default. Two analysts on the same table therefore report two different chi-squares, and
* nothing in either output says which is which.
tabulate exposed outcome, chi2 exact row

* The odds ratio with its confidence interval. cs takes the outcome first and the exposure second,
* both coded 1 for present. The value reported is the sample odds ratio ad/bc -- the same quantity
* the R and Python files compute from the table, and NOT the conditional maximum likelihood
* estimate that R's fisher.test returns as its estimate.
cs outcome exposed, or
