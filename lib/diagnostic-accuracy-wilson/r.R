# Diagnostic accuracy against a reference standard, with Wilson intervals
#
# Sensitivity and specificity are SINGLE PROPORTIONS, which is exactly the case where a Wilson or
# Clopper-Pearson interval is the right choice. The normal-approximation (Wald) interval degrades
# badly near 0 and 1 and can run outside [0, 1], which for an accuracy measure is visibly wrong.
# The same interval must never be attached to an adjusted model estimate.

library(binom)

d <- read.csv("fixture.csv")

tp <- sum(d$disease == 1 & d$test == 1)
fn <- sum(d$disease == 1 & d$test == 0)
tn <- sum(d$disease == 0 & d$test == 0)
fp <- sum(d$disease == 0 & d$test == 1)

# PINNED DEFAULT: method = "wilson". binom.confint returns ELEVEN methods when asked for "all",
# and its own default is "all" -- so a caller who omits method gets a data frame of eleven rows and
# whichever one they index first. Naming it is what makes the reported interval reproducible.
sens <- binom.confint(tp, tp + fn, methods = "wilson")
spec <- binom.confint(tn, tn + fp, methods = "wilson")

cat("2x2 table\n")
print(table(disease = d$disease, test = d$test))
cat("\nsensitivity and specificity, Wilson 95%\n")
print(rbind(sensitivity = sens, specificity = spec))

cat("\n--- HARNESS ---\n")
cat(sprintf("sensitivity=%.10f\n", sens$mean))
cat(sprintf("sensitivity_lcl=%.10f\n", sens$lower))
cat(sprintf("sensitivity_ucl=%.10f\n", sens$upper))
cat(sprintf("specificity=%.10f\n", spec$mean))
cat(sprintf("specificity_lcl=%.10f\n", spec$lower))
cat(sprintf("specificity_ucl=%.10f\n", spec$upper))
cat(sprintf("n=%d\n", nrow(d)))
