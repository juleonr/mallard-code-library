# Competing risks: the cumulative incidence function
#
# THE ONE THING THIS ENTRY IS FOR. A Kaplan-Meier curve for cause 1 treats a death from the
# competing cause as CENSORING -- as though that patient could still go on to have cause 1, when
# they cannot. It therefore OVERSTATES cumulative incidence, and the overstatement grows with the
# competing hazard. On this fixture, at 36 months, the naive curve says 0.65 where the truth is
# 0.34. It nearly doubles it.
#
# Both estimators are computed below, side by side, because the number that matters is the gap.

library(survival)

d <- read.csv("fixture.csv")

# PINNED: status is a FACTOR, which is what makes this a multi-state fit and gives the
# Aalen-Johansen estimator. Surv(time, status) with a numeric status is a two-state model in which
# every non-zero code is "the event", so cause 2 would silently be counted as cause 1. Surv(time,
# status == 1) is the OTHER silent error -- it treats cause 2 as censoring, which is the naive
# curve below. Neither of those two spellings warns you.
d$state <- factor(d$status, levels = c(0, 1, 2),
                  labels = c("event-free", "cause1", "cause2"))
aj <- survfit(Surv(time, state) ~ 1, data = d)

# THE NAIVE CURVE, computed ON PURPOSE so the gap is a number in the output rather than a warning
# in a comment. This is the line to delete from your own analysis, not to copy.
naive <- survfit(Surv(time, status == 1) ~ 1, data = d)

at <- function(fit, t, col) summary(fit, times = t)$pstate[, col]
cat("cumulative incidence of cause 1 (Aalen-Johansen), and the naive 1 - KM beside it\n")
for (t in c(12, 24, 36)) {
  cat(sprintf("  t=%2d   CIF %.6f   1-KM %.6f   the naive curve overstates by %.6f\n",
              t, at(aj, t, "cause1"), 1 - summary(naive, times = t)$surv,
              (1 - summary(naive, times = t)$surv) - at(aj, t, "cause1")))
}

cat("\n--- HARNESS ---\n")
cat(sprintf("cif1_12=%.10f\n", at(aj, 12, "cause1")))
cat(sprintf("cif1_24=%.10f\n", at(aj, 24, "cause1")))
cat(sprintf("cif1_36=%.10f\n", at(aj, 36, "cause1")))
cat(sprintf("naive_incidence_36=%.10f\n", 1 - summary(naive, times = 36)$surv))
cat(sprintf("n_cause1=%d\n", sum(d$status == 1)))
cat(sprintf("n_cause2=%d\n", sum(d$status == 2)))
cat(sprintf("n=%d\n", nrow(d)))
