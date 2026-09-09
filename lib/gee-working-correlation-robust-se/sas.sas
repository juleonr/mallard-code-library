/* Marginal logistic regression by GEE, on binary outcomes clustered within clinic.

   NOT EXECUTED. No SAS engine is licensed for this library, so nothing here has been run and
   nothing here is checked by the agreement claim. The pinned strings below are the only guard on
   this file, which is why each one is named in expected.json.

   FOUR THINGS ARE SET DELIBERATELY.

   event='1'. PROC GENMOD models the probability of the FIRST ordered level of the response, which
   for a 0/1 variable is ZERO. Omitting this fits the probability of NOT having the outcome and
   reverses the sign of every coefficient, with no warning anywhere in the output.

   type=exch. THE DEFAULT IS type=ind, an independence working correlation. R's geeglm and
   statsmodels default the same way; Stata's xtgee defaults to exchangeable. Nothing in any of the
   four outputs says which one produced the numbers.

   modelse. With REPEATED specified, GENMOD prints the EMPIRICAL (sandwich) standard errors as its
   "Analysis Of GEE Parameter Estimates" table. modelse adds the model-based table beside it, which
   is what Stata prints by default -- this entry needs both, because the gap between them is its
   subject, and it needs them under BOTH working correlations because the size of that gap depends
   on which structure produced it.

   corrw prints the estimated working correlation matrix, so alpha is visible rather than implied. */

proc import datafile="fixture.csv" out=fixture dbms=csv replace;
  getnames=yes;
run;

proc sort data=fixture; by clinic; run;

proc genmod data=fixture;
  class clinic;
  model outcome(event='1') = exposed x / dist=binomial link=logit;
  repeated subject=clinic / type=exch corrw modelse;
run;

/* The independence fit, for the same reason the other files report it: the working correlation
   changes the point estimate when cluster sizes vary, and reporting only one hides that. */
proc genmod data=fixture;
  class clinic;
  model outcome(event='1') = exposed x / dist=binomial link=logit;
  repeated subject=clinic / type=ind;
run;
