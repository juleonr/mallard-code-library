# Fixed-model validation for an uncensored binary outcome in independent participants.
# predicted is supplied by a model fixed BEFORE these outcomes were inspected.
# Do not fit or tune the prediction model here. Calibration fits EVALUATE predictions;
# they do not replace them. Unweighted complete data only; no censoring or survey weights.
d <- read.csv("fixture.csv")
stopifnot(!anyNA(d), all(d$outcome %in% c(0, 1)),
          all(is.finite(d$predicted)), all(d$predicted > 0 & d$predicted < 1),
          length(unique(d$outcome)) == 2)
d$lp <- qlogis(d$predicted)
# Intercept with slope fixed at 1: calibration-in-the-large.
citl <- glm(outcome ~ 1 + offset(lp), data = d, family = binomial(link = "logit"))
# Joint intercept and slope: perfect population calibration is intercept=0, slope=1.
cal <- glm(outcome ~ lp, data = d, family = binomial(link = "logit"))
stopifnot(citl$converged, cal$converged)
# Empirical AUC, larger predicted values mean outcome=1; average ranks give tied pairs half credit.
n1 <- sum(d$outcome == 1); n0 <- sum(d$outcome == 0)
auc <- (sum(rank(d$predicted, ties.method = "average")[d$outcome == 1]) - n1*(n1+1)/2)/(n1*n0)
brier <- mean((d$outcome - d$predicted)^2)
cat("\n--- HARNESS ---\n")
cat(sprintf("auc=%.10f\nbrier=%.10f\n", auc, brier))
cat(sprintf("calibration_in_large=%.10f\ncalibration_intercept=%.10f\ncalibration_slope=%.10f\n",
            coef(citl)[1], coef(cal)[1], coef(cal)[2]))
cat(sprintf("n=%d\nevents=%d\n", nrow(d), n1))
# These point estimates need uncertainty and a calibration curve in a real evaluation.
# AUC/Brier/calibration alone do not establish clinical net benefit or deployment safety.
