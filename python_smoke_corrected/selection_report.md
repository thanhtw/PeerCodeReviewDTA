# Cluster selection: computed Python reanalysis

Input: Merge-Data.xlsx; profile: alternative-corrected; complete observations: 73.
Three PCs retain 67.94% of standardized variance.
B=2, seed=42, d.power=1, scaledPCA reference box.

Recommendations: {"Tibs2001SEmax": 2, "firstSEmax": 2, "globalmax": 3, "silhouette": 2}. Primary selection: k=2.

Tibshirani's rule selects the smallest k satisfying Gap(k) >= Gap(k+1) - s(k+1).
s(k) = sqrt(1 + 1/B) * sample_SD(reference log W(k)); it is not SD/sqrt(B).
The CSV includes every adjacent comparison and its margin; the final k has no
next-k comparison. Selection at the upper boundary requires extending the range.

First comparisons:
 k      gap   SE_sim  next_gap_minus_SE  decision_margin
 1 0.366997 0.055966           0.402845        -0.035848
 2 0.416693 0.013848           0.402038         0.014654
 3 0.420855 0.018816           0.367526         0.053329

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
