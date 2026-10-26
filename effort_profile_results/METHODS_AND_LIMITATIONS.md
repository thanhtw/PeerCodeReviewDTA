# Interpretation and methods

Historical labels: Cluster 1 = Extended Engagers (41); Cluster 2 = Brief Participants (32).
All workbooks are joined by unique student ID, never row order. Original Python cluster
numbers are arbitrary; agreement is assessed after orienting groups by effort.

Effort_Total is the sum of six submission count columns. Median splits use >median;
ties at the median are assigned low. The same-size split selects the highest 41
totals, with no tie at the cutpoint. Best threshold is searched IN SAMPLE and is
descriptive, not validated classification accuracy. AUC is also descriptive here.
Composite14 is the mean of all 14 feature z scores; it includes timestamps and
is not interpreted as a validated effort scale. Composite_counts uses six counts.

Relative count shares are calculated per student before averaging, not by dividing
pooled group totals. Shape displays subtract each student's mean standardized
feature value. Standardized centroid magnitude fraction is squared projection of
the two-centroid contrast onto the all-ones direction divided by squared contrast
length. It is a geometric descriptive measure, not percent of students explained.
Behavioral contrasts and effort-adjusted residual contrasts are descriptive: the
same variables generated the clusters, so ordinary group-comparison p values would
not establish independent evidence of behavioral types. Proportions are dependent
and may reflect recording conventions as well as behavior. Timing values are not
given an assumed earlier-is-better or later-is-better interpretation.
For four students the Round 2 submission total is zero, making MF/submission
undefined; these four ratios are excluded, not set to zero or one. The stored
Merge-Data.xlsx ratio uses zero or one for these cases and is not used here.

Score models: historical cluster indicator added to raw-linear, log-linear, or
natural cubic spline (3 df, centered) continuous effort, with/without recorded Pre.
HC3 standard errors, t-based 95% CIs. Holm adjustment covers Mean_HW, Mid, Final
within each specification. HW_unique_sensitivity excludes HW2 because HW1=HW2 for
every student. This is sensitivity, not a correction of unverified source data.
Pre is included as a recorded pre-score covariate; its timing/meaning must be
verified before calling it baseline attainment. The adjusted coefficient is an
association, not a causal effect or proof of cluster validity. Almost-disjoint
effort ranges limit overlap and make adjusted coefficients model-dependent.

Predictive comparison: repeated 5-fold CV, same folds for every model. All scaling,
PCA (3 PCs), k-means (k=2, 25 starts), cluster orientation, median cutpoints and
spline transforms are fitted on training data only. No homework/exam outcome is
used for clustering. Score regressions are then fitted on training data and used
to predict held-out students. K=2 is fixed from the earlier study, not selected
again per fold. These CV labels are training-derived and not the fixed historical
labels. Aggregate RMSE pools squared errors across repeats/students; per-repeat
RMSE differences are sensitivity summaries, not independent observations for a
t-test. No test-set hyperparameter selection is performed. This is internal
validation, not external or prospective validation; submission timing relative
to each outcome must be established for a prospective predictive claim.
An effort-only one-dimensional k-means split supplies another unsupervised baseline.

Main sources:
- https://scikit-learn.org/stable/modules/clustering.html#clustering-performance-evaluation
- https://scikit-learn.org/stable/common_pitfalls.html
- https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html
