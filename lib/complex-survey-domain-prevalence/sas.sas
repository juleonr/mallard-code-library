/* NOT EXECUTED. One-stage stratified PSU sample, Taylor variance without FPC.
   Retain every sampled row. DOMAIN, not a WHERE restriction before design declaration.
   No missing items, replicate weights or multistage design supported here. */
proc import datafile="fixture.csv" out=d dbms=csv replace; guessingrows=max; run;
data d; set d;
 if missing(weight) or weight<=0 or missing(stratum) or missing(psu)
    or outcome not in (0,1) or domain not in (0,1) then abort cancel;
run;
proc surveymeans data=d varmethod=taylor mean stderr;
 strata stratum;
 cluster psu;
 weight weight;
 var outcome;
 domain domain;
run;
/* Read domain=1, and distinguish respondent counts from population estimates. */
