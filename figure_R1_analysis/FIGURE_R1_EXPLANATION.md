# Data-based interpretation of the attached Figure R1

## Version audit: resolve before using this figure with existing tables

The attached plot is reproduced by the stored labels in
`Chart_input_clustering_results_clustered_data_k2.xlsx` (also present in
`New-Chart_input_clustering_results_clustered_data_k2.xlsx`). These labels are
not the same as those in `Merge-Data.xlsx`, `output-cluster-with-score.xlsx`,
`For_analysis_Clustering_Result.xlsx` and the main sheet of
`Table-5-hw-cluster-with-score.xlsx`. Ten of 73 students have different labels,
despite both solutions having group sizes 41 and 32. The data values used here
agree between the chart and historical workbooks after ID matching.

| Label version | Extended/Brief n | Disagreement with effort median | Agreement |
|---|---|---|---|
| Stored chart labels (attached image) | 41/32 | 11 | 84.93% |
| Historical labels used in the earlier effort analysis | 41/32 | 5 | 93.15% |
| Corrected alternative feature configuration, Python refit | 40/33 | 10 | 86.30% |

The attached image's 11 circles are correct for its stored labels; the earlier
five-disagreement result is correct for the historical labels. These are different
partitions, not competing calculations of the same partition. Do not combine
the earlier historical-label adjusted score estimates, agreement statistics, or
validation claims with this figure as though they describe one solution.

The stored chart partition is reproduced exactly (ARI=1) by standardized PCA
(three components) and k-means using the alternative R script's feature list:

    Effort_R1, Effort_R1, R1.Dur, R2.Dur, R1.Start, R1.End,
    R2.Start, R2.End, MF_Ratio_R1, MF_Ratio_R2

This is strong evidence of consistency with that configuration, not a recovered
execution log proving the original run's provenance. The duplicate Effort_R1
weights Round 1 effort twice and omits Effort_R2. The script name and stored
artifact alone do not establish whether that weighting was intended. Replacing
the second Effort_R1 with Effort_R2 changes one assignment in our Python refit,
producing 40/33 groups and 10 median disagreements. This is a sensitivity result,
not an automatic replacement of the published analysis.

The alternative inputs also use stored MF_Ratio_R2 values that set zero-denominator
cases to zero or one. The corrected-feature sensitivity above fixes only the
duplicated effort variable, not the definition of these ratios. It is therefore
not a fully validated preprocessing correction. Resolve both definitions before
choosing the final alternative workflow.

## 1. Define the figure's quantities explicitly

For student i:

    E_i = R1.C1.Sub + R1.C2.Sub + R1.C3.Sub
        + R2.C1.Sub + R2.C2.Sub + R2.C3.Sub

    D_i = (R1_MF_Count + R2_MF_Count) / E_i

Panel (a) plots E_i against R1.Start. Panel (b) plots E_i against D_i. E_i is
the stored Effort_Total and is positive for all 73 students, so this total-density
calculation has no zero denominator. It counts recorded category submissions;
do not imply unique review sessions or a validated latent effort scale.

The sample median is 364. Define high effort as E_i>364 and low effort as
E_i<=364; the one student exactly at 364 is assigned low. This yields 36 high
and 37 low students. Changing the tie convention changes the disagreement count.
Later start means a larger recorded delay after release under the figure's
stated timestamp interpretation; it does not by itself mean longer duration,
greater persistence, or better behavior.

## 2. Quantify agreement rather than relying on visual impression

| Stored chart cluster | E<=364 | E>364 | Total |
|---|---:|---:|---:|
| Extended Engagers (blue) | 8 | 33 | 41 |
| Brief Participants (orange) | 29 | 3 | 32 |
| Total | 37 | 36 | 73 |

Thus, 33+29=62 students agree with a median split and 8+3=11 disagree.
Agreement is 62/73=84.93%; ARI=0.481. The circled students are exactly those
11 disagreements, not statistical outliers, errors, misclassified students,
or evidence of an independently validated true label.

## 3. What timing and density add descriptively

Use medians for timing and means of within-student ratios for density:

| Effort stratum | Stored chart cluster | n | Median R1 start, min | Mean density, comments per 100 submissions |
|---|---|---:|---:|---:|
| E<=364 | Extended | 8 | 1569.40 | 3.44 |
| E<=364 | Brief | 29 | 382.47 | 9.85 |
| E>364 | Extended | 33 | 1141.40 | 4.59 |
| E>364 | Brief | 3 | 399.80 | 10.69 |

The eight lower-effort blue students begin later and have lower mean meaningful
comment density than the 29 lower-effort orange students. The three higher-effort
orange students start earlier and have higher mean density than the 33 higher-
effort blue students. The separation therefore is not exactly a median threshold.

Concrete examples using the original anonymized Index column:

- Index 43: effort 171, R1 start 2287.60 min, density 1.75 per 100, blue.
- Index 47: effort 444, R1 start 629.80 min, density 16.44 per 100, orange.
- Index 28: effort 459, R1 start 276.33 min, density 8.50 per 100, orange.

The effort strata are broad, not matched effort groups: mean effort is 271.63
versus 156.59 within the lower stratum and 511.55 versus 469.00 within the higher
stratum. Do not call these comparisons controlled for identical effort.
The orange high-effort group contains only three students, so its descriptive
statistics are particularly sensitive to individual cases.

Across the full stored chart groups, median R1 start is 1154.00 versus 387.77
minutes, and mean comment density is 4.37 versus 9.93 per 100 submissions.

## 4. A descriptive continuous-effort adjustment

We fitted a three-df natural cubic spline of log(1+E) separately to timing and
density and examined residual contrasts between stored chart labels. Residual
Extended-minus-Brief differences are +451.62 minutes for R1 start and -0.01879
for density, corresponding to +0.763 and -0.366 residual SD, respectively.
In joint regressions Y~spline(log(1+E))+cluster, the cluster coefficients are
+1052.26 minutes and -0.04378 density units (-4.38 per 100), respectively.
Residual mean contrasts and joint regression coefficients are different
quantities; do not quote them interchangeably.

These are descriptive diagnostics and should not be treated as independent
post-selection significance tests, since timing and normalized MF measures
are inputs to the alternative clustering. Density also shares its denominator
with effort, so an inverse visual relationship can partly reflect mathematical
coupling. The figure and these diagnostics do not establish a separate latent
behavioral type, superior prediction, or higher feedback quality.

## 5. Suggested Results text for this stored chart solution

“The two-cluster partition agreed with an effort-total median split for 62 of
73 students (84.9%; adjusted Rand index=0.481). The 11 discordant assignments
comprised eight students at or below the effort median assigned to Extended
Engagers and three students above the median assigned to Brief Participants.
Within the lower-effort stratum, these groups had median Round 1 start times
of 1569.4 and 382.5 minutes and mean meaningful-comment densities of 3.44 and
9.85 comments per 100 submissions, respectively. Within the higher-effort
stratum, the corresponding values were 1141.4 versus 399.8 minutes and 4.59
versus 10.69 comments per 100 submissions. The partition therefore reflects
timing and density associations in addition to a simple effort threshold.
These comparisons are descriptive and do not independently validate distinct
behavioral types.”

Use this only after resolving which label version and feature configuration
the manuscript adopts. If retaining the historical labels, use the separately
generated historical figure (five circles) and its corresponding statistics.

## Suggested caption for the attached/stored-chart version

“Figure R1. Total recorded review submissions against (a) Round 1 review start
time and (b) meaningful-comment density, defined as total meaningful comments
across both rounds divided by total submissions. Colors and symbols indicate
the stored chart cluster assignments. The dashed line marks the effort median
(364); the median split assigns E<=364 to the lower-effort group. Circles mark
the 11 students whose cluster assignment differs from that split. The partitions
agree for 62/73 students (84.9%). Discordant cases illustrate timing and density
patterns beyond the median threshold; these are descriptive associations among
variables used in clustering, not independent validation of behavioral types.”

## Reviewer-response wording

“To examine whether the partition is simply an effort-total split, we plotted
total submissions against review timing and meaningful-comment density and
identified discordant assignments. For the stored chart solution, agreement
with a median split was 84.9%, with 11 discordant students. Eight lower-effort
students assigned to Extended Engagers tended to begin later and exhibit lower
meaningful-comment density, whereas three higher-effort students assigned to
Brief Participants began earlier and had higher density. Thus the partition
is not identical to an effort median split. Nevertheless, timing and feedback
measures contributed to the clustering itself, and these comparisons are
descriptive rather than independent validation. We therefore distinguish
multivariate descriptive information from evidence of distinct behavioral
types or improved outcome prediction.”

Before submitting that response, unify the labels and resolve the alternative
feature/ratio definitions. To claim added outcome value, rerun the score analyses
using the chosen configuration with all preprocessing inside training folds;
do not transfer the earlier original-feature CV results to this partition.

## Score-table consistency check

The label versions yield different Mean_HW summaries from the same score data:

- Stored chart: Extended 83.51; Brief 74.43 (difference 9.07).
- Historical: Extended 87.36; Brief 69.50 (difference 17.86).

This illustrates why the figure cannot be combined with historical score-table
means as though the labels were identical. `label_version_comparison.csv`
documents the versions. Source HW1/HW2 duplication remains unresolved in both.

## Outputs and reproduction

Run `python Cluster-Analysis/analyze_figure_r1.py` from the project root.
The workbook contains plotting values, all 11 circled cases, the 10 label-version
changes, confusion table, stratified summaries and descriptive adjustment results.
Direct student IDs are omitted from exports. PNG/PDF figures are generated
separately for stored chart, historical, and corrected-alternative labels.
The audit verifies 73 rows, eight low-effort blue disagreements and three
high-effort orange disagreements. Metadata records input hashes and definitions.
