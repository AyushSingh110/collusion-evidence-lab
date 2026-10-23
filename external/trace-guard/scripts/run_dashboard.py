"""Automated comparison dashboard for multi-monitor evaluation.

Single-command entry point that generates a comprehensive comparison
dashboard from evaluation logs: Pareto frontier, category heatmap,
dimension breakdown, temporal analysis, and summary JSON.

Usage:
    python scripts/run_dashboard.py --log-dir logs/ --output-dir dashboard_output/
    python scripts/run_dashboard.py --log-dir logs/ --output-dir out/ --thresholds 0.3 0.5 0.7 0.9

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from traceguard.analysis.pareto import (
    compute_pareto_points,
    compute_temporal_analysis,
    load_results,
    plot_category_breakdown,
    plot_dimension_breakdown,
    plot_pareto_frontier,
    plot_temporal_analysis,
)

DEFAULT_THRESHOLDS = [round(i * 0.05, 2) for i in range(21)]  # 0.0 to 1.0, step 0.05


def run_dashboard(
    log_dir: str,
    output_dir: str,
    thresholds: list[float] | None = None,
) -> dict:
    """Single-command comprehensive comparison dashboard.

    Generates:
    1. Pareto frontier plot (safety vs usefulness)
    2. Category breakdown heatmap (detection rate per monitor x category)
    3. Dimension breakdown (per-dimension score distributions, honest vs attack)
    4. Temporal analysis (composite score evolution across trajectory steps)
    5. Summary JSON report

    All outputs saved to output_dir.

    Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
    """
    if thresholds is None:
        thresholds = list(DEFAULT_THRESHOLDS)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Load results
    print(f"Loading evaluation logs from {log_dir}...")
    df = load_results(log_dir)
    monitor_names = sorted(df["monitor_name"].unique().tolist())
    print(f"  Loaded {len(df)} samples across monitors: {monitor_names}")

    # 1. Pareto frontier
    pareto_path = str(out / "pareto_frontier.png")
    print("Generating Pareto frontier plot...")
    points = compute_pareto_points(df, monitor_names, thresholds)
    plot_pareto_frontier(points, output_path=pareto_path)

    # 2. Category breakdown heatmap
    heatmap_path = str(out / "category_heatmap.png")
    print("Generating category breakdown heatmap...")
    mid_threshold = thresholds[len(thresholds) // 2] if thresholds else 0.5
    plot_category_breakdown(df, threshold=mid_threshold, output_path=heatmap_path)

    # 3. Dimension breakdown
    dimension_path = str(out / "dimension_breakdown.png")
    print("Generating dimension breakdown plot...")
    plot_dimension_breakdown(log_dir, output_path=dimension_path)

    # 4. Temporal analysis
    temporal_path = str(out / "temporal_analysis.png")
    print("Generating temporal analysis plot...")
    temporal_data = compute_temporal_analysis(log_dir)
    plot_temporal_analysis(temporal_data, output_path=temporal_path)

    # 5. Compute summary stats
    honest_df = df[df["mode"] == "honest"]
    attack_df = df[df["mode"] == "attack"]

    # Best safety monitor: highest mean suspicion on attack samples
    best_safety = ""
    best_safety_score = -1.0
    # Best usefulness monitor: lowest mean suspicion on honest samples (least false positives)
    best_usefulness = ""
    best_usefulness_score = float("inf")

    for name in monitor_names:
        attack_subset = attack_df[attack_df["monitor_name"] == name]
        honest_subset = honest_df[honest_df["monitor_name"] == name]

        if len(attack_subset) > 0:
            mean_attack = float(attack_subset["max_suspicion"].mean())
            if mean_attack > best_safety_score:
                best_safety_score = mean_attack
                best_safety = name

        if len(honest_subset) > 0:
            mean_honest = float(honest_subset["max_suspicion"].mean())
            if mean_honest < best_usefulness_score:
                best_usefulness_score = mean_honest
                best_usefulness = name

    summary = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "log_dir": log_dir,
        "monitors": monitor_names,
        "plots": {
            "pareto_frontier": "pareto_frontier.png",
            "category_heatmap": "category_heatmap.png",
            "dimension_breakdown": "dimension_breakdown.png",
            "temporal_analysis": "temporal_analysis.png",
        },
        "summary": {
            "total_samples": len(df),
            "honest_samples": len(honest_df),
            "attack_samples": len(attack_df),
            "best_safety_monitor": best_safety,
            "best_usefulness_monitor": best_usefulness,
        },
    }

    # Write summary JSON
    summary_path = out / "dashboard_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary JSON to {summary_path}")

    print(f"\nDashboard complete. All outputs in {output_dir}/")
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive multi-monitor comparison dashboard"
    )
    parser.add_argument(
        "--log-dir", type=str, required=True, help="Directory with .eval log files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="dashboard_output",
        help="Output directory for plots and summary JSON",
    )
    parser.add_argument(
        "--thresholds",
        type=float,
        nargs="+",
        default=None,
        help="Suspicion thresholds (default: 0.0 to 1.0, step 0.05)",
    )
    args = parser.parse_args()

    run_dashboard(args.log_dir, args.output_dir, args.thresholds)


if __name__ == "__main__":
    main()
