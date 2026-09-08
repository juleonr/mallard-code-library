# Marginal logistic regression by GEE on clustered binary data

Estimates a **population-average** odds ratio when patients within a clinic are more alike than
patients across clinics.

## This is not the same number as the mixed-effects entry

`mixed-effects-logistic-clustered` estimates the **cluster-conditional** odds ratio: the effect for
a patient, holding their clinic fixed. GEE estimates the **marginal** one: the effect in the
population as a whole. On identical data those are different numbers, and the marginal one is
attenuated toward the null.

Neither is a better version of the other, and a plan has to say which it wants. That is also why
this fixture generates the marginal model **directly** rather than through a random intercept: a
random-intercept generator has no closed-form marginal odds ratio, so an entry built that way would
be asking GEE to recover a parameter it does not estimate and reporting the attenuation as error.

## The defaults this entry exists to pin

### The working correlation, where Stata is alone

| Language | Default working correlation |
|---|---|
| R `geeglm` | **independence** |
| Python `statsmodels.GEE` | **independence** |
| SAS `PROC GENMOD ... REPEATED` | **independence** (`type=ind`) |
| Stata `xtgee` | **exchangeable** |

Three default one way and the fourth defaults the other, and no output in any of them names the
structure it used. A file translated from R to Stata by deleting what looks like a redundant option
fits a different model; a file translated the other way does too.

Every file here writes `exchangeable` out, **including Stata's, where it is already the default**.
A default that is not written down is one release from changing.

### The standard error, where Stata is alone again and in the dangerous direction

| Language | What the obvious code reports |
|---|---|
| R `summary(geeglm)` | the **sandwich** |
| Python `.bse` | the **sandwich** |
| SAS `REPEATED` | the **empirical** (sandwich) table |
| Stata `xtgee` | the **model-based** error, unless `vce(robust)` |

On the committed fixture the sandwich standard error for the exposure coefficient is **0.1685** and
the model-based one is **0.0944** — a ratio of **1.785**. A confidence interval built on the
model-based error is **44% too narrow**, around an identical point estimate.

That is the direction that matters. The model-based error is the **smaller** one, so the mistake
makes a result look more certain than it is. It is the same shape as the overdispersion trap in
`poisson-rate-regression-overdispersed`: **confidently wrong rather than visibly wrong.**

Both are separate harness keys, so an engine reporting one as the other fails the agreement check
rather than passing with a plausible number.

### And a silent one in R that has nothing to do with statistics

**`geeglm` requires the rows of a cluster to be contiguous.** It does not check. Unsorted input is
treated as many small clusters, which collapses the sandwich toward the model-based error — the
exact failure the file is written to avoid, arriving through the back door. `r.R` sorts
unconditionally even though the committed fixture already arrives sorted. `statsmodels` does not
need this, which is itself a difference a translated file loses.

### And a silent one in SAS that reverses the answer

`PROC GENMOD` models the probability of the **first ordered level** of the response, which for a 0/1
variable is **zero**. Omitting `event='1'` fits the probability of *not* having the outcome and
reverses the sign of every coefficient, with no warning in the output.

## What the fixture is built to make testable

**Exposure has a clinic-level component**, and this is the choice the entry turns on. Measured: with
a clinic-level exposure spread of 0.9 the sandwich-to-model-based ratio for the exposure coefficient
is **1.022** — the demonstration would have been a rounding difference. At 2.5 it is 1.785 on the
committed seed and above 1.3 on 98% of 200 calibration seeds. Some clinics prescribe far more than
others, which is both realistic and what puts the exposure contrast between clusters where the
clustering can reach it.

**Cluster sizes vary from 8 to 40.** With equal cluster sizes, working-independence and
working-exchangeable give the **same** point estimate, and the choice of working correlation would
have nothing to say about the estimate at all. Size is drawn independently of exposure and outcome:
cluster size that carries information about the outcome makes the two working correlations target
**different estimands**, which is real and is not this entry's subject.

**Ninety clusters**, not twelve. The sandwich is a large-sample estimator and is biased downward
when clusters are few — CLAUDE.md warns under 30 and blocks under 15 unless a small-sample approach
is named. An entry demonstrating the sandwich on a dozen clusters would be modelling the practice
the product warns about. Mancl-DeRouen, Kauermann-Carroll and Fay-Graubard corrections are not in
`geepack` and belong to a separate entry.

The latent within-clinic correlation is 0.25; the resulting **binary** within-clinic ICC is 0.187.
Those are two different numbers and the fixture prints both, because a reader looking for "the ICC"
will find the second and the generator is written in terms of the first.

## The two claims

**Agreement** is between `geepack` and `statsmodels` on the same rows: coefficients, both standard
errors, and the estimated working correlation.

`alpha_exchangeable` is included **deliberately** as the key most likely to differ — the two
packages estimate the working correlation with their own moment estimators and nothing guarantees
those coincide. A check whose keys are chosen to avoid the awkward ones is calibrated against
nothing.

**Recovery** is against the fixture's own marginal log odds ratio, `log(2) = 0.6931`, which is exact
by construction rather than a recording of what this code produced. Tolerance 0.50, measured over
200 alternative seeds fitted with a stdlib IRLS logistic regression that is not one of the library's
engines: miss median 0.1190, 95th percentile 0.3283, maximum 0.3978. The committed seed misses by
0.1205.

**That claim is weak and the entry says so.** 0.50 is most of the effect being estimated. With
exposure allocated largely at the clinic level the effective sample size is closer to 90 clinics
than 2169 patients, and the sampling distribution really is that wide — narrowing the tolerance
would fail correct implementations. What carries this entry is agreement, plus a
sandwich-to-model-based ratio that is a property of the design rather than of the seed.

## What is not in this entry

**A small-sample correction.** Not in `geepack`, and a separate entry.

**A conditional odds ratio.** That is `mixed-effects-logistic-clustered`, and it is a different
parameter rather than a different way of getting this one.

**Any claim that SAS or Stata was run.** Neither was. `must_appear` is the only guard those two
files have, which is why every option above is named in `expected.json`.
