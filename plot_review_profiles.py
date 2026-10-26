"""Port of four R boxplot scripts and the score comparison chart.

Labels remain neutral unless interpreting the historical workbook explicitly.
Score SEs are calculated from observations, never copied from hypothetical R SEs.
"""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path(__file__).parent / 'output-cluster-with-score.xlsx')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'python_profile_figures')
    parser.add_argument('--scores-input', type=Path, default=Path(__file__).parent / 'Merge-Data.xlsx',
                        help='Separate historical workbook for score chart; uses its own Cluster assignments')
    args = parser.parse_args()
    df = pd.read_excel(args.input)
    args.output.mkdir(parents=True, exist_ok=True)
    groups = sorted(df.Cluster.dropna().unique())
    for round_ in (1, 2):
        for kind, columns in [('submissions', [f'R{round_}.C{i}.Sub' for i in (1, 2, 3)] + [f'R{round_}.MF']),
                              ('time', [f'R{round_}.Time.To.Start', f'R{round_}.Time.To.End', f'R{round_}.Dur'])]:
            missing = set(columns) - set(df.columns)
            if missing:
                raise ValueError(f'Missing columns: {missing}')
            fig, axes = plt.subplots(len(columns), 1, figsize=(9, 2.4 * len(columns)))
            for ax, column in zip(axes, columns):
                data = [df.loc[df.Cluster == c, column].dropna() for c in groups]
                ax.boxplot(data, vert=False, labels=[f'Cluster {c}' for c in groups], patch_artist=True)
                ax.set(title=column, xlabel='Time (minutes)' if kind == 'time' else 'Submission count')
                ax.grid(axis='x', alpha=.2)
            fig.tight_layout()
            for ext in ('png', 'pdf'):
                fig.savefig(args.output / f'R{round_}_{kind}.{ext}', dpi=300)
            plt.close(fig)
    if args.scores_input:
        df = pd.read_excel(args.scores_input)
        groups = sorted(df.Cluster.dropna().unique())
    scores = [c for c in ['HW1', 'HW2', 'HW3', 'HW4', 'HW5', 'HW6', 'HW7', 'Midterm', 'Mid', 'Final'] if c in df]
    if scores:
        stats = df.groupby('Cluster')[scores].agg(['count', 'mean', 'std', 'sem'])
        stats.to_excel(args.output / 'score_summary.xlsx')
        fig, ax = plt.subplots(figsize=(11, 5))
        width = .8 / len(groups)
        for i, c in enumerate(groups):
            sub = df.loc[df.Cluster == c, scores]
            se = sub.sem()
            # With n<2, SE is undefined; do not draw a fabricated zero error bar.
            x = np.arange(len(scores)) + (i - (len(groups) - 1) / 2) * width
            ax.bar(x, sub.mean(), width, label=f'Cluster {c}')
            valid = se.notna()
            ax.errorbar(x[valid], sub.mean()[valid], yerr=se[valid], fmt='none', color='black', capsize=3)
        ax.set(xticks=np.arange(len(scores)), xticklabels=scores, ylabel='Mean score')
        ax.legend(); fig.tight_layout()
        for ext in ('png', 'pdf'):
            fig.savefig(args.output / f'academic_performance.{ext}', dpi=300)
        plt.close(fig)


if __name__ == '__main__':
    main()
