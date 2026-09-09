* Kaplan-Meier estimation and the log-rank test
* NOT EXECUTED IN CI. No Stata licence is attached to this repository.

import delimited "fixture.csv", clear varnames(1)

stset time, failure(event == 1)

* The survival curves and their medians, by arm.
sts list, by(exposed) at(6 12 18 24)
stci, by(exposed)

* PINNED DEFAULT: the unweighted log-rank, which IS what `sts test` gives without options. The
* weighted alternatives are options on the same command -- wilcoxon, tware, peto -- and they answer
* different questions, weighting early differences more heavily. SAS prints several at once and
* lets the reader choose; here it has to be asked for, which is the safer way round.
sts test exposed, logrank

* A note on what this test is FOR. The log-rank has most power against PROPORTIONAL hazards, which
* is what generated this fixture. Where curves CROSS it can return a p near 1 while the arms are
* plainly different, so the plot is worth looking at before the p value is quoted.
sts graph, by(exposed) risktable
