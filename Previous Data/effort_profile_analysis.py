"""Audit whether historical clusters add information beyond overall effort.

Historical labels are used for descriptive and adjusted associations. Predictive
validation refits scaling, PCA and k-means inside each training fold. Behavioral
comparisons are descriptive because the same features generated the clusters.
"""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import patsy
import scipy
from scipy.stats import spearmanr, pearsonr
import sklearn
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, roc_auc_score, silhouette_score
from sklearn.model_selection import KFold
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from threadpoolctl import threadpool_limits

from clustering_analysis import FEATURES

ROOT = Path(__file__).resolve().parent
COUNT = [f'R{r}.C{i}.Sub' for r in (1, 2) for i in (1, 2, 3)]
OUTCOMES = ['Mean_HW', 'HW_unique_sensitivity', 'Mid', 'Final']


def standardize(train, test=None):
    mean, sd = train.mean(axis=0), train.std(axis=0, ddof=1)
    if (sd == 0).any():
        raise ValueError('Constant feature in training data')
    a = (train - mean) / sd
    return a if test is None else (a, (test - mean) / sd)


def kmeans(x):
    return KMeans(n_clusters=2, n_init=25, max_iter=300,
                  algorithm='elkan', random_state=42).fit(x)


def label_high_effort(labels, effort):
    high = max(np.unique(labels), key=lambda c: effort[labels == c].mean())
    return (labels == high).astype(int), int(high)


def threshold_summary(score, target):
    """Descriptive optimal threshold; searched in-sample, not validated accuracy."""
    unique = np.unique(score)
    thresholds = np.r_[unique[0] - 1, (unique[:-1] + unique[1:]) / 2, unique[-1] + 1]
    accuracy = np.array([np.mean((score > t) == target) for t in thresholds])
    best = np.flatnonzero(accuracy == accuracy.max())
    return dict(accuracy=float(accuracy.max()), threshold_low=float(thresholds[best[0]]),
                threshold_high=float(thresholds[best[-1]]),
                example_threshold=float(thresholds[best[0]]))


def agreement(name, split, high):
    return dict(method=name, high_n=int(split.sum()), low_n=int((1 - split).sum()),
                agreement=float(np.mean(split == high)),
                disagreements=int(np.sum(split != high)), ARI=float(adjusted_rand_score(high, split)))


def save_fig(fig, out, name):
    fig.tight_layout()
    for ext in ('png', 'pdf'):
        fig.savefig(out / f'{name}.{ext}', dpi=300, bbox_inches='tight')
    plt.close(fig)


def summary_figures(out):
    residuals = pd.read_csv(out / 'effort_adjusted_features.csv')
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(range(14), residuals.raw_standardized_mean_difference, 'o-', label='Original feature contrast')
    ax.plot(range(14), residuals.effort_adjusted_residual_difference_SD, 's-', label='After smooth effort adjustment')
    ax.axhline(0, color='grey', linewidth=.8)
    ax.set_xticks(range(14)); ax.set_xticklabels(FEATURES, rotation=65, ha='right', fontsize=8)
    ax.set(ylabel='Extended minus Brief (SD units)',
           title='Descriptive feature contrasts before and after accounting for total effort')
    ax.legend(); ax.grid(alpha=.15)
    save_fig(fig, out, 'effort_adjusted_contrasts')


def adjusted_outcomes(d, high):
    rows = []
    data = d.assign(log_effort=np.log1p(d.Effort_Total), high=high)
    for control in (False, True):
        for shape in ('raw_linear', 'log_linear', 'log_spline'):
            effort_term = {'raw_linear': 'Effort_Total', 'log_linear': 'log_effort',
                           'log_spline': "cr(log_effort, df=3, constraints='center')"}[shape]
            formula = '1 + ' + effort_term + (' + Pre' if control else '')
            base = patsy.dmatrix(formula, data, return_type='dataframe')
            full = base.assign(high=high)
            for outcome in OUTCOMES:
                baseline = sm.OLS(data[outcome], base).fit()
                fit = sm.OLS(data[outcome], full).fit(cov_type='HC3', use_t=True)
                ci = fit.conf_int().loc['high']
                rows.append(dict(outcome=outcome, effort_model=shape, adjust_pre=control,
                                 cluster_coefficient=float(fit.params['high']),
                                 CI_low=float(ci.iloc[0]), CI_high=float(ci.iloc[1]),
                                 p_HC3=float(fit.pvalues['high']),
                                 R2_base=float(baseline.rsquared), R2_plus_cluster=float(fit.rsquared),
                                 delta_R2=float(fit.rsquared - baseline.rsquared),
                                 condition_number=float(fit.condition_number)))
    results = pd.DataFrame(rows)
    # Correct across three distinct primary/exam outcomes, not the duplicate-HW sensitivity.
    results['p_Holm_primary_family'] = np.nan
    for control in (False, True):
        for shape in ('raw_linear', 'log_linear', 'log_spline'):
            mask = ((results.adjust_pre == control) & (results.effort_model == shape)
                    & (results.outcome != 'HW_unique_sensitivity'))
            results.loc[mask, 'p_Holm_primary_family'] = multipletests(results.loc[mask, 'p_HC3'], method='holm')[1]
    return results


def relative_profiles(d, high, x):
    p = pd.DataFrame(index=d.index)
    total = d[COUNT].sum(axis=1)
    p['R2_share_of_submissions'] = d[[c for c in COUNT if c.startswith('R2')]].sum(axis=1) / total
    for j, name in [(1, 'Functionality'), (2, 'Readability'), (3, 'Documentation')]:
        p[f'{name}_share'] = (d[f'R1.C{j}.Sub'] + d[f'R2.C{j}.Sub']) / total
    for r in (1, 2):
        round_total = d[[f'R{r}.C{j}.Sub' for j in (1, 2, 3)]].sum(axis=1)
        p[f'R{r}_MF_per_submission'] = d[f'R{r}.MF'] / round_total.replace(0, np.nan)
    p['Duration_minutes_per_submission'] = (d['R1.Dur'] + d['R2.Dur']) / total
    # Feature residuals: remove a low-df smooth function of magnitude, then
    # standardize residuals for a descriptive comparison on common scale.
    basis = np.asarray(patsy.dmatrix("1 + cr(e, df=3, constraints='center')", {'e': np.log1p(total)}))
    residual = x - basis @ np.linalg.lstsq(basis, x, rcond=None)[0]
    residual_z = residual / residual.std(axis=0, ddof=1)
    rows = []
    for col in p:
        a, b = p.loc[high == 1, col], p.loc[high == 0, col]
        pooled = np.sqrt(((a.count() - 1) * a.var(ddof=1) + (b.count() - 1) * b.var(ddof=1)) /
                         (a.count() + b.count() - 2))
        rows.append(dict(feature=col, high_mean=a.mean(), low_mean=b.mean(),
                         high_median=a.median(), low_median=b.median(),
                         mean_difference=a.mean() - b.mean(), descriptive_Cohen_d=(a.mean() - b.mean()) / pooled))
    contrasts = pd.DataFrame({'feature': FEATURES,
                              'raw_standardized_mean_difference': x[high == 1].mean(axis=0) - x[high == 0].mean(axis=0),
                              'effort_adjusted_residual_difference_SD': residual_z[high == 1].mean(axis=0) - residual_z[high == 0].mean(axis=0)})
    # These are not post-selection hypothesis tests.
    return p, pd.DataFrame(rows), contrasts


def cv_analysis(d, repeats):
    raw = d[FEATURES].to_numpy(float)
    effort = d.Effort_Total.to_numpy(float)
    pre = d.Pre.to_numpy(float)
    y = d[OUTCOMES].to_numpy(float)
    predictions = []
    for repeat in range(repeats):
        kfold = KFold(n_splits=5, shuffle=True, random_state=4200 + repeat)
        for fold, (train, test) in enumerate(kfold.split(d)):
            ztrain, ztest = standardize(raw[train], raw[test])
            pca = PCA(n_components=3, svd_solver='full').fit(ztrain)
            cluster = kmeans(pca.transform(ztrain))
            ctr_train, high_label = label_high_effort(cluster.labels_, effort[train])
            ctr_test = (cluster.predict(pca.transform(ztest)) == high_label).astype(int)
            effort_cluster = kmeans(effort[train, None])
            effort_ctr_train, effort_high_label = label_high_effort(effort_cluster.labels_, effort[train])
            effort_ctr_test = (effort_cluster.predict(effort[test, None]) == effort_high_label).astype(int)
            # All predictors, including the spline's knots and median cutpoint,
            # are estimated from training observations only.
            log_train, log_test = np.log1p(effort[train]), np.log1p(effort[test])
            spline_train = patsy.dmatrix("1 + cr(e, df=3, constraints='center')", {'e': log_train})
            spline_test = np.asarray(patsy.build_design_matrices([spline_train.design_info], {'e': log_test})[0])
            matrices = {
                'intercept_only': (np.ones((len(train), 1)), np.ones((len(test), 1))),
                'effort_raw_linear': (np.c_[np.ones(len(train)), standardize(effort[train])],
                                      np.c_[np.ones(len(test)), (effort[test] - effort[train].mean()) / effort[train].std(ddof=1)]),
                'effort_log_linear': (np.c_[np.ones(len(train)), log_train], np.c_[np.ones(len(test)), log_test]),
                'effort_log_spline': (np.asarray(spline_train), spline_test),
                'effort_median_split': (np.c_[np.ones(len(train)), effort[train] > np.median(effort[train])],
                                        np.c_[np.ones(len(test)), effort[test] > np.median(effort[train])]),
                'composite14_linear': (np.c_[np.ones(len(train)), ztrain.mean(axis=1)],
                                       np.c_[np.ones(len(test)), ztest.mean(axis=1)]),
                'cluster_only': (np.c_[np.ones(len(train)), ctr_train], np.c_[np.ones(len(test)), ctr_test]),
                'effort_only_kmeans_split': (np.c_[np.ones(len(train)), effort_ctr_train],
                                             np.c_[np.ones(len(test)), effort_ctr_test]),
                'effort_log_spline_plus_cluster': (np.c_[spline_train, ctr_train], np.c_[spline_test, ctr_test]),
            }
            for control in (False, True):
                for name, (a, b) in matrices.items():
                    if control:
                        pre_sd = pre[train].std(ddof=1)
                        a = np.c_[a, (pre[train] - pre[train].mean()) / pre_sd]
                        b = np.c_[b, (pre[test] - pre[train].mean()) / pre_sd]
                    fitted = b @ np.linalg.lstsq(a, y[train], rcond=None)[0]
                    for j, idx in enumerate(test):
                        for t, outcome in enumerate(OUTCOMES):
                            predictions.append(dict(repeat=repeat, fold=fold, row=int(idx), outcome=outcome,
                                                    model=name, adjust_pre=control, actual=y[idx, t], predicted=fitted[j, t]))
        print(f'Cross-validation repeat {repeat + 1}/{repeats}', flush=True)
    predictions = pd.DataFrame(predictions)
    predictions['squared_error'] = (predictions.actual - predictions.predicted) ** 2
    predictions['absolute_error'] = (predictions.actual - predictions.predicted).abs()
    summary = predictions.groupby(['outcome', 'adjust_pre', 'model']).agg(
        MSE=('squared_error', 'mean'), MAE=('absolute_error', 'mean')).reset_index()
    summary['RMSE'] = np.sqrt(summary.MSE)
    per_repeat = predictions.groupby(['repeat', 'outcome', 'adjust_pre', 'model']).squared_error.mean().reset_index()
    per_repeat['RMSE'] = np.sqrt(per_repeat.squared_error)
    return predictions, summary, per_repeat


def run(args):
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    files = {'behavior': ROOT / 'input-data.xlsx', 'historical': ROOT / 'output-cluster-with-score.xlsx',
             'scores': ROOT / 'Merge-Data.xlsx'}
    behavior, historical, scores = [pd.read_excel(files[k]) for k in ('behavior', 'historical', 'scores')]
    for name, data in [('behavior', behavior), ('historical', historical), ('scores', scores)]:
        if data.Id.isna().any() or data.Id.duplicated().any():
            raise ValueError(f'{name}: IDs must be present and unique')
    historical = historical.set_index('Id').reindex(behavior.Id)
    scores = scores.set_index('Id').reindex(behavior.Id)
    if historical.Cluster.isna().any() or scores.Cluster.isna().any():
        raise ValueError('Unmatched student IDs')
    if not np.array_equal(historical.Cluster, scores.Cluster):
        raise ValueError('Historical cluster labels disagree between workbooks')
    d = behavior.copy().reset_index(drop=True)
    for col in ['Pre', 'Mid', 'Final', 'Mean_HW', 'Effort_Total'] + [f'HW{i}' for i in range(1, 8)]:
        d[col] = scores[col].to_numpy()
    d['Cluster_historical'] = historical.Cluster.to_numpy()
    for col in COUNT + ['R1.Dur', 'R2.Dur']:
        if not np.allclose(d[col], scores[col], equal_nan=True):
            raise ValueError(f'Behavior/score workbook disagreement for {col}')
    if not np.allclose(d[COUNT].sum(axis=1), d.Effort_Total):
        raise ValueError('Effort_Total does not equal six submission counts')
    if not np.isfinite(d[FEATURES + ['Pre', 'Mid', 'Final', 'Mean_HW', 'Effort_Total']].to_numpy()).all():
        raise ValueError('Missing or nonfinite analysis data')
    high = (d.Cluster_historical == 1).to_numpy(int)
    if d.loc[high == 1, 'Effort_Total'].mean() <= d.loc[high == 0, 'Effort_Total'].mean():
        raise ValueError('Historical cluster 1 is not the higher effort cluster')
    d['HW_unique_sensitivity'] = d[['HW1', 'HW3', 'HW4', 'HW5', 'HW6', 'HW7']].mean(axis=1)
    d['composite14'] = standardize(d[FEATURES].to_numpy(float)).mean(axis=1)
    d['composite_counts'] = standardize(d[COUNT].to_numpy(float)).mean(axis=1)
    effort = d.Effort_Total.to_numpy(float)
    x = standardize(d[FEATURES].to_numpy(float))
    pca = PCA(svd_solver='full').fit(x)
    pcs = pca.transform(x)
    count_pca = PCA(svd_solver='full').fit(standardize(d[COUNT].to_numpy(float)))
    contrasts = []
    splits = {}
    for column in ['Effort_Total', 'composite_counts', 'composite14']:
        median = d[column].median()
        split = (d[column] > median).to_numpy(int)
        splits[f'{column}_median'] = split
        contrasts.append(agreement(f'{column}_median', split, high))
    # Match the historical group sizes without selecting scores or threshold by outcomes.
    order = np.argsort(effort, kind='stable')
    same_size = np.zeros(len(d), dtype=int)
    same_size[order[-int(high.sum()):]] = 1
    if effort[order[-int(high.sum())]] == effort[order[-int(high.sum()) - 1]]:
        raise ValueError('Tied effort at size-matched boundary; specify a tie policy')
    splits['Effort_Total_same_size'] = same_size
    contrasts.append(agreement('Effort_Total_same_size', same_size, high))
    optimal = threshold_summary(effort, high)
    contrasts.append(agreement('Effort_Total_best_in_sample_threshold',
                               (effort > optimal['example_threshold']).astype(int), high))
    full_cluster = kmeans(pcs[:, :3])
    newhigh, _ = label_high_effort(full_cluster.labels_, effort)
    contrasts.append(agreement('Python_refit_vs_historical', newhigh, high))
    effort_only = kmeans(effort[:, None])
    effort_only_high, _ = label_high_effort(effort_only.labels_, effort)
    splits['Effort_Total_kmeans_split'] = effort_only_high
    contrasts.append(agreement('Effort_Total_kmeans_split', effort_only_high, high))
    comparisons = pd.DataFrame(contrasts)
    for name, split in splits.items():
        d[name] = split
    # Group score differences for transparent comparison with naive splits.
    differences = []
    for name, split in {'historical_cluster': high, **splits}.items():
        for outcome in OUTCOMES:
            differences.append(dict(split=name, outcome=outcome, high_n=int(split.sum()),
                                    high_mean=d.loc[split == 1, outcome].mean(),
                                    low_mean=d.loc[split == 0, outcome].mean(),
                                    mean_difference=d.loc[split == 1, outcome].mean() - d.loc[split == 0, outcome].mean()))
    proportions, relative, residuals = relative_profiles(d, high, x)
    adjusted = adjusted_outcomes(d, high)
    correlations = []
    for axis in range(3):
        for magnitude in ['Effort_Total', 'composite_counts', 'composite14']:
            correlations.append(dict(PC=axis + 1, score=magnitude,
                                     Pearson_r=pearsonr(pcs[:, axis], d[magnitude])[0],
                                     Spearman_rho=spearmanr(pcs[:, axis], d[magnitude])[0]))
    pc_info = pd.DataFrame({'PC': np.arange(1, len(pca.explained_variance_ratio_) + 1),
                            'variance_ratio': pca.explained_variance_ratio_})
    descriptive = d.groupby('Cluster_historical')[['Effort_Total', 'Pre'] + OUTCOMES].agg(['count', 'mean', 'std', 'median'])
    # Separate magnitude from shape in the standardized centroid contrast.
    delta = x[high == 1].mean(axis=0) - x[high == 0].mean(axis=0)
    magnitude_fraction = delta.sum() ** 2 / (len(delta) * np.dot(delta, delta))
    countx = standardize(d[COUNT].to_numpy(float))
    countdelta = countx[high == 1].mean(axis=0) - countx[high == 0].mean(axis=0)
    count_fraction = countdelta.sum() ** 2 / (len(countdelta) * np.dot(countdelta, countdelta))
    overlap_low = max(d.loc[high == 1, 'Effort_Total'].min(), d.loc[high == 0, 'Effort_Total'].min())
    overlap_high = min(d.loc[high == 1, 'Effort_Total'].max(), d.loc[high == 0, 'Effort_Total'].max())
    audit = dict(n=len(d), high_n=int(high.sum()), low_n=int((1 - high).sum()),
                 IDs_matched=True, historical_labels_match=True,
                 hw1_hw2_identical=bool((d.HW1 == d.HW2).all()),
                 zero_R2_submission_total_n=int((scores.Effort_R2 == 0).sum()),
                 stored_R2_ratio_at_zero_effort=scores.loc[scores.Effort_R2 == 0, 'MF_Ratio_R2'].tolist(),
                 mean_hw_matches_seven_column_average=bool(np.allclose(d.Mean_HW, d[[f'HW{i}' for i in range(1, 8)]].mean(axis=1))),
                 total_effort_median=float(np.median(effort)), effort_AUC=float(roc_auc_score(high, effort)),
                 effort_only_kmeans_cutpoint=float(effort_only.cluster_centers_.mean()),
                 effort_best_threshold=optimal,
                 PC1_variance=float(pca.explained_variance_ratio_[0]),
                 count_PC1_variance=float(count_pca.explained_variance_ratio_[0]),
                 centroid_contrast_magnitude_fraction_14features=float(magnitude_fraction),
                 centroid_contrast_magnitude_fraction_counts=float(count_fraction),
                 effort_common_range=[float(overlap_low), float(overlap_high)],
                 common_range_counts={str(c): int(((d.Effort_Total >= overlap_low) & (d.Effort_Total <= overlap_high) & (high == c)).sum()) for c in (0, 1)},
                 references_not_needed='No new gap analysis: this audits the fixed historical k=2 interpretation',
                 cv_repeats=args.repeats, cv_folds=5, cv_seed_start=4200,
                 versions={'numpy': np.__version__, 'pandas': pd.__version__, 'scipy': scipy.__version__, 'sklearn': sklearn.__version__},
                 inputs={name: {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for name, path in files.items()})
    frames = {'split_comparison': comparisons, 'score_differences': pd.DataFrame(differences),
              'relative_profiles': relative, 'effort_adjusted_features': residuals,
              'adjusted_score_models': adjusted, 'PC_magnitude_correlations': pd.DataFrame(correlations),
              'PCA_variance': pc_info, 'group_descriptives': descriptive}
    for name, frame in frames.items():
        frame.to_csv(out / f'{name}.csv', index=name == 'group_descriptives')
    predictions, cv, per_repeat = cv_analysis(d, args.repeats)
    frames.update(cv_summary=cv, cv_per_repeat=per_repeat)
    cv.to_csv(out / 'cv_summary.csv', index=False)
    per_repeat.to_csv(out / 'cv_per_repeat.csv', index=False)
    predictions.to_csv(out / 'cv_predictions.csv', index=False)
    # Public-facing exports omit direct student IDs. Rows use the original Excel row.
    export = d.drop(columns=['Id'], errors='ignore').assign(Source_Excel_Row=np.arange(len(d)) + 2)
    disagreement = export.loc[splits['Effort_Total_median'] != high]
    disagreement.to_csv(out / 'median_split_disagreements.csv', index=False)
    with pd.ExcelWriter(out / 'effort_comparison_results.xlsx') as writer:
        for name, frame in frames.items():
            frame.to_excel(writer, sheet_name=name[:31], index=name == 'group_descriptives')
        export.to_excel(writer, sheet_name='Student_data_no_ID', index=False)
        proportions.to_excel(writer, sheet_name='Relative_metrics', index=False)
    (out / 'analysis_metadata.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    # Linear profiles avoid misleading radius comparisons of radar charts.
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    for group, label, color in [(0, 'Brief Participants (n=32)', '#d97706'), (1, 'Extended Engagers (n=41)', '#2563eb')]:
        axes[0].plot(range(14), x[high == group].mean(axis=0), 'o-', label=label, color=color)
        centered = x - x.mean(axis=1, keepdims=True)
        axes[1].plot(range(14), centered[high == group].mean(axis=0), 'o-', label=label, color=color)
    for ax in axes:
        ax.set_xticks(range(14)); ax.set_xticklabels(FEATURES, rotation=75, ha='right', fontsize=8)
        ax.axhline(0, color='grey', linewidth=.7); ax.grid(alpha=.15)
    axes[0].set(title='Original standardized profiles', ylabel='Mean feature z score')
    axes[1].set(title='After subtracting each student’s mean z score', ylabel='Within-student centered z score')
    axes[0].legend(fontsize=8)
    save_fig(fig, out, 'magnitude_vs_shape')
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for group, color, label in [(0, '#d97706', 'Brief'), (1, '#2563eb', 'Extended')]:
        mask = high == group
        axes[0].scatter(effort[mask], pcs[mask, 0], c=color, label=label, alpha=.7)
        axes[1].scatter(effort[mask], d.loc[mask, 'Mean_HW'], c=color, label=label, alpha=.7)
    for ax in axes:
        ax.axvline(np.median(effort), color='black', ls='--', label='Median effort')
        ax.set_xlabel('Total submissions (six behavioral count columns)'); ax.legend()
    axes[0].set_ylabel('PC1'); axes[1].set_ylabel('Mean homework score (as supplied)')
    save_fig(fig, out, 'effort_cluster_score')
    fig, ax = plt.subplots(figsize=(9, 4))
    plotcols = ['Functionality_share', 'Readability_share', 'Documentation_share', 'R2_share_of_submissions']
    for group, color, offset, label in [(0, '#d97706', -.18, 'Brief'), (1, '#2563eb', .18, 'Extended')]:
        ax.bar(np.arange(4) + offset, proportions.loc[high == group, plotcols].mean() * 100, .36, label=label, color=color)
    ax.set(xticks=range(4), xticklabels=['Functionality', 'Readability', 'Documentation', 'Round 2 allocation'],
           ylabel='Mean within-student proportion (%)', title='Descriptive relative allocation; no post-selection significance claim')
    ax.legend(); save_fig(fig, out, 'relative_allocation')
    summary_figures(out)
    notes = '''# Interpretation and methods

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
'''
    (out / 'METHODS_AND_LIMITATIONS.md').write_text(notes, encoding='utf-8')
    print(json.dumps(audit, indent=2), flush=True)
    print(comparisons.to_string(index=False), flush=True)
    print(adjusted.loc[(adjusted.effort_model == 'log_spline') & adjusted.adjust_pre].to_string(index=False), flush=True)
    print(cv.loc[cv.adjust_pre].to_string(index=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'effort_profile_results')
    parser.add_argument('--repeats', type=int, default=20)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    with threadpool_limits(limits=1):
        run(args)
