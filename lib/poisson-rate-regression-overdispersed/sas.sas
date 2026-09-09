/* Rate regression on overdispersed counts with unequal follow-up */
/* NOT EXECUTED IN CI. No SAS engine is licensed for this repository. */

proc import datafile="fixture.csv" out=rates dbms=csv replace;
    getnames=yes;
run;

/* SAS's OFFSET= takes a variable, and that variable must ALREADY BE LOGGED. There is no exposure()
   convention here as there is in Stata, so the log has to be taken explicitly and the model
   statement points at the logged column. */
data rates;
    set rates;
    log_pt = log(person_time);
run;

/* PINNED DEFAULT 1: offset=log_pt, which makes this a RATE model. Omitting it models events per
   PATIENT, which with follow-up from six months to five years is a different question with a
   plausible-looking answer.

   PINNED DEFAULT 2: the REPEATED statement with type=ind. It fits the same Poisson model and
   reports EMPIRICAL (robust) standard errors instead of model-based ones. Without it PROC GENMOD
   reports the model-based errors, which assume variance equals mean -- and these counts have a
   variance 2.4 times their mean. Subjects are singletons here, so type=ind changes nothing about
   the estimates; it is the sandwich that is wanted. */
proc genmod data=rates;
    class id;
    model events = exposed covariate / dist=poisson link=log offset=log_pt;
    repeated subject=id / type=ind;
run;

/* The negative binomial alternative. SAS reports the dispersion as k, which is the same quantity
   statsmodels and Stata call alpha and the RECIPROCAL of the theta R's glm.nb reports. */
proc genmod data=rates;
    model events = exposed covariate / dist=negbin link=log offset=log_pt;
run;
