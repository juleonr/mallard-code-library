# Modified Poisson regression for an adjusted RISK RATIO (Zou 2004)
#
# Logistic regression gives an odds ratio, which for a common outcome is not a risk ratio and is
# not collapsible. Fitting a log-link Poisson to binary data returns the risk ratio directly; the
# model is misspecified for the variance, which is why a ROBUST variance is mandatory rather than
# optional. Without it the standard errors are conservative to the point of uselessness.

library(sandwich)
library(lmtest)

d <- read.csv("fixture.csv")

fit <- glm(outcome ~ exposed + covariate, family = poisson(link = "log"), data = d)

# PINNED DEFAULT, AND THE MOST IMPORTANT LINE IN THIS FILE.
# sandwich::vcovHC defaults to type = "HC3". Zou's method is the ordinary sandwich, HC0. The two
# differ by a finite-sample correction and give different standard errors on the same fit, so a
# file that omits `type` silently reports a different interval than the method it cites.
V <- vcovHC(fit, type = "HC0")

ct <- coeftest(fit, vcov. = V)
cat("estimates (log scale, HC0 robust)\n")
print(ct)

cat("\n--- HARNESS ---\n")
cat(sprintf("exposure_log_rr=%.10f\n", unname(coef(fit)["exposed"])))
cat(sprintf("exposure_se=%.10f\n", sqrt(diag(V))["exposed"]))
cat(sprintf("covariate_beta=%.10f\n", unname(coef(fit)["covariate"])))
cat(sprintf("n=%d\n", nrow(d)))
