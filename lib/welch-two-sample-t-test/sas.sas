/* Two-sample comparison of means with unequal variances (Welch) */
/* NOT EXECUTED IN CI. No SAS engine is licensed for this repository. */

proc import datafile="fixture.csv" out=arms dbms=csv replace;
    getnames=yes;
run;

/* SAS IS THE ONE LANGUAGE HERE WITH NO OPTION TO PIN, AND THAT IS WORTH STATING RATHER THAN
   PAPERING OVER. PROC TTEST prints BOTH rows -- "Pooled" first, then "Satterthwaite" -- together
   with a folded F test of equal variances. Nothing is defaulted and nothing can be switched off;
   the choice is made by which row the reader's eye lands on, and the wrong one is printed first.

   READ THE SATTERTHWAITE ROW. It is the row that matches R's t.test and scipy's equal_var=False.
   The Pooled row above it assumes the two arms have the same spread, which they do not here.

   The folded F test is reported by SAS beside them. It is NOT a gate: choosing Welch only after a
   variance test fails is a two-stage procedure whose overall error rate is not the nominal one.
   Where the arms are not known to have equal spread, Welch is the default worth having. */
proc ttest data=arms;
    class arm;
    var y;
run;
