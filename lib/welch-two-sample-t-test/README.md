# Two-sample comparison of means with unequal variances (Welch)

Compares two arms' means without assuming they have the same spread.

## The default this entry exists to pin

| Language | What the shortest correct-looking line runs |
|---|---|
| R | `t.test(x, y)` — **Welch** |
| Python | `ttest_ind(x, y)` — **pooled**, because `equal_var=True` is scipy's default |
| Stata | `ttest y, by(arm)` — **pooled** |
| SAS | `proc ttest` prints **both**, Pooled first |

So the same analysis written the obvious way in two languages is two different tests. R is the only
one of the four whose default is Welch, and this entry names the option in R anyway.

**SAS is the one language here that cannot pin it**, which is worth stating rather than papering
over. PROC TTEST prints the Pooled and Satterthwaite rows together with a folded F test, nothing is
defaulted and nothing can be switched off. The choice is made by which row the reader's eye lands
on, and the wrong one is printed first. The file says to read the Satterthwaite row.

## Why the smaller arm is the more variable one

The fixture is 1200 controls with sd 2 against 400 treated with sd 5, and that direction is
deliberate.

When the **smaller** group has the **larger** variance, the pooled test is anti-conservative: here
it reports a standard error 32% too small — 0.1753 against Welch's 0.2563 — and a t of 5.81 where
Welch gives 3.97. It manufactures significance. Reverse the two arms and the pooled test is merely
conservative: it loses power without inventing findings.

A fixture built the safe way round would exercise the same arithmetic and demonstrate the harmless
failure. This shape is also the ordinary clinical one: a small treated arm in which the drug helps
some patients a great deal and others not at all, against a large stable control arm.

The rows are shuffled, so an implementation that reads "the first 1200 rows" instead of the `arm`
column fails visibly rather than by luck.

## An option next to the right one that is not a synonym

Stata has both `unequal` and `welch`. They are different degrees-of-freedom formulas, not two names
for one thing: `unequal` is Satterthwaite, which is what R and scipy use, and `welch` is Welch's
1947 approximation. On this fixture they give 442.16 and 442.37 — a fifth of a degree of freedom out
of 442, which changes nothing. They separate in small samples, which is the only place anyone reads
the df at all. `unequal` is the option that matches the other three languages.

## The variance test is not a gate

SAS prints a folded F test of equal variances beside the two rows and it is easy to read as an
instruction: test first, then choose. That is a two-stage procedure whose overall error rate is not
the nominal one, and the pre-test is itself unreliable at the sample sizes where the choice matters
most. Where the arms are not known to have equal spread, Welch is the default worth having.

## The two claims, and which one carries this entry

**Agreement is the strong one.** Pooled against Welch is 8.1e-2 on the standard error, eight hundred
times the 1e-4 tolerance, and 1598 against 442 on the degrees of freedom. An engine that silently
ran the pooled test could not hide in the rounding.

**Recovery is the weak one, and that is a property of the comparison rather than of the code.** The
tolerance is 0.8 against a true difference of 1.0, so it would pass an estimate of 0.3. The treated
arm has a standard deviation five times the effect and 400 patients; no sample of this size pins the
difference tightly. Measured over 300 alternative seeds, `|estimate − 1.0|` had a median of 0.17, a
95th percentile of 0.51 and a maximum of 0.70. The committed seed's miss is 0.018.

## What is not in this entry

**Analysis of variance**, though it shares the Learn page. A k-group comparison is a separate fixture
and a separate default worth pinning — R's `oneway.test` does not assume equal variance while `aov`
does — and folding it in would give one entry two estimands.

**The paired comparison.** Where the two measurements are on the same participant, neither test here
applies.
