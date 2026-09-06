# Cox proportional hazards regression
#
# Estimates a hazard ratio while conditioning the baseline hazard away, so no shape is assumed for
# it. The proportional hazards assumption is what buys that, and it is an assumption: it should be
# checked (scaled Schoenfeld residuals, cox.zph) rather than asserted.

library(survival)

d <- read.csv("fixture.csv")

# PINNED DEFAULT: ties = "efron". This IS coxph's default, and it is named anyway, because the
# alternatives disagree whenever event times tie and follow-up recorded in whole days or months
# ties constantly. In this fixture 664 of 785 events share a time with another. Breslow is faster
# and biased toward the null with heavy ties; "exact" is the conditional logistic likelihood and
# is slow. A file that leaves this implicit is one package upgrade from changing its answer.
fit <- coxph(Surv(time, event) ~ exposed + covariate, data = d, ties = "efron")

s <- summary(fit)
cat("estimates\n")
print(s$coefficients)
cat("\nproportional hazards check (cox.zph): a small p is evidence AGAINST proportionality\n")
print(cox.zph(fit))

cat("\n--- HARNESS ---\n")
cat(sprintf("exposure_log_hr=%.10f\n", unname(coef(fit)["exposed"])))
cat(sprintf("exposure_se=%.10f\n", sqrt(diag(vcov(fit)))["exposed"]))
cat(sprintf("covariate_beta=%.10f\n", unname(coef(fit)["covariate"])))
cat(sprintf("n_events=%d\n", sum(d$event)))
