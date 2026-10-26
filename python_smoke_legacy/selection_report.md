# Cluster selection: computed Python reanalysis

Input: Merge-Data.xlsx; profile: alternative-legacy; complete observations: 73.
Three PCs retain 69.96% of standardized variance.
B=2, seed=42, d.power=1, scaledPCA reference box.

Recommendations: {"Tibs2001SEmax": 2, "firstSEmax": 2, "globalmax": 3, "silhouette": 2}. Primary selection: k=2.

Tibshirani's rule selects the smallest k satisfying Gap(k) >= Gap(k+1) - s(k+1).
s(k) = sqrt(1 + 1/B) * sample_SD(reference log W(k)); it is not SD/sqrt(B).
The CSV includes every adjacent comparison and its margin; the final k has no
next-k comparison. Selection at the upper boundary requires extending the range.

First comparisons:
 k      gap   SE_sim  next_gap_minus_SE  decision_margin
 1 0.362910 0.057386           0.396175        -0.033266
 2 0.409389 0.013213           0.393873         0.015515
 3 0.414495 0.020622           0.362766         0.051729

The original R scripts use firstSEmax by default and ultimately select silhouette's
recommendation. The Python primary rule is explicitly Tibs2001SEmax. This change
must be described as a reanalysis, not retrospectively attributed to the original.
These results are not the exact numerical data underlying the supplied Figure 4:
R/Python random generators, k-means solvers and Monte Carlo draws differ.
Overlapping gap bars neither constitute a pairwise significance test nor establish
that the clusters are unstable. The adjacent 1-SE comparison favors parsimony.
Initialization ARI results assess optimizer sensitivity only; they do not establish
sampling stability, external validity, or the existence of discrete populations.
See ../CLUSTER_SELECTION.md for reviewer wording and interpretation.
