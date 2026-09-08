/* An average treatment effect by inverse-probability-of-treatment weighting.

   NOT EXECUTED. No SAS engine is licensed for this library, so nothing here has been run and
   nothing here is checked by the agreement claim. The pinned strings below are the only guard on
   this file, which is why each one is named in expected.json.

   THREE THINGS ARE SET DELIBERATELY.

   event='1' on the propensity model. PROC LOGISTIC models the probability of the LOWER ordered
   response level, so without this the fitted values are P(untreated) and every weight is inverted
   -- an error that runs to completion and reverses the adjustment.

   The outcome model is PROC GENMOD with dist=normal link=identity on a 0/1 outcome, so the
   coefficient is a RISK DIFFERENCE. A weighted logistic model would estimate a marginal odds
   ratio, which is a different quantity.

   REPEATED SUBJECT=id / TYPE=IND is how the EMPIRICAL (sandwich) standard error is obtained. It
   is not a repeated-measures model -- every subject is its own cluster of one -- it is the
   standard SAS route to a robust variance for a weighted GLM. Without it GENMOD reports the
   model-based error, which treats the estimated weights as known precision. */

proc import datafile="fixture.csv" out=cohort dbms=csv replace;
  getnames=yes;
run;

/* Stage one: the propensity model. Its job is balance, not prediction. */
proc logistic data=cohort descending;
  model treated(event='1') = l;
  output out=ps_out pred=ps;
run;

proc means data=cohort noprint;
  var treated;
  output out=marg mean=ptreat;
run;

data weighted;
  if _n_ = 1 then set marg(keep=ptreat);
  set ps_out;
  if treated = 1 then w = ptreat / ps;
  else w = (1 - ptreat) / (1 - ps);
run;

/* Stage two. The empirical standard error, not the model-based one. */
proc genmod data=weighted;
  class id;
  weight w;
  model outcome = treated / dist=normal link=identity;
  repeated subject=id / type=ind;
run;
