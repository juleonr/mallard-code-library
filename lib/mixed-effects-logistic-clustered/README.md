# Mixed-effects logistic regression for clustered binary outcomes

Estimates a **cluster-conditional** odds ratio with a random intercept per cluster.

## There is no `python.py` here, and that is the answer rather than a gap

The standard Python stack has no frequentist GLMM equivalent to `lme4::glmer`. Three candidates
exist and each was rejected for a specific reason:

| Candidate | Why not |
|---|---|
| `statsmodels` `BinomialBayesMixedGLM` | Variational Bayes: a different estimator targeting a different thing. Agreement with `glmer` would be meaningless either way. |
| `statsmodels` `GEE` | A **population-average** model. It targets an attenuated quantity, not the same number by another route. |
| `pymer4` | Wraps `lme4` through `rpy2`, so it *is* R. Two calls to one engine agreeing is not independent evidence. |

So this entry makes the **recovery** claim only, and `harness/check.py` refuses to state the
agreement claim with fewer than two engines. The weaker guarantee is reported as weaker.

Substituting GEE to make the entry look complete would have been the worst option available: it
would silently swap the estimand, and the agreement check would then compare two different
parameters and report the gap as a defect.

## Conditional is not marginal

A mixed model answers "what is the effect for a given cluster". A GEE answers "what is the effect
averaged over the population". Under a nonlinear link those are **different quantities, not
different spellings**, and the marginal one is attenuated toward 1.

The fixture shows it without needing either model: the crude **marginal** odds ratio is **1.379**
against a true **conditional** odds ratio of **2.000**.

Which one answers your question is a choice to make and state. It is not an inefficiency to be
tolerated, and it is why "mixed-effects versus GEE" is one of the five comparisons in the Learn
plan.

## The fixture

40 clusters of 30, exposure allocated **at the cluster level**, latent-scale ICC 0.163.

Cluster-level allocation is deliberate. With individual-level exposure inside clusters the random
effect is nearly orthogonal to it, and an analysis that ignored clustering entirely would still
land near the truth: the fixture would not test what the entry is for.

## Sizing

`calc: "simulation"`. A clustered design is sized by simulation, not a closed form, and reporting
an unclustered two-group formula or a per-variable floor as *the* method for a clustered design is
a documented error. The alternative to a wrong number is no number.

## Verification

| Engine | Status |
|---|---|
| R (`lme4`) | executed in CI |
| Python | **not applicable** — see above |
| SAS | not executed |
| Stata | not executed |
