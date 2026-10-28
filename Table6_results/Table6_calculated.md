# Table 6. Cluster solution versus effort median split

| Variable | Extended (n=41) | Brief (n=32) | High effort (n=36) | Low effort (n=37) | Cluster d [95% CI] | Median-split d [95% CI] | Cluster effect controlling effort | 95% CI for adjusted b |
|---|---|---|---|---|---|---|---|---|
| Composite effort | 487.46 ± 86.22 | 156.75 ± 84.77 | 508.00 ± 69.66 | 181.46 ± 101.43 | 3.86 [3.07, 4.64] | 3.74 [2.97, 4.51] | N/A | N/A |
| Meaningful comment density | 0.05 ± 0.04 | 0.09 ± 0.07 | 0.05 ± 0.03 | 0.08 ± 0.07 | -0.58 [-1.05, -0.10] | -0.59 [-1.06, -0.12] | b = 0.033, p = 0.247 | [-0.023, 0.089] |
| Round 1 start | 1271.34 ± 685.46 | 596.57 ± 552.52 | 1304.44 ± 696.00 | 655.56 ± 572.60 | 1.07 [0.57, 1.56] | 1.02 [0.53, 1.50] | b = 351.035, p = 0.283 | [-296.628, 998.699] |
| Round 2 retention | 0.92 ± 0.22 | 0.67 ± 0.68 | 0.94 ± 0.19 | 0.69 ± 0.64 | 0.52 [0.05, 0.99] | 0.52 [0.05, 0.99] | b = 0.146, p = 0.556 | [-0.347, 0.638] |
| Mean assignment score (6 columns) | 88.74 ± 9.18 | 69.85 ± 19.79 | 89.02 ± 9.25 | 72.14 ± 19.53 | 1.28 [0.77, 1.78] | 1.10 [0.60, 1.59] | b = 15.000, p = 0.054 | [-0.275, 30.274] |


Values are mean ± sample SD (ddof=1). Cluster labels are the original saved
assignments: Extended=Cluster 1 (41), Brief=Cluster 2 (32). Total effort median=364;
high effort >364 (36), low effort <=364 (37). Cohen's d uses pooled sample SD,
with Extended minus Brief or High minus Low respectively.
Cohen's d is presented as d [95% CI] for each comparison separately. Its
equal-tailed confidence limits are calculated by inverting the noncentral t
distribution with df=n1+n2-2, then multiplying noncentrality limits by
sqrt(1/n1+1/n2). This is a model-based independent-normal-groups, common-variance
interval conditional on the observed assignments. It does not account for
data-driven cluster/median selection or establish independent cluster validity.
Method reference: https://easystats.r-universe.dev/effectsize/effectsize.pdf

Composite effort = sum of the six R1/R2 category-submission counts.
Meaningful comment density = (R1_MF_Count + R2_MF_Count) / Effort_Total.
Round 2 retention = Effort_R2 / Effort_R1; this is a count ratio and can exceed 1,
not a binary retention proportion. All denominators are positive for this ratio.
Round 1 start is the raw R1.Start field; its physical time unit is not established
by the workbook alone. Use 'minutes' only if verified from collection documentation.

The score row reproducing the attached table averages HW1, HW3, HW4, HW5, HW6,
HW7. HW1 and HW2 are identical for all 73 students in these sources; HW2 is
excluded from this six-column sensitivity, not silently corrected in the source.
The source files do not establish whether that identical recording is erroneous.
Stored Mean_HW averages HW1-HW7 and is also reported as a separate sensitivity.
Use the score definition actually adopted in Table 5 consistently across tables.

Adjusted cluster effects use separate OLS models:
Y = intercept + beta_E * Effort_Total + b * I(Cluster=1) + error.
The table reports unstandardized b and conventional two-sided OLS t-test p values
(70 residual degrees of freedom). No Pre covariate, transformation, spline or
multiple-testing correction is applied. HC3 p values and original score-definition
sensitivity are exported separately, not mixed with the attached table's method.
The 95% confidence intervals for b use conventional OLS standard errors and
the t distribution: b +/- t(0.975, 70) * SE(b). They are individual two-sided
intervals, consistent with the table's p values, not simultaneous intervals.
These intervals are for the adjusted cluster coefficients, not the group means
or Cohen's d. N/A for composite effort is intentional.
Regressing composite effort on itself is not meaningful, so its effect is N/A.

These adjusted associations are exploratory. Behavioral variables helped define
the clusters, so these p values are not independent validation of behavioral
types. A positive adjusted density coefficient despite a negative marginal
contrast reflects conditioning on strongly associated effort and cluster variables;
it should not be presented as a robust reversal. Non-significance does not prove
no association. Score coefficients are associations, not causal effects.

Six-column score: b=14.999625, p=0.054149, 95% CI [-0.274731, 30.273980].
Stored seven-column Mean_HW sensitivity: Extended 87.355401±9.481029,
Brief 69.500000±17.472446; High 87.718254±9.430086, Low 71.559846±17.410815;
d=1.316546/1.149664; b=14.014267, conventional p=0.049933, HC3 p=0.050358.
This sensitivity to score definition is important near the 0.05 threshold.

Sources: Merge-Data.xlsx and output-cluster-with-score.xlsx. The latter verifies
all saved labels and plotted behavioral/count inputs by unique student ID.
No clustering is refitted. Reproduce with python Cluster-Analysis/calculate_table6.py.
