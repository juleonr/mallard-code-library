/* NOT EXECUTED. Fixed-model independent binary validation, complete unweighted data.
   Higher predicted values mean outcome=1. These are point estimates, not evidence
   of clinical utility; plan uncertainty and a calibration curve separately. */
proc import datafile="fixture.csv" out=d dbms=csv replace; guessingrows=max; run;
data d; set d;
  if missing(outcome) or missing(predicted) or predicted<=0 or predicted>=1
     or outcome not in (0,1) then abort cancel;
  lp=log(predicted/(1-predicted)); brier=(outcome-predicted)**2;
run;
proc logistic data=d;
  model outcome(event='1') = lp;
run;
/* Calibration-in-the-large holds the supplied log odds as an OFFSET, slope=1. */
proc logistic data=d;
  model outcome(event='1') = / offset=lp;
run;
proc rank data=d out=ranked ties=mean; var predicted; ranks prediction_rank; run;
proc sql;
  select (sum(case when outcome=1 then prediction_rank else 0 end)
          -sum(outcome)*(sum(outcome)+1)/2)/(sum(outcome)*sum(1-outcome)) as auc,
         mean(brier) as brier from ranked;
quit;
