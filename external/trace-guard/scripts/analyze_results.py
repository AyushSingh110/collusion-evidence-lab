"""Analyze evaluation results and generate plots.

Usage:
    python scripts/analyze_results.py --log-dir logs/ --output plots/
    python scripts/analyze_results.py --log-dir logs/ --output plots/ --dimension-breakdown
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from traceguard.analysis.pareto import (
    compute_pareto_points,
    load_results,
    plot_category_breakdown,
    plot_confusion_matrix,
    plot_dimension_breakdown,
    plot_pareto_frontier,
    plot_roc_curve,
)


def main():
    parser = argparse.ArgumentParser(description="Analyze TraceGuard evaluation results")
    parser.add_argument("--log-dir", type=str, default="logs", help="Eval log directory")
    parser.add_argument("--output", type=str, default="plots", help="Output directory for plots")
    parser.add_argument("--dimension-breakdown", action="store_true")
    parser.add_argument("--category-breakdown", action="store_true", help="Generate per-category detection rate heatmap")
    parser.add_argument("--confusion-matrix", action="store_true", help="Generate confusion matrix plot")
    parser.add_argument("--roc-curve", action="store_true", help="Generate AUC-ROC curve plot")
    parser.add_argument("--all-plots", action="store_true", help="Generate all available plots")
    parser.add_argument("--thresholds", type=float, nargs="+", default=[round(i * 0.05, 2) for i in range(21)])
    parser.add_argument(
        "--recent",
        type=int,
        default=None,
        metavar="MINUTES",
        help="Only analyze logs modified within the last N minutes (default: all logs)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading results from {args.log_dir}...")
    df = load_results(args.log_dir, recent_minutes=args.recent)
    recent_label = f" (last {args.recent} min)" if args.recent else ""
    print(f"  Loaded {len(df)} samples{recent_label} ({(df['mode'] == 'honest').sum()} honest, {(df['mode'] == 'attack').sum()} attack)")

    print("\nComputing Pareto points...")
    points = compute_pareto_points(df, thresholds=args.thresholds)

    print("Generating Pareto frontier plot...")
    plot_pareto_frontier(
        points,
        title="TraceGuard: Safety vs Usefulness",
        output_path=str(output_dir / "pareto_frontier.png"),
    )

    if args.dimension_breakdown:
        print("Generating dimension breakdown...")
        plot_dimension_breakdown(
            args.log_dir,
            output_path=str(output_dir / "dimension_breakdown.png"),
        )

    if args.category_breakdown:
        print("Generating category breakdown...")
        plot_category_breakdown(
            df,
            threshold=args.thresholds[0],
            output_path=str(output_dir / "category_breakdown.png"),
        )

    if args.confusion_matrix or args.all_plots:
        print("Generating confusion matrix...")
        plot_confusion_matrix(
            df,
            threshold=args.thresholds[0],
            output_path=str(output_dir / "confusion_matrix.png"),
        )

    if args.roc_curve or args.all_plots:
        print("Generating AUC-ROC curve...")
        plot_roc_curve(
            df,
            output_path=str(output_dir / "roc_curve.png"),
        )

    # Print summary table
    print("\n--- Results Summary ---")
    print(f"{'Threshold':>10} | {'Safety':>8} | {'Usefulness':>10} | {'Defer Rate':>10}")
    print("-" * 48)
    for p in points:
        print(f"{p.threshold:>10.1f} | {p.safety:>8.3f} | {p.usefulness:>10.3f} | {p.audit_budget:>10.1%}")

    # Raw stats
    print(f"\n--- Raw Stats ---")
    print(f"Suspicion scores: min={df['max_suspicion'].min():.3f}, max={df['max_suspicion'].max():.3f}, mean={df['max_suspicion'].mean():.3f}")
    honest = df[df["mode"] == "honest"]
    attack = df[df["mode"] == "attack"]
    if len(honest) > 0:
        print(f"Honest suspicion:  mean={honest['max_suspicion'].mean():.3f}")
    if len(attack) > 0:
        print(f"Attack suspicion:  mean={attack['max_suspicion'].mean():.3f}")
    print(f"Main task success: {df['main_task_success'].mean():.1%}")

    print(f"\nPlots saved to {output_dir}/")


if __name__ == "__main__":
    main()
