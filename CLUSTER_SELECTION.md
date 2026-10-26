# Selecting k and responding to the reviewer

## What the original code actually did

Both `K-mean-with-n-cluster.R` scripts call
`maxSE(gap_stat$Tab[, "gap"], gap_stat$Tab[, "SE.sim"])` without a method.
The R default is `firstSEmax`, which examines the first local gap maximum and
allows a smaller k within its uncertainty band. `fviz_gap_stat()` uses the same
default. Both scripts then set `optimal_k_final <- optimal_k_silhouette`.
Thus the implementation uses silhouette as its primary final decision; it does
not explicitly implement Tibshirani's adjacent-comparison rule and does not simply
select the global maximum gap. Describe this history accurately.

## Tibshirani et al. (2001) rule

For each k, Gap(k) = mean_b[log W*_b(k)] - log W(k).
Generate B uniform reference datasets in the PCA-aligned bounding box, refitting
the clustering for each k and each reference sample. Define
s(k) = sqrt(1 + 1/B) × SD_b[log W*_b(k)], using sample SD (denominator B-1).
Select the **smallest** k such that

    Gap(k) >= Gap(k+1) - s(k+1).

Include k=1: otherwise the procedure cannot conclude that no split is warranted.
The bar quantity is simulation-adjusted reference SD, not a confidence interval
for a difference, and not SD divided by sqrt(B). Compare adjacent values using
the NEXT k's s, rather than judging overlap between plotted bars.
If no comparison passes before Kmax, the implementation returns Kmax as a
boundary fallback; extend the range before treating that as an established optimum.

## What the attached Figure 4 suggests

Approximate visual readings (not extracted original statistics) give:

| Comparison | Gap(k) | Gap(k+1) - s(k+1) | Pass? |
|---|---:|---:|---|
| k=1 versus 2 | 0.193 | 0.340 - 0.033 = 0.307 | No |
| k=2 versus 3 | 0.340 | 0.305 - 0.033 = 0.272 | Yes |

Therefore **k=2 appears to satisfy the Tibshirani rule**, because k=1 fails and
k=2 passes. This conclusion is an inference from the plotted values, not an exact
audit of the R object that generated the image. The Python outputs provide a new,
reproducible numerical audit on the supplied input; distinguish them from the
original Figure 4. Do not use these approximate values as measured results.

Overlapping bars for larger k do not overturn that rule: it deliberately favors
the first adequate, parsimonious partition rather than asserting that its gap is
significantly higher than every larger k. The appropriate claim is a supported
two-cluster summary under the stated representation and reference model, not
proof of two natural populations or universal robustness. Silhouette agreement
is complementary evidence. WSS supplies a diagnostic curve, not a formal optimum.

## Suggested response based on code and figure (before exact original-table audit)

“Thank you for identifying the ambiguity in our description. Inspection of the
analysis scripts shows that the final cluster count was chosen using average
silhouette width, with the gap statistic providing complementary evidence. The
gap implementation used R's default firstSEmax criterion, which differs from the
adjacent-comparison rule in Tibshirani et al. (2001). We have clarified this
distinction. The Tibshirani rule selects the smallest k for which
Gap(k) >= Gap(k+1) - s(k+1), where s(k) is the simulation-adjusted standard
deviation of reference log-dispersion. The displayed Figure 4 is consistent with
this rule selecting k=2: the k=1 comparison fails and the k=2 comparison passes.
We distinguish this graphical assessment from the numerical reanalysis supplied
with the revision. Overlap of the displayed uncertainty bars does not constitute
a pairwise significance test. We interpret the partition as a parsimonious
behavioral summary and have moderated claims of robustness.”

For a final response, replace the graphical-assessment sentence with the exact
Python reanalysis values from `python_results/selection_report.md`, explicitly
calling it a reanalysis and stating B, seed, feature set, distance power and the
reference distribution. If the exact original `gap_stat$Tab` becomes available,
apply the rule directly to it to audit the historical figure without refitting.

## Limits and further evidence

The Python default increases B from 50 to 500 to reduce Monte Carlo uncertainty
in the estimated reference mean and SD; it does not eliminate uncertainty about
the data or the clustering model. Repeat with separate seeds and preserve output
folders to assess Monte Carlo sensitivity. The exported initialization ARI checks
optimizer sensitivity for k=2,3,4. Sampling robustness would require resampling
observations and refitting scaling, PCA and clustering, with appropriate matching
of clusters; this is not established by the gap bars or by initialization ARI.
Changing the feature set or distance power is a separate model sensitivity analysis.

## Sources

- [R cluster documentation: clusGap and maxSE](https://stat.ethz.ch/R-manual/R-devel/RHOME/library/cluster/html/clusGap.html)
- [R factoextra documentation: fviz_gap_stat default](https://rpkgs.datanovia.com/factoextra/reference/fviz_nbclust.html)
- Tibshirani, R., Walther, G., and Hastie, T. (2001). Estimating the number of
  clusters in a data set via the gap statistic. JRSS B, 63(2), 411–423.
  [DOI](https://doi.org/10.1111/1467-9868.00293)
