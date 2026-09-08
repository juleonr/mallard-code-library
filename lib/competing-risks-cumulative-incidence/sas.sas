/* Competing risks: the cumulative incidence function */
/* NOT EXECUTED IN CI. No SAS engine is licensed for this repository. */

proc import datafile="fixture.csv" out=cr dbms=csv replace;
    getnames=yes;
run;

/* PINNED: eventcode=1 on the FAILCODE option. That is what makes this the cumulative incidence
   function rather than one minus a Kaplan-Meier curve.

   PROC LIFETEST's plots=cif with eventcode= gives the Aalen-Johansen estimator. WITHOUT eventcode
   the same procedure gives a Kaplan-Meier curve in which every non-zero status is the event, so
   cause 2 would be silently counted as cause 1 -- and there is a third spelling, time*status(0 2),
   which treats cause 2 as CENSORING and gives the naive curve. Three spellings, three different
   answers, and none of them warns you. */
proc lifetest data=cr plots=cif(test) eventcode=1;
    time time*status(0);
run;

/* THE NAIVE CURVE, run ON PURPOSE so the gap is a number in the output rather than a warning in a
   comment. This is the line to delete from your own analysis, not to copy: it censors the competing
   death, as though that patient could still go on to have cause 1. They cannot. */
proc lifetest data=cr;
    time time*status(0 2);
run;

/* A regression on this scale is PROC PHREG with eventcode=, which fits the Fine-Gray
   subdistribution model. That is a different question from a cause-specific Cox model and the two
   answer different things: cause-specific for aetiology, subdistribution for prediction. Neither is
   in this entry. */
