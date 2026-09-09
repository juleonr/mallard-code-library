# One-stage stratified PSU survey, WR Taylor-linearized variance; NO replicate weights/FPC.
# Complete data only. Use survey-provider methods for actual released data and missingness.
library(survey)
d <- read.csv("fixture.csv")
stopifnot(!anyNA(d), all(d$weight > 0), all(d$outcome %in% c(0,1)), all(d$domain %in% c(0,1)))
options(survey.lonely.psu = "fail")
# PSU numbers repeat between strata: nest=TRUE is required. Declare ALL rows first.
design <- svydesign(ids = ~psu, strata = ~stratum, weights = ~weight, nest = TRUE, data = d)
overall <- svymean(~outcome, design, na.rm = FALSE)
domain_design <- subset(design, domain == 1)
domain_result <- svymean(~outcome, domain_design, na.rm = FALSE)
# Point estimates and design-based SEs only. Plan the provider's interval/reliability criteria.
cat("\n--- HARNESS ---\n")
cat(sprintf("prevalence=%.10f\nprevalence_se=%.10f\n", coef(overall)[1], SE(overall)[1]))
cat(sprintf("domain_prevalence=%.10f\ndomain_prevalence_se=%.10f\n", coef(domain_result)[1], SE(domain_result)[1]))
cat(sprintf("n=%d\npsus=%d\nstrata=%d\n", nrow(d), nrow(unique(d[c("stratum", "psu")])), length(unique(d$stratum))))
