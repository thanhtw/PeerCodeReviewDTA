"""Recalculate Table 6 using original saved labels and documented definitions."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.optimize import brentq
from scipy.stats import nct

from generate_figures_r1_12 import load_verified

ROOT = Path(__file__).resolve().parent


def cohen_d(high, low):
    pooled = np.sqrt(((len(high) - 1) * high.var(ddof=1) + (len(low) - 1) * low.var(ddof=1)) /
                     (len(high) + len(low) - 2))
    return (high.mean() - low.mean()) / pooled


def cohen_d_ci(value, n_high, n_low, confidence=.95):
    """Equal-tailed noncentral-t CI for the population standardized difference.

    Uses the same pooled-SD, independent-group model as the reported Cohen's d.
    Conditions on observed group assignments; does not correct cluster selection.
    """
    scale = np.sqrt(1 / n_high + 1 / n_low)
    observed_t = value / scale
    df = n_high + n_low - 2
    alpha = 1 - confidence
    limits = []
    for probability in (1 - alpha / 2, alpha / 2):
        width = 8.
        while True:
            lo, hi = observed_t - width, observed_t + width
            f_lo = nct.cdf(observed_t, df, lo) - probability
            f_hi = nct.cdf(observed_t, df, hi) - probability
            if f_lo >= 0 and f_hi <= 0:
                break
            width *= 2
            if width > 1e6:
                raise RuntimeError('Cannot bracket noncentral-t confidence limit')
        limits.append(brentq(lambda noncentrality: nct.cdf(observed_t, df, noncentrality) - probability,
                             lo, hi) * scale)
    return tuple(limits)


def run():
    d, sources = load_verified()
    out = ROOT / 'Table6_results'
    out.mkdir(exist_ok=True)
    score_cols = ['HW1', 'HW3', 'HW4', 'HW5', 'HW6', 'HW7']
    assert d.HW1.eq(d.HW2).all(), 'Six-column sensitivity presumes recorded HW1=HW2'
    d['Round2_retention'] = d.Effort_R2 / d.Effort_R1
    d['Mean_assignment_score_6'] = d[score_cols].mean(axis=1)
    if not np.isfinite(d[['Round2_retention', 'Comment_density', 'Mean_assignment_score_6']]).all().all():
        raise ValueError('Nonfinite derived variables')
    extended = d.Cluster.eq(1)
    high = d.Effort_Total.gt(d.Effort_Total.median())
    design = pd.DataFrame({'Intercept': np.ones(len(d)), 'Effort_Total': d.Effort_Total,
                           'Extended_indicator': extended.astype(int)})
    variables = [('Composite effort', 'Effort_Total'),
                 ('Meaningful comment density', 'Comment_density'),
                 ('Round 1 start', 'R1.Start'),
                 ('Round 2 retention', 'Round2_retention'),
                 ('Mean assignment score (6 columns)', 'Mean_assignment_score_6')]
    rows, regressions = [], []
    for name, col in variables + [('Stored Mean_HW (7-column sensitivity)', 'Mean_HW')]:
        y = d[col]
        row = {'Variable': name, 'source_variable': col}
        for group, mask in [('Extended', extended), ('Brief', ~extended), ('High_effort', high), ('Low_effort', ~high)]:
            row[group + '_n'] = int(mask.sum())
            row[group + '_mean'] = float(y.loc[mask].mean())
            row[group + '_SD'] = float(y.loc[mask].std(ddof=1))
        row['d_cluster'] = float(cohen_d(y.loc[extended], y.loc[~extended]))
        row['d_median_split'] = float(cohen_d(y.loc[high], y.loc[~high]))
        for prefix, n1, n2 in [('d_cluster', int(extended.sum()), int((~extended).sum())),
                               ('d_median_split', int(high.sum()), int((~high).sum()))]:
            row[prefix + '_CI_low'], row[prefix + '_CI_high'] = cohen_d_ci(row[prefix], n1, n2)
        if col != 'Effort_Total':
            model = sm.OLS(y, design).fit()
            hc3 = sm.OLS(y, design).fit(cov_type='HC3', use_t=True)
            row.update(b_cluster=float(model.params.Extended_indicator),
                       SE_cluster=float(model.bse.Extended_indicator),
                       t_cluster=float(model.tvalues.Extended_indicator),
                       p_cluster=float(model.pvalues.Extended_indicator),
                       CI_low=float(model.conf_int().loc['Extended_indicator', 0]),
                       CI_high=float(model.conf_int().loc['Extended_indicator', 1]),
                       p_HC3_sensitivity=float(hc3.pvalues.Extended_indicator),
                       R2=float(model.rsquared), residual_df=float(model.df_resid))
            for coefficient in design:
                regressions.append(dict(variable=name, coefficient=coefficient, b=float(model.params[coefficient]),
                                        SE=float(model.bse[coefficient]), t=float(model.tvalues[coefficient]),
                                        p=float(model.pvalues[coefficient])))
        rows.append(row)
    numeric = pd.DataFrame(rows)
    primary = numeric.iloc[:5]
    formatted = []
    for _, row in primary.iterrows():
        formatted.append({'Variable': row.Variable,
                          'Extended (n=41)': f'{row.Extended_mean:.2f} ± {row.Extended_SD:.2f}',
                          'Brief (n=32)': f'{row.Brief_mean:.2f} ± {row.Brief_SD:.2f}',
                          'High effort (n=36)': f'{row.High_effort_mean:.2f} ± {row.High_effort_SD:.2f}',
                          'Low effort (n=37)': f'{row.Low_effort_mean:.2f} ± {row.Low_effort_SD:.2f}',
                          'Cluster d [95% CI]': f'{row.d_cluster:.2f} [{row.d_cluster_CI_low:.2f}, {row.d_cluster_CI_high:.2f}]',
                          'Median-split d [95% CI]': f'{row.d_median_split:.2f} [{row.d_median_split_CI_low:.2f}, {row.d_median_split_CI_high:.2f}]',
                          'Cluster effect controlling effort': 'N/A' if row.source_variable == 'Effort_Total'
                          else f'b = {row.b_cluster:.3f}, p = {row.p_cluster:.3f}',
                          '95% CI for adjusted b': 'N/A' if row.source_variable == 'Effort_Total'
                          else f'[{row.CI_low:.3f}, {row.CI_high:.3f}]'})
    table = pd.DataFrame(formatted)
    export_cols = ['Index', 'Cluster', 'Effort_Total', 'Effort_R1', 'Effort_R2', 'R1_MF_Count', 'R2_MF_Count',
                   'Comment_density', 'R1.Start', 'Round2_retention', 'Mean_assignment_score_6', 'Mean_HW'] + [f'HW{i}' for i in range(1, 8)]
    export = d[export_cols].assign(High_effort=high.astype(int))
    numeric.to_csv(out / 'Table6_exact_values.csv', index=False)
    table.to_csv(out / 'Table6_formatted.csv', index=False)
    intervals = numeric[['Variable', 'b_cluster', 'SE_cluster', 'CI_low', 'CI_high', 'p_cluster', 'residual_df']]
    intervals.to_csv(out / 'Table6_95CI.csv', index=False)
    d_intervals = numeric[['Variable', 'd_cluster', 'd_cluster_CI_low', 'd_cluster_CI_high',
                           'd_median_split', 'd_median_split_CI_low', 'd_median_split_CI_high']]
    d_intervals.to_csv(out / 'Table6_Cohen_d_95CI.csv', index=False)
    with pd.ExcelWriter(out / 'Table6_calculated.xlsx') as writer:
        table.to_excel(writer, sheet_name='Table6_formatted', index=False)
        numeric.to_excel(writer, sheet_name='Exact_values_and_sensitivity', index=False)
        intervals.to_excel(writer, sheet_name='Adjusted_effect_95CI', index=False)
        d_intervals.to_excel(writer, sheet_name='Cohen_d_95CI', index=False)
        pd.DataFrame(regressions).to_excel(writer, sheet_name='OLS_coefficients', index=False)
        export.to_excel(writer, sheet_name='Calculation_data_no_ID', index=False)
    lines = ['| ' + ' | '.join(table.columns) + ' |', '|' + '|'.join(['---'] * len(table.columns)) + '|']
    lines += ['| ' + ' | '.join(map(str, values)) + ' |' for values in table.to_numpy()]
    note = '''
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
'''
    (out / 'Table6_calculated.md').write_text('# Table 6. Cluster solution versus effort median split\n\n' + '\n'.join(lines) + '\n\n' + note, encoding='utf-8')
    (out / 'metadata.json').write_text(json.dumps(dict(sources=[str(p) for p in sources],
                         cluster_refitted=False, score_columns=score_cols,
                         stored_mean_score_columns=[f'HW{i}' for i in range(1, 8)],
                         median=364, high_effort_rule='Effort_Total > 364',
                         regression='OLS: intercept + raw Effort_Total + I(Cluster=1)',
                         main_p_method='Conventional two-sided OLS t test',
                         confidence_level=0.95, CI_method='b +/- t(0.975, 70) * conventional OLS SE(b)',
                         Cohen_d_CI_method='Equal-tailed noncentral-t inversion, pooled-SD independent-group model; fixed assignments'), indent=2), encoding='utf-8')
    fig, ax = plt.subplots(figsize=(24, 5.5))
    ax.axis('off')
    labels = ['Variable', 'Extended\n(n=41)', 'Brief\n(n=32)', 'High effort\n(n=36)', 'Low effort\n(n=37)', 'Cluster\nd [95% CI]', 'Median split\nd [95% CI]', 'Adjusted cluster effect\ncontrolling effort', '95% CI\nfor adjusted b']
    cells = table.to_numpy().tolist()
    cells[1][0] = 'Meaningful comment\ndensity'
    cells[-1][0] = 'Mean assignment score\n(six columns)'
    chart = ax.table(cellText=cells, colLabels=labels, cellLoc='center', loc='center',
                     colWidths=[.16, .10, .10, .10, .10, .15, .15, .16, .13])
    chart.auto_set_font_size(False); chart.set_fontsize(9); chart.scale(1, 2.7)
    for (r, c), cell in chart.get_celld().items():
        if r == 0:
            cell.set_facecolor('#e8eef5'); cell.set_text_props(weight='bold')
    ax.set_title('Table 6. Comparison of the cluster solution with an effort median split', pad=12)
    fig.text(.02, .04, 'Mean ± sample SD. Adjusted effects: OLS with raw continuous effort and cluster indicator; two-sided p.\nScore averages HW1 and HW3–HW7. See accompanying methods and seven-column sensitivity.', fontsize=10)
    for ext in ['png', 'pdf']:
        fig.savefig(out / f'Table6_calculated.{ext}', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(table.to_string(index=False))


if __name__ == '__main__':
    run()
