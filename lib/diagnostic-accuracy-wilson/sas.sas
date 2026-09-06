/* Diagnostic accuracy against a reference standard, with Wilson intervals */
/* NOT EXECUTED IN CI. No SAS engine is licensed for this repository. */

proc import datafile="fixture.csv" out=dx dbms=csv replace;
    getnames=yes;
run;

/* Sensitivity: the proportion testing positive AMONG THE DISEASED. */
proc freq data=dx;
    where disease = 1;
    tables test / binomial(level='1' cl=wilson) alpha=0.05;
    title "Sensitivity";
run;

/* Specificity: the proportion testing negative among the non-diseased. */
proc freq data=dx;
    where disease = 0;
    tables test / binomial(level='0' cl=wilson) alpha=0.05;
    title "Specificity";
run;
