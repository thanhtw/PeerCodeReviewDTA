"""Reproduce and audit the supplied effort/timing/comment-density figure.

Use the selected workbook's saved labels without refitting. Keep the historical
comparison separate. Group
comparisons of clustering inputs are descriptive, not independent validation.
"""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import patsy
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parent


def plot_panel(d, label, out, name):
    effort = d.Effort_Total.to_numpy(float)
    median = float(np.median(effort))
    high = label == 1
    disagree = high != (effort > median)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, col, title, ylabel in zip(axes, ['R1.Start', 'Comment_density'],
                                    ['(a) Effort magnitude versus review timing', '(b) Effort magnitude versus comment density'],
                                    ['Round 1 review start (minutes after release)', 'Meaningful comments / review submissions']):
        for mask, color, marker in [(high, '#267ce0', 'o'), (~high, '#f56536', '^')]:
            ax.scatter(effort[mask], d.loc[mask, col], color=color, marker=marker, s=24, zorder=3)
        ax.scatter(effort[disagree], d.loc[disagree, col], facecolors='none', edgecolors='black', s=92, linewidths=.9, zorder=4)
        ax.axvline(median, color='grey', ls='--', lw=1)
        ax.text(median + 7, .96, f'median = {median:g}', transform=ax.get_xaxis_transform(), color='dimgray', va='top', fontsize=9)
        ax.set(title=title, xlabel='Composite effort score (total review submissions)', ylabel=ylabel)
        ax.grid(axis='y', alpha=.2); ax.set_axisbelow(True)
        ax.spines[['top', 'right']].set_visible(False)
    handles = [Line2D([], [], ls='', marker='o', color='#267ce0', label=f'Extended Engagers (n={high.sum()})'),
               Line2D([], [], ls='', marker='^', color='#f56536', label=f'Brief Participants (n={(~high).sum()})'),
               Line2D([], [], ls='', marker='o', markerfacecolor='none', color='black', label=f'Cluster and median split disagree (n={disagree.sum()})')]
    fig.legend(handles=handles, loc='lower center', ncol=3, fontsize=9)
    fig.tight_layout(rect=(0, .1, 1, 1))
    for ext in ('png', 'pdf'):
        fig.savefig(out / f'{name}.{ext}', dpi=300, bbox_inches='tight')
    plt.close(fig)
    return disagree


def run(args):
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    chart_path = args.input.resolve()
    historical_path = ROOT / 'Merge-Data.xlsx'
    d = pd.read_excel(chart_path)
    if d.Cluster.value_counts().to_dict() != {1: 41, 2: 32}:
        raise ValueError('Expected saved Cluster labels: 1=41 students, 2=32 students')
    h = pd.read_excel(historical_path)
    if d.Id.duplicated().any() or h.Id.duplicated().any():
        raise ValueError('IDs must be unique')
    h = h.set_index('Id').reindex(d.Id)
    if h.Cluster.isna().any():
        raise ValueError('Unmatched IDs')
    # The older workbook supplies historical LABELS for comparison only.
    # New homework scores and means must always come from the selected input.
    for col in ['Effort_Total', 'R1.Start']:
        if not np.allclose(d[col], h[col]):
            raise ValueError(f'Values disagree for {col}')
    homework = [f'HW{i}' for i in range(1, 7)]
    if not np.allclose(d.Mean_HW, d[homework].mean(axis=1)):
        raise ValueError('Selected workbook Mean_HW does not equal the HW1-HW6 average')
    d['Comment_density'] = (d.R1_MF_Count + d.R2_MF_Count) / d.Effort_Total
    if not (d.Effort_Total > 0).all():
        raise ValueError('Total submission density denominator must be positive')
    effort = d.Effort_Total.to_numpy(float)
    median = np.median(effort)
    high = d.Cluster.eq(1).to_numpy()
    historical = h.Cluster.to_numpy(int)
    versions = {'stored_chart': d.Cluster.to_numpy(int), 'historical_original': historical}
    version_rows = []
    for version, label in versions.items():
        group = label == 1
        version_rows.append(dict(version=version, high_n=int(group.sum()), low_n=int((~group).sum()),
                                 median_disagreements=int(np.sum(group != (effort > median))),
                                 agreement_with_median=float(np.mean(group == (effort > median))),
                                 ARI_vs_stored_chart=float(adjusted_rand_score(label, d.Cluster)),
                                 changed_vs_stored_chart=int(np.sum(label != d.Cluster)),
                                 high_mean_HW=float(d.loc[group, 'Mean_HW'].mean()),
                                 low_mean_HW=float(d.loc[~group, 'Mean_HW'].mean())))
    pd.DataFrame(version_rows).to_csv(out / 'label_version_comparison.csv', index=False)
    disagree = plot_panel(d, versions['stored_chart'], out, 'figure_R1_stored_chart')
    plot_panel(d, versions['historical_original'], out, 'figure_R1_historical_original')
    # Retain the requested output filename, but use exactly the saved labels.
    # No scaling, PCA or k-means is rerun in this figure-generation workflow.
    plot_panel(d, versions['stored_chart'], out, 'figure_R1_alternative_corrected')
    corrected = d.copy()
    corrected['Stored_Cluster'] = corrected.Cluster
    corrected['Median_high'] = (effort > median).astype(int)
    corrected['Disagrees_with_median'] = corrected.Cluster.eq(1).to_numpy() != (effort > median)
    corrected['Effort_stratum'] = np.where(effort > median, 'Above median', 'At or below median')
    corrected_export = corrected.drop(columns=['Id'])
    corrected_export.to_csv(out / 'figure_R1_alternative_corrected_data.csv', index=False)
    with pd.ExcelWriter(out / 'figure_R1_alternative_corrected_data.xlsx') as writer:
        corrected_export.to_excel(writer, sheet_name='Corrected_data_no_ID', index=False)
        corrected_export.loc[corrected_export.Disagrees_with_median].to_excel(writer, sheet_name='Disagreement_cases', index=False)
        corrected.groupby('Cluster')[['Effort_Total', 'R1.Start', 'Comment_density', 'Mean_HW'] + homework].agg(['count', 'mean', 'median', 'std']).to_excel(writer, sheet_name='Corrected_group_summaries')
        corrected.groupby(['Effort_stratum', 'Cluster'])[['R1.Start', 'Comment_density']].agg(['count', 'mean', 'median']).to_excel(writer, sheet_name='Corrected_effort_strata')
    d['Effort_stratum'] = np.where(effort > median, 'Above median', 'At or below median')
    d['Median_high'] = (effort > median).astype(int)
    d['Disagrees_with_median'] = disagree
    summaries = d.groupby('Cluster')[['Effort_Total', 'R1.Start', 'Comment_density', 'Mean_HW', 'Mid', 'Final']].agg(['count', 'mean', 'median', 'std'])
    strata = d.groupby(['Effort_stratum', 'Cluster'])[['Effort_Total', 'R1.Start', 'Comment_density']].agg(['count', 'mean', 'median'])
    confusion = pd.crosstab(d.Cluster, d.Median_high)
    # Descriptive effort-adjusted contrast; no post-selection significance test.
    basis = np.asarray(patsy.dmatrix("1 + cr(e, df=3, constraints='center')", {'e': np.log1p(effort)}))
    residual_rows = []
    for col in ['R1.Start', 'Comment_density']:
        y = d[col].to_numpy(float)
        residual = y - basis @ np.linalg.lstsq(basis, y, rcond=None)[0]
        full = np.c_[basis, high.astype(int)]
        residual_rows.append(dict(variable=col, original_high_minus_low=float(y[high].mean() - y[~high].mean()),
                                  residual_high_minus_low=float(residual[high].mean() - residual[~high].mean()),
                                  residual_contrast_in_residual_SD=float((residual[high].mean() - residual[~high].mean()) / residual.std(ddof=1)),
                                  adjusted_cluster_coefficient=float(np.linalg.lstsq(full, y, rcond=None)[0][-1])))
    residuals = pd.DataFrame(residual_rows)
    # Anonymized local data table uses original Index, not direct student IDs.
    cols = ['Index', 'Effort_Total', 'Cluster', 'R1.Start', 'R1_MF_Count', 'R2_MF_Count', 'Comment_density',
            'Median_high', 'Disagrees_with_median', 'Effort_stratum', 'Pre', 'Mid', 'Final', 'Mean_HW'] + homework
    cases = d.loc[disagree, cols].sort_values('Effort_Total')
    changes = d.loc[d.Cluster.to_numpy() != historical, cols].copy()
    changes['Historical_Cluster'] = historical[d.Cluster.to_numpy() != historical]
    cases.to_csv(out / 'eleven_disagreement_cases.csv', index=False)
    changes.to_csv(out / 'ten_label_version_changes.csv', index=False)
    strata.to_csv(out / 'effort_stratum_summaries.csv')
    summaries.to_csv(out / 'group_summaries.csv')
    residuals.to_csv(out / 'descriptive_effort_adjustment.csv', index=False)
    with pd.ExcelWriter(out / 'figure_R1_analysis.xlsx') as writer:
        d[cols].to_excel(writer, sheet_name='Plot_data_no_ID', index=False)
        cases.to_excel(writer, sheet_name='Eleven_disagreements', index=False)
        changes.to_excel(writer, sheet_name='Ten_label_changes', index=False)
        summaries.to_excel(writer, sheet_name='Group_summaries')
        strata.to_excel(writer, sheet_name='Effort_strata')
        confusion.to_excel(writer, sheet_name='Cluster_vs_median')
        residuals.to_excel(writer, sheet_name='Descriptive_adjustment', index=False)
        pd.DataFrame(version_rows).to_excel(writer, sheet_name='Label_versions', index=False)
    metadata = dict(primary_input=str(chart_path), worksheet='Sheet 1',
                    homework_columns=homework, homework_mean_definition='Mean_HW = mean(HW1-HW6)',
                    historical_workbook_usage='Historical labels only; no historical scores imported',
                    cluster_label_source='Saved Cluster column in primary input; no refitting',
                    clustering_refitted=False,
                    corrected_group_sizes=corrected.Cluster.value_counts().sort_index().to_dict(),
                    corrected_median_disagreements=int(corrected.Disagrees_with_median.sum()),
                    median=float(median), tie_policy='High > median; low <= median',
                    density_definition='(R1_MF_Count + R2_MF_Count) / Effort_Total',
                    chart_vs_median_ARI=float(adjusted_rand_score(high, effort > median)),
                    label_version_warning='Chart labels differ for ten students from Merge-Data.xlsx labels',
                    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [chart_path, historical_path]})
    (out / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(pd.DataFrame(version_rows).to_string(index=False))
    print(strata.to_string())
    print(residuals.to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'New-Chart_input_clustering_results_clustered_data_k2.xlsx')
    parser.add_argument('--output', type=Path, default=ROOT / 'figure_R1_analysis')
    with threadpool_limits(limits=1):
        run(parser.parse_args())
