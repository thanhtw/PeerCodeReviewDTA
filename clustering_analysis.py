"""Python port of both R clustering workflows; explicit, auditable gap rules."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.spatial.distance import pdist
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, silhouette_samples, adjusted_rand_score
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parent
FEATURES = ['R1.C1.Sub', 'R1.C2.Sub', 'R1.C3.Sub', 'R2.C1.Sub',
            'R2.C2.Sub', 'R2.C3.Sub', 'R1.Time.To.Start', 'R1.Time.To.End',
            'R1.Dur', 'R1.MF', 'R2.Time.To.Start', 'R2.Time.To.End', 'R2.Dur', 'R2.MF']
# Preserve the duplicate Effort_R1 in the alternative R script deliberately.
ALTERNATIVE = ['Effort_R1', 'Effort_R1', 'R1.Dur', 'R2.Dur', 'R1.Start',
               'R1.End', 'R2.Start', 'R2.End', 'MF_Ratio_R1', 'MF_Ratio_R2']


def select_gap(gap, se, method='Tibs2001SEmax'):
    """Return 1-based k; Kmax is a boundary fallback if no earlier match exists."""
    gap, se = np.asarray(gap), np.asarray(se)
    if gap.ndim != 1 or len(gap) < 2 or gap.shape != se.shape:
        raise ValueError('Need equally sized gap and SE vectors with at least two k values')
    if not np.isfinite(gap).all() or not np.isfinite(se).all() or (se < 0).any():
        raise ValueError('Gap and SE must be finite; SE must be nonnegative')
    if method == 'globalmax':
        return int(np.argmax(gap) + 1)
    if method == 'Tibs2001SEmax':
        matches = np.flatnonzero(gap[:-1] >= gap[1:] - se[1:])
        return int(matches[0] + 1) if len(matches) else len(gap)
    if method == 'firstSEmax':
        decreases = np.flatnonzero(np.diff(gap) <= 0)
        peak = int(decreases[0]) if len(decreases) else len(gap) - 1
        return int(np.flatnonzero(gap[:peak + 1] >= gap[peak] - se[peak])[0] + 1)
    raise ValueError(method)


def fit(x, k, seed):
    # Elkan computes the same Euclidean objective while avoiding repeated BLAS
    # discovery overhead in older sklearn Lloyd implementations on Windows.
    return KMeans(k, n_init=25 if k > 1 else 1, max_iter=300,
                  algorithm='elkan' if k > 1 else 'lloyd', random_state=int(seed)).fit(x)


def dispersion(x, labels, power):
    """clusGap convention: 0.5 * sum_r sum_{i<j} d(i,j)^power / n_r.

    Default power=1 matches R clusGap, rather than silently using inertia.
    For power=2 this equals one half of k-means inertia (gap unaffected).
    """
    value = sum(0.5 * np.sum(pdist(x[labels == c]) ** power) / np.sum(labels == c)
                for c in np.unique(labels))
    if value <= 0:
        raise ValueError('Zero dispersion; reduce maximum k or inspect duplicate rows')
    return value


def gap_statistic(x, max_k, b, seed, power):
    rng = np.random.default_rng(seed)
    models = [fit(x, k, rng.integers(2**31)) for k in range(1, max_k + 1)]
    observed = np.log([dispersion(x, m.labels_, power) for m in models])
    center = x.mean(axis=0)
    _, _, vt = np.linalg.svd(x - center, full_matrices=False)
    rotated = (x - center) @ vt.T
    low, high = rotated.min(axis=0), rotated.max(axis=0)
    reference = np.empty((b, max_k))
    for i in range(b):
        z = rng.uniform(low, high, size=x.shape) @ vt + center
        for k in range(1, max_k + 1):
            model = fit(z, k, rng.integers(2**31))
            reference[i, k - 1] = np.log(dispersion(z, model.labels_, power))
        if (i + 1) % 50 == 0:
            print(f'Reference datasets: {i + 1}/{b}', flush=True)
    table = pd.DataFrame({'k': range(1, max_k + 1), 'logW': observed,
                          'E_logW': reference.mean(axis=0),
                          'gap': reference.mean(axis=0) - observed,
                          'SE_sim': reference.std(axis=0, ddof=1) * np.sqrt(1 + 1 / b),
                          'wss': [m.inertia_ for m in models],
                          'silhouette': [np.nan] + [silhouette_score(x, m.labels_) for m in models[1:]]})
    table['next_gap_minus_SE'] = (table.gap - table.SE_sim).shift(-1)
    table['decision_margin'] = table.gap - table.next_gap_minus_SE
    table['Tibs_condition'] = table.decision_margin.ge(0).astype('boolean')
    table.loc[max_k - 1, 'Tibs_condition'] = pd.NA
    return table, reference, models


def save_plot(fig, out, name):
    fig.tight_layout()
    for ext in ('png', 'pdf'):
        fig.savefig(out / f'{name}.{ext}', dpi=300)
    plt.close(fig)


def run(args):
    if args.references < 2:
        raise ValueError('At least two reference datasets required')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = args.input or ROOT / ('Merge-Data.xlsx' if args.profile != 'original' else 'input-data.xlsx')
    df = pd.read_excel(source)
    features = FEATURES if args.profile == 'original' else ALTERNATIVE.copy()
    if args.profile == 'alternative-corrected':
        features[1] = 'Effort_R2'
    values = df[features].apply(pd.to_numeric, errors='raise')
    keep = np.isfinite(values.to_numpy()).all(axis=1)
    df, values = df.loc[keep].copy(), values.loc[keep]
    if not 2 <= args.max_k < len(values):
        raise ValueError('Require 2 <= max-k < complete observations')
    sd = values.std(ddof=1)
    if (sd == 0).any():
        raise ValueError('Constant features cannot be standardized')
    scaled = (values - values.mean()) / sd
    pca = PCA(svd_solver='full').fit(scaled)
    x = pca.transform(scaled)[:, :3]
    table, references, models = gap_statistic(x, args.max_k, args.references, args.seed, args.power)
    choices = {m: select_gap(table.gap, table.SE_sim, m)
               for m in ('Tibs2001SEmax', 'firstSEmax', 'globalmax')}
    choices['silhouette'] = int(table.loc[table.silhouette.idxmax(), 'k'])
    selected = choices['Tibs2001SEmax']
    model = models[selected - 1]
    df['Cluster'] = model.labels_ + 1
    scores = pd.DataFrame(x, columns=['PC1', 'PC2', 'PC3'], index=df.index)
    scores['Cluster'] = df.Cluster
    df['Source_Excel_Row'] = df.index + 2
    summary = df.groupby('Cluster')[list(dict.fromkeys(features))].agg(['count', 'mean', 'std', 'median'])
    table.to_csv(out / 'cluster_selection.csv', index=False)
    pd.DataFrame(references, columns=range(1, args.max_k + 1)).to_csv(out / 'reference_logW.csv', index=False)
    variance = pd.DataFrame({'PC': np.arange(1, len(pca.explained_variance_ratio_) + 1),
                            'variance_ratio': pca.explained_variance_ratio_})
    loadings = pd.DataFrame(pca.components_[:3].T, index=features, columns=['PC1', 'PC2', 'PC3'])
    with pd.ExcelWriter(out / 'clustering_results.xlsx') as writer:
        df.to_excel(writer, sheet_name='Clustered_data', index=False)
        scores.to_excel(writer, sheet_name='PCA_scores', index=False)
        table.to_excel(writer, sheet_name='Cluster_selection', index=False)
        summary.to_excel(writer, sheet_name='Feature_profiles')
        variance.to_excel(writer, sheet_name='PCA_variance', index=False)
        loadings.to_excel(writer, sheet_name='PCA_loadings')
    # Initialization sensitivity is distinct from sampling stability.
    stability = []
    for k in range(2, min(4, args.max_k) + 1):
        baseline = models[k - 1].labels_
        for seed in range(20):
            stability.append({'k': k, 'seed': seed,
                              'ARI_vs_baseline': adjusted_rand_score(baseline, fit(x, k, seed).labels_)})
    pd.DataFrame(stability).to_csv(out / 'initialization_sensitivity.csv', index=False)
    metadata = dict(profile=args.profile, input=str(source.resolve()),
                    input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    n=len(df), excluded_rows=int((~keep).sum()), features=features,
                    references=args.references, seed=args.seed, d_power=args.power,
                    spaceH0='scaledPCA', n_init=25, max_iter=300, algorithm='elkan (lloyd for k=1)', selected_k=selected,
                    recommendations=choices, retained_variance=float(pca.explained_variance_ratio_[:3].sum()))
    import sklearn, scipy
    metadata['versions'] = dict(numpy=np.__version__, pandas=pd.__version__,
                                sklearn=sklearn.__version__, scipy=scipy.__version__)
    (out / 'run_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(table.k, table.gap, yerr=table.SE_sim, fmt='o-', capsize=4, label='Gap ± s(k)')
    ax.axvline(selected, ls='--', color='black', label=f'Tibshirani 1-SE: k={selected}')
    ax.set(xlabel='Number of clusters k', ylabel='Gap statistic', xticks=table.k)
    ax.legend(); ax.grid(alpha=.2)
    save_plot(fig, out, 'figure4_gap_statistic')
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, col in zip(axes, ['wss', 'silhouette', 'gap']):
        ax.plot(table.k, table[col], 'o-'); ax.set(xlabel='k', ylabel=col, xticks=table.k)
    save_plot(fig, out, 'selection_diagnostics')
    fig, ax = plt.subplots()
    ax.scatter(x[:, 0], x[:, 1], c=model.labels_, cmap='tab10')
    ax.set(xlabel='PC1', ylabel='PC2', title=f'K-means, k={selected}')
    save_plot(fig, out, 'pca_clusters')
    fig = px.scatter_3d(scores.assign(Cluster=scores.Cluster.astype(str)), x='PC1', y='PC2', z='PC3', color='Cluster')
    fig.write_html(out / 'pca_clusters_3d.html', include_plotlyjs=True)
    fig, ax = plt.subplots()
    ax.bar(variance.PC, variance.variance_ratio * 100)
    ax.set(xlabel='Principal component', ylabel='Explained variance (%)')
    save_plot(fig, out, 'pca_variance')
    if selected > 1:
        fig, ax = plt.subplots()
        sil = silhouette_samples(x, model.labels_)
        start = 0
        for c in range(selected):
            vals = np.sort(sil[model.labels_ == c]); stop = start + len(vals)
            ax.fill_betweenx(np.arange(start, stop), 0, vals, alpha=.7, label=f'Cluster {c + 1}')
            start = stop + 3
        ax.axvline(sil.mean(), ls='--', color='black'); ax.set(xlabel='Silhouette width', ylabel='Observations'); ax.legend()
        save_plot(fig, out, 'silhouette_clusters')
    report = f'''# Cluster selection: computed Python reanalysis

Input: {source.name}; profile: {args.profile}; complete observations: {len(df)}.
Three PCs retain {metadata['retained_variance']:.2%} of standardized variance.
B={args.references}, seed={args.seed}, d.power={args.power}, scaledPCA reference box.

Recommendations: {json.dumps(choices)}. Primary selection: k={selected}.

Tibshirani's rule selects the smallest k satisfying Gap(k) >= Gap(k+1) - s(k+1).
s(k) = sqrt(1 + 1/B) * sample_SD(reference log W(k)); it is not SD/sqrt(B).
The CSV includes every adjacent comparison and its margin; the final k has no
next-k comparison. Selection at the upper boundary requires extending the range.

First comparisons:
{table[['k', 'gap', 'SE_sim', 'next_gap_minus_SE', 'decision_margin']].head(3).to_string(index=False)}

The original R scripts use firstSEmax by default and ultimately select silhouette's
recommendation. The Python primary rule is explicitly Tibs2001SEmax. This change
must be described as a reanalysis, not retrospectively attributed to the original.
These results are not the exact numerical data underlying the supplied Figure 4:
R/Python random generators, k-means solvers and Monte Carlo draws differ.
Overlapping gap bars neither constitute a pairwise significance test nor establish
that the clusters are unstable. The adjacent 1-SE comparison favors parsimony.
Initialization ARI results assess optimizer sensitivity only; they do not establish
sampling stability, external validity, or the existence of discrete populations.
See ../CLUSTER_SELECTION.md for reviewer wording and interpretation.
'''
    (out / 'selection_report.md').write_text(report, encoding='utf-8')
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'python_results')
    parser.add_argument('--profile', choices=['original', 'alternative-legacy', 'alternative-corrected'], default='original')
    parser.add_argument('--references', type=int, default=500)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--max-k', type=int, default=10)
    parser.add_argument('--power', type=int, choices=[1, 2], default=1)
    with threadpool_limits(limits=1):
        run(parser.parse_args())
