# Draft response: effort magnitude versus qualitative profiles

**Label-version scope:** This response analyzes the historical labels in
Merge-Data.xlsx/output-cluster-with-score.xlsx. The subsequently supplied Figure
R1 uses chart-workbook labels that differ for ten students. Its 11-disagreement
result and feature configuration are documented in
`figure_R1_analysis/FIGURE_R1_EXPLANATION.md`; do not mix the two analyses.

Use the following after incorporating the supplementary analyses and revising
the manuscript's interpretation. The study results below have been computed;
the manuscript itself has not been edited in this workspace.

Thank you for this important observation. We agree that our original description
did not sufficiently distinguish overall engagement magnitude from differences
in relative behavioral emphasis. We have therefore compared the original
two-cluster solution with simple effort-based groupings and examined whether
clustering contributes information beyond a continuous effort measure.

We defined total effort as the sum of the six submission-count features across
the two review rounds. Among the 73 students, a median split of this total agreed
with the original clusters for 68 students (93.2%; adjusted Rand index=0.741).
Because the median split produces different group sizes, we also compared an
effort split with the same 41/32 group sizes as the original clusters. This
reproduced 71 assignments (97.3%; adjusted Rand index=0.892). Furthermore, the
first principal component correlated strongly with total effort (r=0.978).
These findings support the reviewer's interpretation that the dominant
separation reflects engagement magnitude.

We also examined relative allocation using within-student proportions.
Extended Engagers allocated, on average, 47.2% of their submissions to Round 2,
compared with 33.3% for Brief Participants; their readability shares were 65.9%
and 53.6%, respectively. Thus, the groups are not exact scalar multiples.
However, these contrasts are descriptive and derive from features used to
construct the clusters. After removing a smooth relationship with total effort,
the absolute residual contrasts in the six submission features were all below
0.06 residual standard deviations. We therefore do not regard the relative
allocation differences as sufficient evidence of distinct behavioral types
independent of overall effort.

To examine external associations, we modeled homework and examination scores
using continuous effort, with and without the cluster indicator, and conducted
20 repetitions of five-fold cross-validation. Scaling, PCA and clustering were
refitted within each training fold. With the recorded Pre score included, the
cluster model had a mean-homework RMSE of 13.74, compared with 13.90 for an
effort-median-split model and 14.10 for raw continuous effort. This improvement
over the median split was small. Adding the cluster indicator to a flexible
continuous-effort model changed homework RMSE from 14.69 to 14.51, but worsened
midterm and final-examination RMSE. In the corresponding adjusted association
model, the homework cluster coefficient remained positive but imprecise
(+15.34 points, 95% CI -3.82 to 34.51; HC3 p=0.115). Its inference was sensitive
to the functional form used for effort. We therefore find limited evidence of
consistent incremental value beyond effort magnitude, rather than evidence
that the cluster contribution is definitively absent.

Accordingly, we have moderated our interpretation: the clusters are useful as
a parsimonious summary of predominantly higher- and lower-effort engagement,
with some descriptive variation in relative allocation. We no longer present
them as established qualitatively distinct behavioral profiles or claim clear
predictive superiority over simple effort measures. We have added the effort
split comparisons and effort-adjusted profile analysis to make this limitation
explicit. The gap-statistic support for k=2 is retained as evidence concerning
partition size, not as proof that the resulting groups represent distinct types.

## Suggested manuscript addition

“The two-cluster solution predominantly reflected overall engagement magnitude.
It agreed with a total-submission median split for 93.2% of students and with a
group-size-matched effort split for 97.3%; PC1 correlated 0.978 with total
submissions. Although within-student allocation differed descriptively across
groups, effort-adjusted submission-feature contrasts were small. Internal
cross-validation showed only a small homework-score advantage over a median
split, and adding clusters to a flexible continuous-effort model did not improve
examination prediction. We therefore interpret the groups as descriptive effort
strata rather than established distinct behavioral types. Adjusted score
associations were uncertain and sensitive to effort specification.”

## Before final submission

- Confirm what Pre represents and when it was measured. Until confirmed, call it
  the recorded Pre score rather than baseline achievement.
- Resolve why HW1 and HW2 are identical for all students. A six-distinct-column
  homework sensitivity analysis is already supplied and yields the same cautious
  interpretation: adding clusters changes adjusted CV RMSE from 16.47 to 16.35;
  the adjusted coefficient is +16.40 (95% CI -5.36 to 38.16).
- Do not state that the adjusted homework difference disappears: the point
  estimate remains positive, with wide uncertainty. Only seven students lie in
  the overlapping effort range between clusters.
- Do not use behavioral-feature significance tests as independent validation:
  these features defined the clusters.
- Do not claim that manuscript edits have already been made until they are.

Numerical evidence: `effort_profile_results/effort_comparison_results.xlsx` and
the accompanying `ANALYSIS_REPORT.md`, CSVs, metadata and figures.
