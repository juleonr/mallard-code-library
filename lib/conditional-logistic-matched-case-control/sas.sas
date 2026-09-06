/* Conditional logistic regression for a 1:m matched case-control study */
/* NOT EXECUTED IN CI. No SAS engine is licensed for this repository yet, so this file is
   structurally linted and reviewed, never run. See the repository README. */

proc import datafile="fixture.csv" out=mcc dbms=csv replace;
    getnames=yes;
run;

/* PINNED DEFAULT: the modelled level. PROC LOGISTIC models the LOWER ordered value by default,
   which for a 0/1 outcome is 0 -- the opposite of what is wanted. event='1' is not optional
   decoration here; without it every odds ratio in the output is inverted. */
proc logistic data=mcc;
    strata set_id;
    model case(event='1') = exposed covariate;
    ods output ParameterEstimates=est;
run;

proc print data=est;
run;
