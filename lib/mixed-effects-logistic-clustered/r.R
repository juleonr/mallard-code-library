# Mixed-effects logistic regression for a cluster-randomised binary outcome
#
# Estimates a CLUSTER-CONDITIONAL odds ratio: the effect for a given cluster, holding its random
# intercept fixed. That is not the population-average odds ratio a GEE would report. Under a
# nonlinear link the two are genuinely different quantities, not different spellings, and the
# marginal one is attenuated toward 1. Which one answers the question is a choice to be made and
# stated, not an inefficiency to be tolerated.

library(lme4)

d <- read.csv("fixture.csv")

# PINNED DEFAULT: nAGQ. glmer defaults to nAGQ = 1, the Laplace approximation. Adaptive
# Gauss-Hermite quadrature (nAGQ > 1) is more accurate for binary outcomes, and the two give
# different estimates on the same data. Naming it is what makes the number reproducible; it is
# also why this file will not silently change its answer when lme4 changes a default.
fit <- glmer(outcome ~ exposed + (1 | cluster), data = d, family = binomial, nAGQ = 10)

cat("estimates (CLUSTER-CONDITIONAL, not population-average)\n")
print(summary(fit))

vc <- as.data.frame(VarCorr(fit))
sigma_u <- vc$sdcor[vc$grp == "cluster"]

# FEW-CLUSTER WARNING, stated in the output rather than left to the reader. Ordinary sandwich or
# GEE inference is unreliable below about 30 clusters and worse below 15; a random-intercept
# likelihood is better behaved but the between-cluster variance is still poorly estimated.
n_clusters <- length(unique(d$cluster))
if (n_clusters < 30) {
  cat(sprintf("\nNOTE: %d clusters. Below ~30 clusters, name a small-sample approach ",
              n_clusters))
  cat("(CR2, Satterthwaite, Kenward-Roger, cluster-level summaries).\n")
}

cat("\n--- HARNESS ---\n")
cat(sprintf("conditional_log_or=%.10f\n", unname(fixef(fit)["exposed"])))
cat(sprintf("conditional_se=%.10f\n", sqrt(diag(vcov(fit)))["exposed"]))
cat(sprintf("cluster_sd=%.10f\n", sigma_u))
cat(sprintf("n_clusters=%d\n", n_clusters))
