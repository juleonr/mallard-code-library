/* Modified Poisson regression for an adjusted RISK RATIO (Zou 2004) */
/* NOT EXECUTED IN CI. No SAS engine is licensed for this repository. */

proc import datafile="fixture.csv" out=rr dbms=csv replace;
    getnames=yes;
run;

/* PINNED DEFAULT: the robust ("empirical") variance is obtained through the REPEATED statement
   with each subject its own cluster. Without it PROC GENMOD reports model-based standard errors
   from a Poisson variance that does not hold for binary data. */
proc genmod data=rr;
    class id;
    model outcome = exposed covariate / dist=poisson link=log;
    repeated subject=id / type=ind;
    estimate 'log RR exposed' exposed 1;
run;
