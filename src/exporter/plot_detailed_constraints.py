import matplotlib.pyplot as plt
import os
from typing import Dict, List


def plot_individual_hard_constraints(
    hard_trends: Dict[str, List[int]], output_dir: str
):
    """
    Plots each hard constraint trend separately and saves them in hard/ subdirectory.

    Args:
        hard_trends: Dictionary mapping constraint names to their trends over generations
        output_dir: Base output directory
    """
    hard_dir = os.path.join(output_dir, "hard")
    os.makedirs(hard_dir, exist_ok=True)

    # Individual plots for each hard constraint
    for constraint_name, trend in hard_trends.items():
        plt.figure(figsize=(12, 6))

        # Main trend line
        plt.plot(
            trend,
            color="red",
            linewidth=2,
            marker="o",
            markersize=4,
            label=constraint_name.replace("_", " ").title(),
        )

        # Add statistics
        final_value = trend[-1]
        max_value = max(trend)
        min_value = min(trend)
        avg_value = sum(trend) / len(trend)

        # Add horizontal lines for statistics
        plt.axhline(
            y=final_value,
            color="red",
            linestyle="--",
            alpha=0.5,
            label=f"Final: {final_value}",
        )
        plt.axhline(
            y=max_value,
            color="orange",
            linestyle=":",
            alpha=0.5,
            label=f"Max: {max_value}",
        )
        plt.axhline(
            y=avg_value,
            color="gray",
            linestyle="-.",
            alpha=0.5,
            label=f"Avg: {avg_value:.1f}",
        )

        plt.xlabel("Generation")
        plt.ylabel("Violations")
        plt.title(f"Hard Constraint Trend: {constraint_name.replace('_', ' ').title()}")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save individual plot
        filename = f"{constraint_name}_trend.pdf"
        plt.savefig(os.path.join(hard_dir, filename), bbox_inches="tight")
        plt.close()

    # Combined plot with all hard constraints
    plt.figure(figsize=(14, 8))
    colors = ["red", "darkred", "crimson", "firebrick", "indianred", "lightcoral"]

    for i, (constraint_name, trend) in enumerate(hard_trends.items()):
        color = colors[i % len(colors)]
        plt.plot(
            trend,
            label=constraint_name.replace("_", " ").title(),
            color=color,
            linewidth=2,
            alpha=0.8,
            marker="o",
            markersize=3,
        )

    plt.xlabel("Generation")
    plt.ylabel("Violations")
    plt.title("All Hard Constraints Trends")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(hard_dir, "all_hard_constraints.pdf"), bbox_inches="tight")
    plt.close()

    # Create a summary statistics table plot
    plt.figure(figsize=(12, 8))
    constraint_names = list(hard_trends.keys())
    final_values = [trend[-1] for trend in hard_trends.values()]
    max_values = [max(trend) for trend in hard_trends.values()]
    avg_values = [sum(trend) / len(trend) for trend in hard_trends.values()]

    x = range(len(constraint_names))
    width = 0.25

    plt.bar(
        [i - width for i in x],
        final_values,
        width,
        label="Final",
        color="red",
        alpha=0.7,
    )
    plt.bar(x, max_values, width, label="Maximum", color="orange", alpha=0.7)
    plt.bar(
        [i + width for i in x],
        avg_values,
        width,
        label="Average",
        color="gray",
        alpha=0.7,
    )

    plt.xlabel("Constraints")
    plt.ylabel("Violations")
    plt.title("Hard Constraints Statistics Summary")
    plt.xticks(
        x,
        [name.replace("_", "\n") for name in constraint_names],
        rotation=45,
        ha="right",
    )
    plt.legend()
    plt.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(
        os.path.join(hard_dir, "hard_constraints_summary.pdf"), bbox_inches="tight"
    )
    plt.close()


def plot_individual_soft_constraints(
    soft_trends: Dict[str, List[int]], output_dir: str
):
    """
    Plots each soft constraint trend separately and saves them in soft/ subdirectory.

    Args:
        soft_trends: Dictionary mapping constraint names to their trends over generations
        output_dir: Base output directory
    """
    soft_dir = os.path.join(output_dir, "soft")
    os.makedirs(soft_dir, exist_ok=True)

    # Individual plots for each soft constraint
    for constraint_name, trend in soft_trends.items():
        plt.figure(figsize=(12, 6))

        # Main trend line
        plt.plot(
            trend,
            color="green",
            linewidth=2,
            marker="o",
            markersize=4,
            label=constraint_name.replace("_", " ").title(),
        )

        # Add statistics
        final_value = trend[-1]
        max_value = max(trend)
        min_value = min(trend)
        avg_value = sum(trend) / len(trend)

        # Add horizontal lines for statistics
        plt.axhline(
            y=final_value,
            color="green",
            linestyle="--",
            alpha=0.5,
            label=f"Final: {final_value}",
        )
        plt.axhline(
            y=max_value,
            color="orange",
            linestyle=":",
            alpha=0.5,
            label=f"Max: {max_value}",
        )
        plt.axhline(
            y=avg_value,
            color="gray",
            linestyle="-.",
            alpha=0.5,
            label=f"Avg: {avg_value:.1f}",
        )

        plt.xlabel("Generation")
        plt.ylabel("Penalty")
        plt.title(f"Soft Constraint Trend: {constraint_name.replace('_', ' ').title()}")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save individual plot
        filename = f"{constraint_name}_trend.pdf"
        plt.savefig(os.path.join(soft_dir, filename), bbox_inches="tight")
        plt.close()

    # Combined plot with all soft constraints
    plt.figure(figsize=(14, 8))
    colors = [
        "green",
        "darkgreen",
        "forestgreen",
        "limegreen",
        "mediumseagreen",
        "lightgreen",
    ]

    for i, (constraint_name, trend) in enumerate(soft_trends.items()):
        color = colors[i % len(colors)]
        plt.plot(
            trend,
            label=constraint_name.replace("_", " ").title(),
            color=color,
            linewidth=2,
            alpha=0.8,
            marker="o",
            markersize=3,
        )

    plt.xlabel("Generation")
    plt.ylabel("Penalty")
    plt.title("All Soft Constraints Trends")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(soft_dir, "all_soft_constraints.pdf"), bbox_inches="tight")
    plt.close()

    # Create a summary statistics table plot
    plt.figure(figsize=(12, 8))
    constraint_names = list(soft_trends.keys())
    final_values = [trend[-1] for trend in soft_trends.values()]
    max_values = [max(trend) for trend in soft_trends.values()]
    avg_values = [sum(trend) / len(trend) for trend in soft_trends.values()]

    x = range(len(constraint_names))
    width = 0.25

    plt.bar(
        [i - width for i in x],
        final_values,
        width,
        label="Final",
        color="green",
        alpha=0.7,
    )
    plt.bar(x, max_values, width, label="Maximum", color="orange", alpha=0.7)
    plt.bar(
        [i + width for i in x],
        avg_values,
        width,
        label="Average",
        color="gray",
        alpha=0.7,
    )

    plt.xlabel("Constraints")
    plt.ylabel("Penalty")
    plt.title("Soft Constraints Statistics Summary")
    plt.xticks(
        x,
        [name.replace("_", "\n") for name in constraint_names],
        rotation=45,
        ha="right",
    )
    plt.legend()
    plt.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(
        os.path.join(soft_dir, "soft_constraints_summary.pdf"), bbox_inches="tight"
    )
    plt.close()


def plot_constraint_summary(
    hard_trends: Dict[str, List[int]],
    soft_trends: Dict[str, List[int]],
    output_dir: str,
):
    """
    Creates a summary dashboard showing total trends and final constraint values.
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # Total hard constraints trend
    total_hard = [sum(values) for values in zip(*hard_trends.values())]
    ax1.plot(total_hard, color="red", linewidth=3)
    ax1.set_title("Total Hard Constraint Violations")
    ax1.set_xlabel("Generation")
    ax1.set_ylabel("Total Violations")
    ax1.grid(True, alpha=0.3)

    # Total soft constraints trend
    total_soft = [sum(values) for values in zip(*soft_trends.values())]
    ax2.plot(total_soft, color="green", linewidth=3)
    ax2.set_title("Total Soft Constraint Penalties")
    ax2.set_xlabel("Generation")
    ax2.set_ylabel("Total Penalty")
    ax2.grid(True, alpha=0.3)

    # Final hard constraint values (bar chart)
    final_hard = {name: trend[-1] for name, trend in hard_trends.items()}
    ax3.bar(range(len(final_hard)), list(final_hard.values()), color="red", alpha=0.7)
    ax3.set_title("Final Hard Constraint Violations")
    ax3.set_ylabel("Violations")
    ax3.set_xticks(range(len(final_hard)))
    ax3.set_xticklabels(
        [name.replace("_", "\n") for name in final_hard.keys()], rotation=45, ha="right"
    )

    # Final soft constraint values (bar chart)
    final_soft = {name: trend[-1] for name, trend in soft_trends.items()}
    ax4.bar(range(len(final_soft)), list(final_soft.values()), color="green", alpha=0.7)
    ax4.set_title("Final Soft Constraint Penalties")
    ax4.set_ylabel("Penalty")
    ax4.set_xticks(range(len(final_soft)))
    ax4.set_xticklabels(
        [name.replace("_", "\n") for name in final_soft.keys()], rotation=45, ha="right"
    )

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "constraint_summary.pdf"), bbox_inches="tight")
    plt.close()
