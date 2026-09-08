# Marginal logistic regression by GEE, on binary outcomes clustered within clinic.
#
# THREE THINGS ARE PINNED HERE AND EVERY ONE OF THEM IS A DEFAULT SOMEWHERE ELSE.
#
# 1. corstr = "exchangeable". geeglm DEFAULTS TO "independence", and so do statsmodels and SAS's
#    PROC GENMOD. Stata's xtgee defaults to EXCHANGEABLE. So the same analysis written in four
#    languages fits two different working correlations depending on which one you started from,
#    and no output says which.
#
# 2. The data are SORTED BY CLUSTER. geeglm requires observations from one cluster to be
#    contiguous; it does not check, and unsorted input is silently treated as many small clusters.
#    That is the failure mode this file guards against by sorting unconditionally, even though the
#    committed fixture already arrives sorted.
#
# 3. BOTH standard errors are reported. geeglm's summary prints the sandwich; Stata's xtgee prints
#    the MODEL-BASED one unless you ask for vce(robust). On this fixture they differ by 78%, so a
#    file translated between the two produces an interval that is 44% too narrow while reporting
#    the same estimate.

library(geepack)

d <- read.csv("fixture.csv")
d <- d[order(d$clinic), ]

fit <- geeglm(outcome ~ exposed + x, id = clinic, data = d,
              family = binomial(link = "logit"), corstr = "exchangeable")

# vbeta is the sandwich, vbeta.naiv the model-based variance. Taken from the fitted object rather
# than from summary(), because summary() prints one of them and the entry needs both.
se_robust <- sqrt(diag(fit$geese$vbeta))
se_naive <- sqrt(diag(fit$geese$vbeta.naiv))
nm <- names(coef(fit))

ind <- geeglm(outcome ~ exposed + x, id = clinic, data = d,
              family = binomial(link = "logit"), corstr = "independence")

cat("--- HARNESS ---\n")
cat(sprintf("exposure_log_or=%.10f\n", coef(fit)[["exposed"]]))
cat(sprintf("exposure_se_robust=%.10f\n", se_robust[which(nm == "exposed")]))
cat(sprintf("exposure_se_naive=%.10f\n", se_naive[which(nm == "exposed")]))
cat(sprintf("covariate_beta=%.10f\n", coef(fit)[["x"]]))
cat(sprintf("exposure_log_or_independence=%.10f\n", coef(ind)[["exposed"]]))
cat(sprintf("alpha_exchangeable=%.10f\n", fit$geese$alpha))
