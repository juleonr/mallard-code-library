# An average treatment effect by inverse-probability-of-treatment weighting.
#
# THE POINT ESTIMATE IS THE EASY PART. Every default standard error on this fit is wrong, and each
# one is wrong in a different way, which is what this entry exists to pin.
#
# 1. STABILIZED WEIGHTS. The unstabilized weight is 1/e(L) for the treated and 1/(1-e(L)) for the
#    untreated; the stabilized one multiplies by the marginal P(A=a). Both estimate the same ATE.
#    Stabilized weights average to about 1, which is a DIAGNOSTIC -- mean_stabilized_weight is a
#    harness key for exactly that reason -- and they keep the variance smaller. This file pins the
#    stabilized form and reports the mean so a reader can see the check rather than take it.
#
# 2. THE OUTCOME MODEL IS A WEIGHTED LINEAR MODEL ON A BINARY OUTCOME, ON PURPOSE. Its coefficient
#    on `treated` IS the weighted risk difference. Fitting a weighted LOGISTIC model here would
#    estimate a marginal odds ratio, which is a different quantity, and `weights=` would then mean
#    something else again -- see 4.
#
# 3. THE STANDARD ERROR HAS TO BE THE SANDWICH. The model-based error from a weighted fit treats
#    the weights as if they were known precision, which they are not: they are estimated, and the
#    observations are not independent draws with those variances. `sandwich::vcovHC(type = "HC0")`
#    is the defensible one here.
#
#    IT IS STILL CONSERVATIVE, and the file says so rather than implying the interval is exact:
#    it ignores that e(L) was ESTIMATED. Accounting for that (an M-estimation stack, or a
#    bootstrap of the whole two-stage procedure) narrows it. Conservative is the safe direction and
#    is not the same as right.
#
# 4. `weights =` IN R MEANS DIFFERENT THINGS BY FAMILY, and this is the trap that has no harness
#    key because it does not survive as a number. For `gaussian` it is a PRIOR PRECISION weight,
#    which is what is wanted here. For `binomial` with a 0/1 response it is the NUMBER OF TRIALS --
#    a count -- so `glm(y ~ a, family = binomial, weights = w)` warns "non-integer #successes" and
#    reports a standard error computed as though the study had sum(w) participants. statsmodels
#    splits the two into `var_weights` and `freq_weights` and makes you choose. Same argument name,
#    same intent, two different variances.

library(sandwich)

d <- read.csv("fixture.csv")

# Stage one: the propensity model. Its job is BALANCE, not prediction -- a propensity model chosen
# to maximise discrimination can be worse for the estimate than one that is merely correct.
ps_fit <- glm(treated ~ L, data = d, family = binomial(link = "logit"))
e <- fitted(ps_fit)

p_treat <- mean(d$treated)
w <- ifelse(d$treated == 1, p_treat / e, (1 - p_treat) / (1 - e))

# Stage two. gaussian(identity) on a 0/1 outcome, so the coefficient is a RISK DIFFERENCE.
out <- glm(outcome ~ treated, data = d, family = gaussian(link = "identity"), weights = w)

se_model <- sqrt(diag(vcov(out)))[["treated"]]
se_robust <- sqrt(diag(vcovHC(out, type = "HC0")))[["treated"]]

# The same regression with the weights thrown away, to put a number on what the weighting bought.
crude <- glm(outcome ~ treated, data = d, family = gaussian(link = "identity"))

cat("--- HARNESS ---\n")
cat(sprintf("ate_iptw=%.10f\n", coef(out)[["treated"]]))
cat(sprintf("ate_se_robust=%.10f\n", se_robust))
cat(sprintf("ate_se_model=%.10f\n", se_model))
cat(sprintf("ate_crude=%.10f\n", coef(crude)[["treated"]]))
cat(sprintf("ps_beta_L=%.10f\n", coef(ps_fit)[["L"]]))
cat(sprintf("mean_stabilized_weight=%.10f\n", mean(w)))
cat(sprintf("max_stabilized_weight=%.10f\n", max(w)))
cat(sprintf("n=%d\n", nrow(d)))
