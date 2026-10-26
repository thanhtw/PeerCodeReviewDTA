# Does the clustering add information beyond effort magnitude?

**Label-version scope:** The results below concern Merge-Data.xlsx and
output-cluster-with-score.xlsx labels. The later attached Figure R1 uses stored
chart labels that differ for ten students. Its corresponding analysis is in
`../figure_R1_analysis/FIGURE_R1_EXPLANATION.md`. The earlier results remain valid
for their specified partition and must not be attributed to the chart partition.

## Conclusion

The reviewer identifies a substantive issue. In these 73 students, the historical
two-cluster partition predominantly summarizes overall submission effort. It is
not identical to a median split, but that difference is too small to justify a
strong claim of qualitatively distinct behavioral types. Relative allocation
differences exist descriptively. Evidence of incremental score information is
modest, model-dependent and uncertain; it should not be presented as conclusive
validation of the behavioral interpretation. This does not contradict the earlier
gap-statistic result: choosing k=2 and interpreting what the groups represent are
different questions.

## Data and provenance

- `input-data.xlsx`: 73 students, original 14 clustering features.
- `output-cluster-with-score.xlsx`: historical cluster labels; despite the name,
  the main sheet contains behavior and labels rather than homework scores.
- `Merge-Data.xlsx`: HW1–HW7, Mean_HW, Mid, Final, recorded Pre, effort totals and labels.
- Joined by unique student ID. All 73 IDs match, historical labels agree between
  workbooks, and submission/duration values match. Historical Cluster 1 is Extended
  Engagers (41), Cluster 2 is Brief Participants (32). The Python refit reproduces
  historical assignments exactly after orienting groups by effort (ARI=1).
- Effort_Total equals the sum of the six R1/R2 functionality, readability and
  documentation submission columns. It is a submission-volume proxy, not a
  validated measure of all learning effort or quality.
- Individual direct IDs are omitted from the analysis workbook and CV export.

## 1. Direct comparison with simple effort rules

The median Effort_Total is 364. Median split means >364 is high, <=364 is low;
there is one median tie. It gives 36 high and 37 low, whereas the clusters have
41 high and 32 low. A median split necessarily changes group sizes, so also
compare a split that assigns the highest 41 totals to the high group. There is
no tie at that boundary.

| Comparator | Agreement | Disagreements | Adjusted Rand index |
|---|---:|---:|---:|
| Total-submission median split | 68/73 = 93.15% | 5 | 0.741 |
| Six standardized count features: mean-z median split | 68/73 = 93.15% | 5 | 0.741 |
| All 14 standardized features: mean-z median split | 68/73 = 93.15% | 5 | 0.741 |
| Highest 41 submission totals versus remaining 32 | 71/73 = 97.26% | 2 | 0.892 |
| One-dimensional k-means on total effort | 69/73 = 94.52% | 4 | 0.790 |

The median groups are not necessarily identical across the three composite
definitions, despite matching agreement statistics. All14 includes timestamps,
so it is a mechanical comparison, not a validated composite effort scale.
An in-sample threshold search can also reproduce 71/73 assignments; that search
is descriptive, not out-of-sample classification performance. Total effort has
an in-sample AUC of 0.9958 for historical cluster membership. The same-size
comparison is stronger evidence against a special qualitative interpretation
than the observation that a strict median split differs on five students.

The mean homework-score gap is already reproduced closely by simple splits:

| Grouping | High mean | Low mean | Difference |
|---|---:|---:|---:|
| Historical clusters | 87.36 | 69.50 | 17.86 |
| Total-effort median split | 87.72 | 71.56 | 16.16 |
| Size-matched total-effort split | 86.93 | 70.05 | 16.88 |

## 2. PCA and magnitude versus shape

PC1 explains 46.83% of variance in the original 14 standardized features and
correlates strongly with Effort_Total: Pearson r=0.9778, Spearman rho=0.9656.
The first three PCs explain 75.43%, as in the earlier reanalysis. PC1 from the
six count features alone explains 86.51% of their variance.

For the contrast between standardized cluster centroids, 84.22% of its squared
length lies along the common all-features-increase direction. For the six count
features alone, that fraction is 99.95%. This is a geometric decomposition of
the centroid contrast, not variance explained for the entire data or a validity
test. It directly supports the reviewer's concern about similarly shaped profiles.

There are relative allocation differences when proportions are computed within
each student before averaging:

| Within-student proportion | Extended | Brief |
|---|---:|---:|
| Round 2 share of all submissions | 47.22% | 33.28% |
| Functionality share | 17.02% | 23.96% |
| Readability share | 65.95% | 53.62% |
| Documentation share | 17.03% | 22.42% |

These differences show that the raw profiles are not exact scalar multiples.
They do not demonstrate independent qualitative types: composition can vary
systematically along a continuous effort gradient, and these are variables used
to create the clusters. Do not attach ordinary post-selection group-test p values
as if these were independent validation measures. Recording conventions could
also influence the proportions.

To examine what remains after overall effort, each original standardized feature
was regressed on a three-df natural cubic spline of log(1+Effort_Total). We then
compared cluster means of standardized residuals descriptively. The six submission
contrasts fall from 1.61–1.71 SD to absolute differences <=0.058 residual SD. The
largest residual contrast across all 14 features is 0.237 SD (Round 2 end time).
This is strong descriptive evidence that most separation follows magnitude.
Residualization is not independent proof of absent types and is sensitive to
the chosen effort model.

Figures:
- `magnitude_vs_shape`: original feature means and within-student centered z profiles.
  Removing each student's mean z score removes one common direction, not every
  possible effort effect; do not overinterpret apparent residual shape.
- `effort_adjusted_contrasts`: original differences versus differences after smooth effort adjustment.
- `relative_allocation`: within-student proportions, with no significance claim.
- `effort_cluster_score`: PC1 and homework score against total effort.

## 3. Do scores supply incremental evidence?

The primary adjusted specification adds the historical high-cluster indicator
to a natural cubic spline of log(1+Effort_Total), three df, plus the recorded
Pre score. OLS uses HC3 standard errors and t-based confidence intervals.

| Outcome | Adjusted cluster coefficient | 95% CI | HC3 p | Added in-sample R² |
|---|---:|---|---:|---:|
| Mean_HW | +15.34 | -3.82 to 34.51 | 0.115 | 0.040 |
| Mid | +15.54 | -19.72 to 50.80 | 0.382 | 0.020 |
| Final | +15.28 | -21.35 to 51.91 | 0.408 | 0.018 |

Holm-adjusted p values for this three-outcome family are 0.344, 0.764 and 0.764.
**The estimated association does not disappear:** it remains positive but is
imprecise. Non-significance is not proof of equivalence or no added value.
Effort ranges overlap only from 293 to 342, with two Extended and five Brief
students in that interval. This limited overlap makes cluster/effort separation
weakly identified and dependent on functional form.

Functional-form sensitivity must be reported: for Mean_HW with Pre adjustment,
the cluster coefficient is +13.86 (p=0.059) under raw-linear effort,
+19.58 (p=0.0039) under log-linear effort, and +15.34 (p=0.115) under the more
flexible log-effort spline. Thus, claiming a robust independent contribution by
highlighting only the significant log-linear model would be misleading. Pre's
meaning and timing must be confirmed before interpreting it as baseline attainment.

## 4. Internal predictive comparison

We used 20 repetitions of five-fold cross-validation with shared folds across
models. Within every training fold, feature standardization, PCA, k-means,
cluster orientation, effort median and spline basis were refitted; held-out
students were then transformed and assigned to the training-derived clusters.
Scores were not used to derive clusters. K=2 was fixed from the prior analysis.
All rows in this table additionally include the recorded Pre score. Lower RMSE
is better, in score points.

| Model | Mean_HW RMSE | Mid RMSE | Final RMSE |
|---|---:|---:|---:|
| Raw continuous effort | 14.10 | 23.84 | 24.33 |
| Effort median split | 13.90 | 24.01 | 24.31 |
| Effort-only k-means split | 14.18 | 23.99 | 24.47 |
| PCA + two-cluster indicator | 13.74 | 23.75 | 24.30 |
| Flexible continuous effort spline | 14.69 | 24.32 | 24.76 |
| Flexible effort spline + cluster | 14.51 | 24.65 | 25.13 |

The cluster indicator alone is slightly better than the simple median split,
but only by 0.16 homework points in RMSE; the exam differences are also small.
This may reflect an adaptive cut along magnitude, rather than distinct types.
Adding clusters to flexible continuous effort improves homework RMSE by 0.18
points but worsens both exam RMSEs. The homework improvement varies from -0.61
to +0.90 across repeats and occurs in 15/20 repeats. Repeats overlap and are not
independent replicates for a significance test. These results support, at most,
modest internal predictive benefit, not reliable general superiority. The spline
is an adjustment sensitivity, not a claim that it is the best predictive baseline;
the simpler raw-linear and median baselines perform better than it here.

No-Pre results and every tested specification are available in the CSV/workbook.
This is internal, retrospective validation, not external or prospective evidence.
Scores may overlap temporally with the behavior window, so avoid causal or
prospective prediction claims without establishing measurement timing.

## 5. Source-data issues and score sensitivity

HW1 and HW2 are identical for all 73 students. Mean_HW equals the mean of seven
stored columns, giving that identical column twice the weight of each remaining
column. This may reflect genuinely equal recorded scores or an export problem;
the project files alone do not establish which. No source workbook was changed.
Sensitivity analysis averages HW1 and HW3–HW7 (six distinct stored columns).
With Pre adjustment, its spline-model cluster coefficient is +16.40 (95% CI
-5.36 to 38.16, p=0.137), and adding clusters changes CV RMSE from 16.47 to
16.35. The interpretation remains modest/uncertain incremental value.

Four students have zero Round 2 submission totals; one has one recorded MF event.
The stored R2 MF ratios at zero effort are [0, 1, 0, 0]. A MF/submission ratio is
undefined for those students, so our ratio summary excludes them instead of
using those stored values. Do not quote the stored ratio means as validated
normalized rates. This does not affect total-effort, cluster or score models.

## Recommended revision

1. Acknowledge that clustering mainly operationalizes high versus low effort.
   Consider names such as Higher- and Lower-Submission Engagement groups; duration
   has large outliers, so 'Extended' should not imply uniformly longer activity.
2. Present continuous effort as the main explanatory dimension; retain clusters
   as a descriptive summary if useful, not as established natural behavioral types.
3. Add the agreement table and predictive comparison; replace or supplement the
   radar with magnitude-adjusted feature contrasts and relative allocation.
4. Report positive but uncertain adjusted score associations and functional-form
   sensitivity. Do not claim that adjusted differences vanish or that scores
   independently validate the partition.
5. Resolve HW1/HW2 provenance before finalizing score claims. Keep the six-column
   sensitivity analysis until that is resolved.

## Reproduction and verification

Run `python Cluster-Analysis/effort_profile_analysis.py` from the project root.
Outputs include all student-level held-out predictions (without direct IDs),
model estimates, comparisons, plots, input hashes and software versions.
Seven unit tests pass across the cluster-selection and effort-analysis suites.
CV results were checked for exactly one held-out prediction per student/model/
outcome/repeat and complete coverage of all 73 students per repeat.

Methods references: [ARI and clustering comparisons](https://scikit-learn.org/stable/modules/clustering.html#clustering-performance-evaluation),
[train-only preprocessing](https://scikit-learn.org/stable/common_pitfalls.html),
and [HC3 covariance](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html).
