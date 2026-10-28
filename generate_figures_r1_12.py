"""Generate Figures R1 and 12 from the original matching 41/32 assignments.

Merge-Data.xlsx supplies values; output-cluster-with-score.xlsx independently
verifies every plotted behavior and saved label by student ID. No refitting.
"""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

ROOT = Path(__file__).resolve().parent
BLUE, RED = '#1e88e5', '#ef5350'
NAMES = {1: 'Extended Engagers', 2: 'Brief Participants'}
TEMPORAL = ['R1.Start', 'R1.End', 'R1.Dur', 'R2.Start', 'R2.End', 'R2.Dur']
SCORE_COLUMNS = ['HW1', 'HW3', 'HW4', 'HW5', 'HW6', 'HW7']


def save(fig, folder, name):
    folder.mkdir(parents=True, exist_ok=True)
    for ext in ['png', 'pdf']:
        fig.savefig(folder / f'{name}.{ext}', dpi=300, bbox_inches='tight')


def load_verified():
    primary, check = ROOT / 'Merge-Data.xlsx', ROOT / 'output-cluster-with-score.xlsx'
    d, other = pd.read_excel(primary), pd.read_excel(check)
    d.columns = d.columns.str.strip()
    if d.Id.isna().any() or other.Id.isna().any() or d.Id.duplicated().any() or other.Id.duplicated().any():
        raise ValueError('Source IDs must be present and unique')
    if set(d.Id) != set(other.Id):
        raise ValueError('Student sets differ between sources')
    other = other.set_index('Id').reindex(d.Id)
    columns = {c: c for c in ['Cluster', 'R1.Dur', 'R2.Dur']}
    columns.update({f'R{r}.{edge}': f'R{r}.Time.To.{edge}' for r in (1, 2) for edge in ('Start', 'End')})
    columns.update({f'R{r}_MF_Count': f'R{r}.MF' for r in (1, 2)})
    counts = [f'R{r}.C{i}.Sub' for r in (1, 2) for i in (1, 2, 3)]
    columns.update({c: c for c in counts})
    for a, b in columns.items():
        np.testing.assert_allclose(d[a].to_numpy(), other[b].to_numpy(), err_msg=f'Source mismatch: {a}')
    if d.Cluster.value_counts().to_dict() != {1: 41, 2: 32}:
        raise ValueError('Expected original saved groups of 41 and 32')
    np.testing.assert_allclose(d.Effort_Total, d[counts].sum(axis=1))
    if not (d.Effort_Total > 0).all():
        raise ValueError('Density denominators must be positive')
    d['Comment_density'] = (d.R1_MF_Count + d.R2_MF_Count) / d.Effort_Total
    # Same six-column score definition as the primary Table 6 score row.
    # Preserve the source's separate seven-column Mean_HW value in exports.
    if not d.HW1.eq(d.HW2).all():
        raise ValueError('Six-column Table 6 score definition requires checking HW1/HW2 provenance')
    d['Mean_assignment_score_6'] = d[SCORE_COLUMNS].mean(axis=1)
    d['Stored_Cluster'] = d.Cluster
    d['Median_high'] = d.Effort_Total.gt(d.Effort_Total.median()).astype(int)
    d['Disagrees_with_median'] = d.Cluster.eq(1).ne(d.Median_high.astype(bool))
    return d, [primary, check]


def make_r1(d, out):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, col, ylabel in zip(axes, ['Mean_assignment_score_6', 'Comment_density'],
                              ['Mean assignment score', 'Meaningful comments / review submissions']):
        for c, color, marker in [(1, BLUE, 'o'), (2, RED, '^')]:
            group = d.loc[d.Cluster == c]
            ax.scatter(group.Effort_Total, group[col], s=25, color=color, marker=marker, zorder=3)
        circled = d.loc[d.Disagrees_with_median]
        ax.scatter(circled.Effort_Total, circled[col], s=95, facecolors='none', edgecolors='black', zorder=4)
        median = d.Effort_Total.median()
        ax.axvline(median, color='grey', ls='--')
        ax.text(median + 7, .97, f'median = {median:g}', transform=ax.get_xaxis_transform(), va='top', color='dimgray', fontsize=9)
        ax.set(xlabel='Composite effort score (total review submissions)', ylabel=ylabel)
        ax.grid(axis='y', alpha=.2); ax.spines[['top', 'right']].set_visible(False)
    handles = [Line2D([], [], ls='', marker='o', color=BLUE, label='Extended Engagers (n=41)'),
               Line2D([], [], ls='', marker='^', color=RED, label='Brief Participants (n=32)'),
               Line2D([], [], ls='', marker='o', color='black', markerfacecolor='none', label=f'Cluster and median split disagree (n={d.Disagrees_with_median.sum()})')]
    fig.legend(handles=handles, loc='lower center', ncol=3, fontsize=9)
    fig.tight_layout(rect=(0, .1, 1, 1))
    for name in ['Figure_R1', 'figure_R1_alternative_corrected', 'figure_R1_stored_chart', 'figure_R1_historical_original']:
        save(fig, out, name)
    plt.close(fig)


def make_confusion_matrix(d, out):
    matrix = pd.crosstab(d.Cluster, d.Median_high).reindex(index=[1, 2], columns=[1, 0], fill_value=0)
    fig, ax = plt.subplots(figsize=(6.8, 5.3))
    ax.imshow(matrix.to_numpy(), cmap='Blues', vmin=0, vmax=max(matrix.to_numpy().max(), 1))
    ax.set(xticks=[0, 1], xticklabels=['High effort (>364)\n(n=36)', 'Low effort (<=364)\n(n=37)'],
           yticks=[0, 1], yticklabels=['Extended Engagers\n(n=41)', 'Brief Participants\n(n=32)'],
           xlabel='Effort median split', ylabel='Saved cluster assignment',
           title='Cluster solution versus effort median split')
    threshold = matrix.to_numpy().max() / 2
    for i in range(2):
        for j in range(2):
            count = int(matrix.iloc[i, j])
            ax.text(j, i, str(count), ha='center', va='center', fontsize=24,
                    color='white' if count > threshold else 'black')
    agreement = int(matrix.iloc[0, 0] + matrix.iloc[1, 1])
    fig.text(.5, .02, f'Agreement: {agreement}/73 ({agreement / 73:.1%}); disagreements: {73 - agreement}\nNeither partition is an independently known ground truth.',
             ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .1, 1, 1))
    save(fig, out, 'Confusion_Matrix_Cluster_vs_Median_Split')
    matrix.index = ['Extended Engagers', 'Brief Participants']
    matrix.columns = ['High effort (>364)', 'Low effort (<=364)']
    matrix.to_csv(out / 'Confusion_Matrix_Cluster_vs_Median_Split.csv')
    plt.close(fig)


def make_fig12(d, out):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.7))
    for ax, cols, labels, title, ylabel in [
        (axes[0], ['R1.Dur', 'R2.Dur'], ['Round 1', 'Round 2'], '(a) Review duration by cluster', 'Mean duration (recorded time units)'),
        (axes[1], ['R1.Start', 'R1.End', 'R2.Start', 'R2.End'], ['R1 Start', 'R1 End', 'R2 Start', 'R2 End'], '(b) Review timing by cluster', 'Mean time (recorded time units)')]:
        x = np.arange(len(cols))
        for c, color, offset in [(1, BLUE, -.175), (2, RED, .175)]:
            group = d.loc[d.Cluster == c, cols]
            bars = ax.bar(x + offset, group.mean(), .35, yerr=group.sem(), capsize=4, color=color,
                          alpha=.85, label=f'{NAMES[c]} (n={len(group)})')
            if ax is axes[0]:
                for bar in bars:
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3, f'{bar.get_height():.1f}', ha='center', fontsize=8)
        ax.set(xticks=x, xticklabels=labels, title=title, ylabel=ylabel)
        ax.grid(axis='y', alpha=.2); ax.set_axisbelow(True); ax.legend(fontsize=8)
    fig.suptitle('Fig. 12. Temporal Engagement Features by Cluster (R1 & R2)')
    fig.tight_layout()
    save(fig, out, 'Fig12_Temporal_Engagement_Features')
    plt.close(fig)


def main():
    d, sources = load_verified()
    out = ROOT / 'figure_R1_analysis'
    out.mkdir(exist_ok=True)
    make_r1(d, out)
    make_confusion_matrix(d, out)
    make_fig12(d, ROOT / 'Cluster-Profile-Figures')
    export = d.drop(columns='Id')
    temporal = d.groupby('Cluster')[TEMPORAL].agg(['count', 'mean', 'std', 'sem', 'median'])
    groups = d.groupby('Cluster')[['Effort_Total', 'Mean_assignment_score_6', 'R1.Start', 'Comment_density', 'Mean_HW']].agg(['count', 'mean', 'std', 'median'])
    strata = d.assign(Effort_stratum=np.where(d.Median_high == 1, 'Above median', 'At or below median')).groupby(
        ['Effort_stratum', 'Cluster'])[['Effort_Total', 'Mean_assignment_score_6', 'R1.Start', 'Comment_density']].agg(['count', 'mean', 'median'])
    cases = export.loc[export.Disagrees_with_median].sort_values('Effort_Total')
    confusion = pd.crosstab(d.Cluster, d.Median_high)
    for filename in ['figures_R1_12_data.xlsx', 'figure_R1_analysis.xlsx', 'figure_R1_alternative_corrected_data.xlsx']:
        with pd.ExcelWriter(out / filename) as writer:
            export.to_excel(writer, sheet_name='Plot_data_no_ID', index=False)
            cases.to_excel(writer, sheet_name='Disagreement_cases', index=False)
            temporal.to_excel(writer, sheet_name='Figure12_statistics')
            groups.to_excel(writer, sheet_name='R1_group_summaries')
            strata.to_excel(writer, sheet_name='Effort_strata')
            confusion.to_excel(writer, sheet_name='Cluster_vs_median')
    export.to_csv(out / 'figure_R1_alternative_corrected_data.csv', index=False)
    cases.to_csv(out / 'median_split_disagreements.csv', index=False)
    temporal.to_csv(out / 'Figure12_statistics.csv')
    groups.to_csv(out / 'group_summaries.csv')
    strata.to_csv(out / 'effort_stratum_summaries.csv')
    meta = dict(primary_input=str(sources[0]), verification_input=str(sources[1]),
                label_source='Matching saved Cluster columns in both source workbooks',
                clustering_refitted=False, group_sizes={'1': 41, '2': 32},
                median=float(d.Effort_Total.median()), median_high_rule='Effort_Total > median',
                disagreements=int(d.Disagrees_with_median.sum()),
                median_agreement=float((~d.Disagrees_with_median).mean()),
                ARI=float(adjusted_rand_score(d.Cluster, d.Median_high)),
                density='(R1_MF_Count + R2_MF_Count) / Effort_Total',
                figure_R1_left_y='Mean_assignment_score_6',
                figure_R1_right_y='Comment_density',
                figure_R1_score_columns=SCORE_COLUMNS,
                figure_R1_score_definition='Mean of HW1 and HW3-HW7, matching primary Table 6; HW2 duplicates HW1',
                time_units='Raw recorded units, no conversion; minutes/seconds not asserted',
                figure12_error_bars='Sample standard error, SD / sqrt(n); SD also exported',
                sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    (out / 'metadata.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    notes = f'''# Current Figure R1 and Figure 12 sources

Both figures use Merge-Data.xlsx values and saved Cluster assignments, verified
student-by-student against output-cluster-with-score.xlsx using Id. All plotted
behavioral values and all 73 labels agree across both files. No clustering is refitted.
Source columns with trailing spaces are normalized by stripping column names.

Groups: Extended Engagers 41; Brief Participants 32. These are the original
assignments matching Table 4, not the different 41/32 New-Chart assignments.

Figure R1: median effort 364; high effort >364. Five students disagree with the
median split; 68/73 agree (93.15%, ARI={meta['ARI']:.3f}). All five are Extended
students at or below the median. There are no high-effort Brief students.
The earlier eleven-circle interpretation and its timing/density contrasts are
superseded for these selected sources. Do not claim that the eleven New-Chart
cases establish additional behavioral profiles for this partition.

Figure R1 left panel now plots mean assignment score, not review start time.
It averages HW1 and HW3-HW7, matching the six-column definition in Table 6.
The recorded HW1 and HW2 values are identical for every student; HW2 is excluded
from this score definition, with no alteration of the source workbook. Group
score means are 88.74 and 69.85. The stored seven-column Mean_HW is exported
separately and is not the score plotted on this figure. The right panel plots
meaningful-comment density. Panel titles are omitted as requested.

Suggested caption: "Figure R1. Composite effort score against (a) mean assignment
score and (b) meaningful-comment density, by cluster. Mean assignment score
averages HW1 and HW3-HW7, as in Table 6. The dashed line marks median effort
(364); circles mark the five students whose saved cluster assignment differs
from the effort median split."

Figure 12 plots means with standard errors. For R1 start the means are 1271.34
and 596.57; R1 end 1370.45 and 649.70; R1 duration 99.05 and 52.96. Table 4's
descriptive values agree, apart from rounding/truncation. Table 4 reports SD;
Figure 12 reports SE, so their dispersion bars/columns differ by definition.

Figure 12 time values are plotted without conversion and labeled recorded
time units rather than making conflicting seconds/minutes claims.
The physical time unit still requires verification from source documentation.

Density equals total R1/R2 meaningful-comment counts divided by total six-category
submission counts. Denominators are positive for all students. The figure is
descriptive; comparisons on clustering inputs are not independent validation.

Authoritative exports: figures_R1_12_data.xlsx, Figure12_statistics.csv,
median_split_disagreements.csv and metadata.json. The existing
figure_R1_alternative_corrected PNG/PDF/data filenames are compatibility aliases
for this same original saved-label solution. Older New-Chart outputs and code
in Previous Data are superseded for the two requested figures. Other figures
have not been regenerated by this script.

Reproduce: python Cluster-Analysis/generate_figures_r1_12.py
'''
    for filename in ['FIGURE_R1_EXPLANATION.md', 'CORRECTED_FIGURE_DATA.md', 'CURRENT_SOURCE.md']:
        (out / filename).write_text(notes, encoding='utf-8')
    print(json.dumps(meta, indent=2))
    print(temporal.to_string())


if __name__ == '__main__':
    main()
