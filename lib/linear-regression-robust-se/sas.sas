/* Linear regression with heteroskedasticity-consistent standard errors */
/* NOT EXECUTED IN CI. No SAS engine is licensed for this repository. */

proc import datafile="fixture.csv" out=lin dbms=csv replace;
    getnames=yes;
run;

/* PINNED DEFAULT: hccmethod=3.

   HCC alone gives HCCMETHOD=0, which is HC0 -- the estimator with no small-sample correction at
   all. R's vcovHC defaults to HC3 and Stata's robust option gives HC1, so a SAS file that writes
   only `/ hcc` reports a third quantity again, and nothing in the listing names which. */
proc reg data=lin;
    model y = exposed covariate / hcc hccmethod=3 spec;
run;
quit;

/* SPEC above is White's test of the constant-variance assumption the classical standard errors
   printed beside these rest on. It does not survive on this fixture, by construction: the two arms
   were generated with different spread. The point estimates are unaffected either way -- what
   changes is the width of every interval. */
