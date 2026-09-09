/* Kaplan-Meier estimation and the log-rank test */
/* NOT EXECUTED IN CI. No SAS engine is licensed for this repository. */

proc import datafile="fixture.csv" out=surv dbms=csv replace;
    getnames=yes;
run;

/* PINNED DEFAULT 1: conftype=loglog, which IS PROC LIFETEST's default and is named anyway --
   because it is NOT R's. survfit() defaults to the plain log transform, so the same curve carries
   a different default band in the two languages and neither output says which it used. log-log is
   the one that cannot leave [0, 1]; the plain log transform produces upper limits above 1 in the
   tail, where a survival probability cannot go.

   PINNED DEFAULT 2: there is nothing to pin for the test, and that is the point. PROC LIFETEST
   prints the log-rank, the Wilcoxon and the likelihood-ratio tests together. They answer different
   questions -- Wilcoxon weights early differences more heavily -- and a plan naming "the log-rank
   test" means the first row. READ THE LOG-RANK ROW. */
proc lifetest data=surv method=km conftype=loglog plots=(survival(atrisk cb));
    time time*event(0);
    strata exposed / test=logrank;
run;

/* The log-rank has most power against PROPORTIONAL hazards, which is what this fixture generates.
   It is not a general test that two curves differ: where curves CROSS it can return a p near 1
   while the arms are plainly different. That is a property of the test rather than a fault, and
   crossing curves are a reason to look at the plot before quoting the p value. */
