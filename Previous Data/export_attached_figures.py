import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


BLUE = "#1e88e5"
RED = "#ef5350"
GREEN = "#43a047"


def sem(series: pd.Series) -> float:
    n = series.notna().sum()
    if n <= 1:
        return 0.0
    return float(series.std(ddof=1) / np.sqrt(n))


def detect_label_map(df: pd.DataFrame) -> dict:
    counts = df["Cluster"].value_counts().to_dict()
    if set(counts.keys()) == {1, 2}:
        return {1: "Extended Engagers", 2: "Brief Participants"}

    sorted_keys = sorted(counts, key=counts.get, reverse=True)
    label_map = {}
    if sorted_keys:
        label_map[sorted_keys[0]] = "Extended Engagers"
    if len(sorted_keys) > 1:
        label_map[sorted_keys[1]] = "Brief Participants"
    for k in sorted_keys[2:]:
        label_map[k] = f"Cluster {k}"
    return label_map


def style_axes(ax):
    ax.grid(True, alpha=0.25)
    ax.set_facecolor("#f5f5f5")


def fig6_trajectory(df: pd.DataFrame, out_dir: Path, label_map: dict):
    hw_cols = ["HW1", "HW2", "HW3", "HW4", "HW5", "HW6"]
    x = np.arange(1, len(hw_cols) + 1)

    fig, ax = plt.subplots(figsize=(6.4, 4.8), dpi=150)

    for cluster, color, marker in [(1, BLUE, "o"), (2, RED, "s")]:
        if cluster not in set(df["Cluster"]):
            continue
        group = df[df["Cluster"] == cluster]
        means = [group[c].mean() for c in hw_cols]
        errs = [sem(group[c]) for c in hw_cols]
        n = len(group)
        label = f"{label_map.get(cluster, f'Cluster {cluster}')} (n={n})"
        ax.errorbar(
            x,
            means,
            yerr=errs,
            color=color,
            marker=marker,
            linewidth=1.6,
            markersize=4.5,
            capsize=3,
            label=label,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(hw_cols)
    ax.set_ylim(50, 105)
    ax.set_xlabel("Assignment")
    ax.set_ylabel("Mean Score")
    ax.set_title("Fig. 6. Academic Performance Trajectories by Engagement Cluster")
    style_axes(ax)

    ext = df[df["Cluster"] == 1]
    brief = df[df["Cluster"] == 2]
    if not ext.empty and not brief.empty:
        x_arrow = 4
        y_ext = ext["HW4"].mean()
        y_brief = brief["HW5"].mean()
        ax.annotate(
            "Performance gap\nwidens from HW4",
            xy=(x_arrow, y_ext - 12),
            xytext=(5.5, min(y_brief - 10, 55)),
            arrowprops={"arrowstyle": "->", "color": "gray", "lw": 1},
            fontsize=9,
            color="gray",
        )

    ax.legend(loc="lower left", frameon=True)
    fig.tight_layout()
    fig.savefig(out_dir / "Fig6_Academic_Performance_Trajectories.png", dpi=300)
    fig.savefig(out_dir / "Fig6_Academic_Performance_Trajectories.pdf")
    plt.close(fig)


def fig7_radar(df: pd.DataFrame, out_dir: Path, label_map: dict, r1_mf_col: str, r2_mf_col: str):
    metrics = [
        ("R1.C3.Sub", "Doc (R1)"),
        ("R1.C2.Sub", "Read (R1)"),
        ("R1.C1.Sub", "Func (R1)"),
        (r2_mf_col, "Meaningful (R2)"),
        (r1_mf_col, "Meaningful (R1)"),
        ("R2.C3.Sub", "Doc (R2)"),
        ("R2.C2.Sub", "Read (R2)"),
        ("R2.C1.Sub", "Func (R2)"),
    ]

    cols = [m[0] for m in metrics]
    labels = [m[1] for m in metrics]

    cluster_means = df.groupby("Cluster")[cols].mean()
    max_vals = cluster_means.max(axis=0).replace(0, 1)
    normalized = cluster_means.divide(max_vals, axis=1)

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6.4, 5.8), subplot_kw={"projection": "polar"}, dpi=150)

    # Use fixed group names for clusters 1 and 2
    group_names = {1: "Extended Engagers", 2: "Brief Participants"}

    for cluster, color, marker in [(1, BLUE, "o"), (2, RED, "s")]:
        if cluster not in normalized.index:
            continue
        values = normalized.loc[cluster].tolist()
        values += values[:1]
        label = group_names.get(cluster, label_map.get(cluster, str(cluster)))
        ax.plot(angles, values, color=color, linewidth=1.5, marker=marker, markersize=4.5, label=label)
        ax.fill(angles, values, color=color, alpha=0.18)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"])
    # Remove the title for this figure
    # ax.set_title("Fig. 7. Behavioral Feature Profiles by Cluster", pad=15)
    # Move legend inside plot area to the upper left for better visibility of long group names
    ax.legend(loc="upper left", bbox_to_anchor=(0.05, 1.05), frameon=True)
    fig.tight_layout()
    fig.savefig(out_dir / "Fig7_Behavioral_Feature_Profiles_Radar.png", dpi=300)
    fig.savefig(out_dir / "Fig7_Behavioral_Feature_Profiles_Radar.pdf")
    plt.close(fig)


def fig8_cross_dimension(df: pd.DataFrame, out_dir: Path):
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.6), dpi=150)
    pairs = [
        ("R1.C1.Sub", "R1.C2.Sub", "Functionality vs Readability"),
        ("R1.C1.Sub", "R1.C3.Sub", "Functionality vs Documentation"),
        ("R1.C2.Sub", "R1.C3.Sub", "Readability vs Documentation"),
    ]

    for ax, (xcol, ycol, title) in zip(axes, pairs):
        ext = df[df["Cluster"] == 1]
        brief = df[df["Cluster"] == 2]

        ax.scatter(ext[xcol], ext[ycol], color=BLUE, alpha=0.65, s=12, edgecolors="none", label="Extended")
        ax.scatter(brief[xcol], brief[ycol], color=RED, alpha=0.65, s=12, edgecolors="none", label="Brief")

        ext_r = ext[xcol].corr(ext[ycol]) if len(ext) > 1 else np.nan
        brief_r = brief[xcol].corr(brief[ycol]) if len(brief) > 1 else np.nan

        ann = f"Ext r≈{ext_r:.2f}\nBrief r≈{brief_r:.2f}"
        ax.text(0.03, 0.94, ann, transform=ax.transAxes, fontsize=6, va="top", bbox={"boxstyle": "round,pad=0.2", "fc": "wheat", "alpha": 0.4})

        ax.set_title(title, fontsize=8)
        ax.set_xlabel(f"{xcol.replace('R1.', '').replace('.Sub', '')} (R1 count)", fontsize=7)
        ax.set_ylabel(f"{ycol.replace('R1.', '').replace('.Sub', '')} (R1 count)", fontsize=7)
        ax.tick_params(labelsize=7)
        style_axes(ax)

    handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=BLUE, markersize=5, label="Extended"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=RED, markersize=5, label="Brief"),
    ]
    axes[0].legend(handles=handles, fontsize=6, loc="lower right", frameon=True)

    fig.suptitle("Fig. 8. Cross-Dimensional Review Patterns by Cluster", y=1.02, fontsize=9)
    fig.tight_layout()
    fig.savefig(out_dir / "Fig8_Cross_Dimensional_Review_Patterns.png", dpi=300, bbox_inches="tight")
    fig.savefig(out_dir / "Fig8_Cross_Dimensional_Review_Patterns.pdf", bbox_inches="tight")
    plt.close(fig)


def choose_representative_students(df: pd.DataFrame):
    hw_cols = ["HW1", "HW2", "HW3", "HW4", "HW5", "HW6"]

    ext = df[df["Cluster"] == 1].copy()
    brief = df[df["Cluster"] == 2].copy()

    ext["mean_hw"] = ext[hw_cols].mean(axis=1)
    ext["std_hw"] = ext[hw_cols].std(axis=1)

    brief["drop"] = brief["HW1"] - brief["HW6"]
    brief["mean_hw"] = brief[hw_cols].mean(axis=1)
    declining = brief.sort_values(["drop", "HW6"], ascending=[False, True]).iloc[0]

    # Prefer extended students whose mean score is higher than Student C.
    better_ext = ext[ext["mean_hw"] > declining["mean_hw"]].copy()
    if better_ext.empty:
        better_ext = ext.copy()

    stable = better_ext.sort_values(["std_hw", "mean_hw"], ascending=[True, False]).iloc[0]
    variable_pool = better_ext[better_ext["Id"] != stable["Id"]]
    if variable_pool.empty:
        variable_pool = better_ext
    variable = variable_pool.sort_values(["std_hw", "mean_hw"], ascending=[False, False]).iloc[0]

    return stable, variable, declining


def fig9_individual_trajectories(df: pd.DataFrame, out_dir: Path):
    hw_cols = ["HW1", "HW2", "HW3", "HW4", "HW5", "HW6"]
    x = np.arange(1, len(hw_cols) + 1)

    stable, variable, declining = choose_representative_students(df)

    fig, ax = plt.subplots(figsize=(6.4, 4.8), dpi=150)

    ax.plot(x, stable[hw_cols].values, color="#1565c0", marker="o", linewidth=1.8, label=f"Student A ({stable['Id']}, extended, stable)")
    ax.plot(x, variable[hw_cols].values, color=GREEN, marker="^", linewidth=1.8, label=f"Student B ({variable['Id']}, extended, variable)")
    ax.plot(x, declining[hw_cols].values, color="#e53935", marker="s", linewidth=1.8, label=f"Student C ({declining['Id']}, brief, declining)")

    ax.set_xticks(x)
    ax.set_xticklabels(hw_cols)
    ax.set_ylim(-5, 110)
    ax.set_xlabel("Assignment")
    ax.set_ylabel("Score")
    ax.set_title("Fig. 9. Individual Student Trajectories Across Assignments")
    style_axes(ax)
    ax.legend(loc="center right", frameon=True)

    fig.tight_layout()
    fig.savefig(out_dir / "Fig9_Individual_Student_Trajectories.png", dpi=300)
    fig.savefig(out_dir / "Fig9_Individual_Student_Trajectories.pdf")
    plt.close(fig)


def fig10_effort_feedback_performance(df: pd.DataFrame, out_dir: Path, r1_mf_col: str, r2_mf_col: str):
    fig, ax = plt.subplots(figsize=(6.6, 5.0), dpi=150)

    sizes = np.clip(df["Mean_HW"].values, 0, None) * 3.2
    ext = df[df["Cluster"] == 1]
    brief = df[df["Cluster"] == 2]

    ax.scatter(ext["Effort_Total"], ext[r1_mf_col] + ext[r2_mf_col], s=np.clip(ext["Mean_HW"], 0, None) * 3.2, color=BLUE, alpha=0.55, edgecolors="white", linewidths=0.8, label="Extended")
    ax.scatter(brief["Effort_Total"], brief[r1_mf_col] + brief[r2_mf_col], s=np.clip(brief["Mean_HW"], 0, None) * 3.2, color=RED, alpha=0.55, edgecolors="white", linewidths=0.8, label="Brief")

    ax.set_xlabel("Total Review Submissions (all dimensions, both rounds)")
    ax.set_ylabel("Total Meaningful Comments (R1 + R2)")
    ax.set_title("Fig. 10. Review Effort vs Feedback Quality vs Academic Performance")
    style_axes(ax)
    ax.legend(loc="upper right", frameon=True)
    ax.text(0.98, 0.03, "Bubble size = Mean HW score", transform=ax.transAxes, ha="right", va="bottom", color="gray", fontsize=9, style="italic")

    fig.tight_layout()
    fig.savefig(out_dir / "Fig10_Effort_Feedback_Performance_Bubble.png", dpi=300)
    fig.savefig(out_dir / "Fig10_Effort_Feedback_Performance_Bubble.pdf")
    plt.close(fig)


def fig11_effort_distribution(df: pd.DataFrame, out_dir: Path, label_map: dict):
    dims = ["Functionality", "Readability", "Documentation"]

    ext = df[df["Cluster"] == 1]
    brief = df[df["Cluster"] == 2]

    ext_vals = [
        (ext["R1.C1.Sub"] + ext["R2.C1.Sub"]).mean(),
        (ext["R1.C2.Sub"] + ext["R2.C2.Sub"]).mean(),
        (ext["R1.C3.Sub"] + ext["R2.C3.Sub"]).mean(),
    ]
    brief_vals = [
        (brief["R1.C1.Sub"] + brief["R2.C1.Sub"]).mean(),
        (brief["R1.C2.Sub"] + brief["R2.C2.Sub"]).mean(),
        (brief["R1.C3.Sub"] + brief["R2.C3.Sub"]).mean(),
    ]

    x = np.arange(len(dims))
    width = 0.35

    fig, ax = plt.subplots(figsize=(6.4, 4.8), dpi=150)
    bars1 = ax.bar(x - width / 2, ext_vals, width, color=BLUE, alpha=0.8, label=label_map.get(1, "Cluster 1"))
    bars2 = ax.bar(x + width / 2, brief_vals, width, color=RED, alpha=0.9, label=label_map.get(2, "Cluster 2"))

    ax.set_xticks(x)
    ax.set_xticklabels(dims)
    ax.set_ylabel("Mean Total Submissions (R1 + R2)")
    ax.set_xlabel("Review Dimension")
    ax.set_title("Fig. 11. Review Effort Distribution Across Rubric Dimensions")
    style_axes(ax)
    ax.legend(loc="upper right")

    for bars in [bars1, bars2]:
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + 2.5, f"{h:.0f}", ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(out_dir / "Fig11_Effort_Distribution_By_Dimension.png", dpi=300)
    fig.savefig(out_dir / "Fig11_Effort_Distribution_By_Dimension.pdf")
    plt.close(fig)


def fig12_temporal_engagement(df: pd.DataFrame, out_dir: Path, label_map: dict):
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2), dpi=150)

    ext = df[df["Cluster"] == 1]
    brief = df[df["Cluster"] == 2]

    # --- Panel (a): Mean Duration by cluster (grouped bar) ---
    ax = axes[0]
    dur_cols = ["R1.Dur", "R2.Dur"]
    ext_means = [ext[c].mean() for c in dur_cols]
    ext_errs = [sem(ext[c]) for c in dur_cols]
    brief_means = [brief[c].mean() for c in dur_cols]
    brief_errs = [sem(brief[c]) for c in dur_cols]

    x = np.arange(len(dur_cols))
    width = 0.35
    bars1 = ax.bar(x - width / 2, ext_means, width, yerr=ext_errs, capsize=4,
                   color=BLUE, alpha=0.8, label=label_map.get(1, "Cluster 1"))
    bars2 = ax.bar(x + width / 2, brief_means, width, yerr=brief_errs, capsize=4,
                   color=RED, alpha=0.9, label=label_map.get(2, "Cluster 2"))
    ax.set_xticks(x)
    ax.set_xticklabels(["Round 1", "Round 2"])
    ax.set_ylabel("Mean Duration (seconds)")
    ax.set_title("(a) Review Duration by Cluster", fontsize=9)
    style_axes(ax)
    ax.legend(fontsize=8)
    for bars in [bars1, bars2]:
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + 3, f"{h:.1f}",
                    ha="center", va="bottom", fontsize=8)

    # --- Panel (b): Start-time comparison ---
    ax = axes[1]
    time_cols = ["R1.Start", "R1.End", "R2.Start", "R2.End"]
    time_labels = ["R1 Start", "R1 End", "R2 Start", "R2 End"]
    ext_t = [ext[c].mean() for c in time_cols]
    ext_t_err = [sem(ext[c]) for c in time_cols]
    brief_t = [brief[c].mean() for c in time_cols]
    brief_t_err = [sem(brief[c]) for c in time_cols]

    x2 = np.arange(len(time_cols))
    ax.bar(x2 - width / 2, ext_t, width, yerr=ext_t_err, capsize=3,
           color=BLUE, alpha=0.8, label=label_map.get(1, "Cluster 1"))
    ax.bar(x2 + width / 2, brief_t, width, yerr=brief_t_err, capsize=3,
           color=RED, alpha=0.9, label=label_map.get(2, "Cluster 2"))
    ax.set_xticks(x2)
    ax.set_xticklabels(time_labels, fontsize=7.5, rotation=15)
    ax.set_ylabel("Mean Time (seconds)")
    ax.set_title("(b) Review Timing by Cluster", fontsize=9)
    style_axes(ax)
    ax.legend(fontsize=7)

    fig.suptitle("Fig. 12. Temporal Engagement Features by Cluster (R1 & R2)", y=1.02, fontsize=10)
    fig.tight_layout()
    fig.savefig(out_dir / "Fig12_Temporal_Engagement_Features.png", dpi=300, bbox_inches="tight")
    fig.savefig(out_dir / "Fig12_Temporal_Engagement_Features.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Export paper figures (Fig. 6 to Fig. 12).")
    parser.add_argument(
        "--input",
        default="New-Chart_input_clustering_results_clustered_data_k2.xlsx",
        help="Path to clustered dataset Excel file.",
    )
    parser.add_argument(
        "--out-dir",
        default="Cluster-Profile-Figures",
        help="Directory where exported figures will be written.",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = Path(__file__).resolve().parent / input_path

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = Path(__file__).resolve().parent / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(input_path)

    r1_mf_col = "R1.MF_Count" if "R1.MF_Count" in df.columns else "R1_MF_Count"
    r2_mf_col = "R2.MF_Count" if "R2.MF_Count" in df.columns else "R2_MF_Count"

    required_cols = {
        "Id",
        "Cluster",
        "R1.C1.Sub",
        "R1.C2.Sub",
        "R1.C3.Sub",
        "R2.C1.Sub",
        "R2.C2.Sub",
        "R2.C3.Sub",
        r1_mf_col,
        r2_mf_col,
        "Effort_Total",
        "Mean_HW",
        "HW1",
        "HW2",
        "HW3",
        "HW4",
        "HW5",
        "HW6",
    }
    missing = sorted(required_cols - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    label_map = detect_label_map(df)

    plt.style.use("seaborn-v0_8-whitegrid")
    fig6_trajectory(df, out_dir, label_map)
    fig7_radar(df, out_dir, label_map, r1_mf_col, r2_mf_col)
    fig8_cross_dimension(df, out_dir)
    fig9_individual_trajectories(df, out_dir)
    fig10_effort_feedback_performance(df, out_dir, r1_mf_col, r2_mf_col)
    fig11_effort_distribution(df, out_dir, label_map)
    fig12_temporal_engagement(df, out_dir, label_map)

    print(f"Export complete. Figures saved to: {out_dir}")


if __name__ == "__main__":
    main()
