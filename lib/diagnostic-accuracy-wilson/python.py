# Diagnostic accuracy against a reference standard, with Wilson intervals
#
# The Python equivalent of the R file beside this one. The two use INDEPENDENT implementations of
# the Wilson interval -- binom::binom.confint and statsmodels.proportion_confint -- rather than the
# same formula typed twice, which is what makes their agreement worth anything.

import pandas as pd
from statsmodels.stats.proportion import proportion_confint

d = pd.read_csv("fixture.csv")

tp = int(((d.disease == 1) & (d.test == 1)).sum())
fn = int(((d.disease == 1) & (d.test == 0)).sum())
tn = int(((d.disease == 0) & (d.test == 0)).sum())
fp = int(((d.disease == 0) & (d.test == 1)).sum())

sensitivity = tp / (tp + fn)
specificity = tn / (tn + fp)

# PINNED DEFAULT: method="wilson". proportion_confint defaults to "normal", the Wald interval,
# which is the one that misbehaves near 0 and 1 and can leave [0, 1] entirely.
sens_lcl, sens_ucl = proportion_confint(tp, tp + fn, alpha=0.05, method="wilson")
spec_lcl, spec_ucl = proportion_confint(tn, tn + fp, alpha=0.05, method="wilson")

print(f"2x2 table  TP={tp} FP={fp} FN={fn} TN={tn}")
print(f"sensitivity {sensitivity:.4f} ({sens_lcl:.4f} to {sens_ucl:.4f})")
print(f"specificity {specificity:.4f} ({spec_lcl:.4f} to {spec_ucl:.4f})")

print("\n--- HARNESS ---")
print(f"sensitivity={sensitivity:.10f}")
print(f"sensitivity_lcl={sens_lcl:.10f}")
print(f"sensitivity_ucl={sens_ucl:.10f}")
print(f"specificity={specificity:.10f}")
print(f"specificity_lcl={spec_lcl:.10f}")
print(f"specificity_ucl={spec_ucl:.10f}")
print(f"n={len(d)}")
