/* Mixed-effects logistic regression for a cluster-randomised binary outcome */
/* NOT EXECUTED IN CI. No SAS engine is licensed for this repository. */

proc import datafile="fixture.csv" out=cl dbms=csv replace;
    getnames=yes;
run;

/* PINNED DEFAULT: method=quad. PROC GLIMMIX DEFAULTS TO RSPL, a pseudo-likelihood that is known
   to be biased for binary outcomes with small clusters, and it is not comparable to glmer's
   quadrature. method=quad is the equivalent of nAGQ > 1.
   Also note ddfm: GLIMMIX defaults to a containment method for denominator degrees of freedom;
   with few clusters, betweenwithin or Kenward-Roger is the defensible choice. */
proc glimmix data=cl method=quad(qpoints=10);
    class cluster;
    model outcome(event='1') = exposed / dist=binary link=logit ddfm=betwithin;
    random intercept / subject=cluster;
run;
