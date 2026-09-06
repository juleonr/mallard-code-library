/* Cox proportional hazards regression */
/* NOT EXECUTED IN CI. No SAS engine is licensed for this repository. */

proc import datafile="fixture.csv" out=surv dbms=csv replace;
    getnames=yes;
run;

/* PINNED DEFAULT: ties=efron. PROC PHREG DEFAULTS TO BRESLOW, unlike R and lifelines, so a SAS
   file that omits this disagrees with every other language in this entry the moment event times
   tie -- and with follow-up recorded in whole days they always do. This is the single most
   important option in the file. */
proc phreg data=surv;
    model time*event(0) = exposed covariate / ties=efron risklimits;
    assess ph / resample;
run;
