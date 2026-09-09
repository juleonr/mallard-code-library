/* Two-by-two table: chi-square, Fisher's exact test and the odds ratio */
/* NOT EXECUTED IN CI. No SAS engine is licensed for this repository. */

proc import datafile="fixture.csv" out=tab dbms=csv replace;
    getnames=yes;
run;

/* PROC FREQ orders levels by their formatted value, so numeric 0 sorts before 1 and the table
   comes out with the unexposed row and the no-event column first. That leaves the odds ratio
   unchanged -- swapping BOTH rows and columns leaves ad/bc alone -- and silently reverses what
   RISKDIFF means, which then reads as the risk of NOT having the event among the UNEXPOSED minus
   the same among the exposed. The numeric prefixes below fix the order where a reader can see it
   rather than in an option they have to remember. */
data tab2;
    set tab;
    length exposure $11 event $10;
    exposure = ifc(exposed = 1, "1 exposed", "2 unexposed");
    event    = ifc(outcome = 1, "1 event",   "2 no event");
run;

/* SAS IS ALREADY ON THE PINNED SIDE OF THIS ONE, WHICH IS WHY THE FILE SAYS SO EXPLICITLY.
   PROC FREQ's CHISQ prints the uncorrected Pearson chi-square as its headline and puts the
   corrected value on a separate row labelled "Continuity Adj. Chi-Square". R's chisq.test and
   scipy's chi2_contingency both apply Yates' correction BY DEFAULT and print only that. So a SAS
   analyst and an R analyst comparing notes on the same table find two chi-squares and nothing in
   either output says why. */
proc freq data=tab2 order=formatted;
    tables exposure*event / chisq riskdiff or nocol nopercent;
    exact fisher;
run;

/* The odds ratio SAS prints under OR is the sample odds ratio ad/bc, which is what the R and
   Python files here report. It is NOT the conditional maximum likelihood estimate that R's
   fisher.test returns as its `estimate`: those are two different estimators of the same parameter
   and they do not agree. */
