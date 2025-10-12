import os
import matplotlib.pyplot as plt
from deap import tools
import numpy as np


def plot_pareto_front(population, output_dir):
    """
    Enhanced Pareto front visualization showing all points with better visibility.
    """
    hard_vals, soft_vals = zip(*[ind.fitness.values for ind in population])

    # Create comprehensive plots showing all data
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: All population points with jitter to show overlapping points
    unique_points = {}
    jittered_hard = []
    jittered_soft = []

    for h, s in zip(hard_vals, soft_vals):
        key = (h, s)
        if key in unique_points:
            unique_points[key] += 1
            # Add small jitter to overlapping points
            jitter_strength = 0.1 * unique_points[key]
            jittered_hard.append(h + np.random.normal(0, jitter_strength))
            jittered_soft.append(s + np.random.normal(0, jitter_strength))
        else:
            unique_points[key] = 1
            jittered_hard.append(h)
            jittered_soft.append(s)

    ax1.scatter(jittered_hard, jittered_soft, color="lightblue", alpha=0.6, s=25)
    ax1.set_xlabel("Hard Constraint Violations")
    ax1.set_ylabel("Soft Constraint Penalty")
    ax1.set_title(f"All Population Points with Jitter\n({len(population)} individuals)")
    ax1.grid(True, alpha=0.3)

    # Plot 2: Original view with population and Pareto front
    ax2.scatter(
        hard_vals, soft_vals, color="lightblue", alpha=0.4, s=20, label="Population"
    )

    # Highlight the actual Pareto front
    pareto_front = tools.sortNondominated(
        population, len(population), first_front_only=True
    )[0]
    pareto_hard = [ind.fitness.values[0] for ind in pareto_front]
    pareto_soft = [ind.fitness.values[1] for ind in pareto_front]

    ax2.scatter(
        pareto_hard,
        pareto_soft,
        color="red",
        alpha=0.8,
        s=50,
        label=f"Pareto Front ({len(pareto_front)} solutions)",
        edgecolors="black",
    )

    # Show count for overlapping points
    for (h, s), count in unique_points.items():
        if count > 1:
            ax2.annotate(
                f"{count}",
                (h, s),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
                alpha=0.7,
            )

    ax2.set_xlabel("Hard Constraint Violations")
    ax2.set_ylabel("Soft Constraint Penalty")
    ax2.set_title(
        f"Population with Pareto Front\n({len(unique_points)} unique solutions)"
    )
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Heatmap of point density
    try:
        from scipy.stats import gaussian_kde

        if len(np.unique(hard_vals)) > 1 and len(np.unique(soft_vals)) > 1:
            # Create density heatmap
            hard_range = np.linspace(min(hard_vals), max(hard_vals), 50)
            soft_range = np.linspace(min(soft_vals), max(soft_vals), 50)
            H, S = np.meshgrid(hard_range, soft_range)
            positions = np.vstack([H.ravel(), S.ravel()])
            values = np.vstack([hard_vals, soft_vals])
            kernel = gaussian_kde(values)
            density = np.reshape(kernel(positions).T, H.shape)

            im = ax3.contourf(H, S, density, levels=20, cmap="Blues", alpha=0.7)
            ax3.scatter(hard_vals, soft_vals, color="darkblue", alpha=0.5, s=10)
            ax3.scatter(
                pareto_hard,
                pareto_soft,
                color="red",
                s=30,
                alpha=0.8,
                edgecolors="black",
            )
            plt.colorbar(im, ax=ax3, label="Density")
        else:
            # Fallback if density estimation fails
            ax3.scatter(hard_vals, soft_vals, color="lightblue", alpha=0.6, s=25)
            ax3.scatter(
                pareto_hard,
                pareto_soft,
                color="red",
                s=50,
                alpha=0.8,
                edgecolors="black",
            )
    except ImportError:
        # Fallback without scipy
        ax3.scatter(hard_vals, soft_vals, color="lightblue", alpha=0.6, s=25)
        ax3.scatter(
            pareto_hard, pareto_soft, color="red", s=50, alpha=0.8, edgecolors="black"
        )

    ax3.set_xlabel("Hard Constraint Violations")
    ax3.set_ylabel("Soft Constraint Penalty")
    ax3.set_title("Population Density with Pareto Front")
    ax3.grid(True, alpha=0.3)

    # Plot 4: Size-coded points showing frequency
    sizes = [unique_points.get((h, s), 1) * 20 for h, s in zip(hard_vals, soft_vals)]
    scatter = ax4.scatter(
        hard_vals,
        soft_vals,
        c=sizes,
        s=sizes,
        alpha=0.6,
        cmap="viridis",
        edgecolors="black",
        linewidth=0.5,
    )
    ax4.scatter(
        pareto_hard,
        pareto_soft,
        color="red",
        s=100,
        alpha=0.9,
        edgecolors="white",
        linewidth=2,
        label="Pareto Front",
    )

    plt.colorbar(scatter, ax=ax4, label="Point Frequency")
    ax4.set_xlabel("Hard Constraint Violations")
    ax4.set_ylabel("Soft Constraint Penalty")
    ax4.set_title("Frequency-Coded Population")
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(
        os.path.join(output_dir, "pareto_front_comprehensive.pdf"), bbox_inches="tight"
    )
    plt.close()

    # Create the original single plot for backward compatibility
    plt.figure(figsize=(10, 8))
    plt.scatter(
        hard_vals, soft_vals, color="lightblue", alpha=0.4, s=20, label="Population"
    )
    plt.scatter(
        pareto_hard,
        pareto_soft,
        color="red",
        alpha=0.8,
        s=50,
        label=f"Pareto Front ({len(pareto_front)} solutions)",
        edgecolors="black",
    )

    # Show count for overlapping points
    for (h, s), count in unique_points.items():
        if count > 1:
            plt.annotate(
                f"{count}",
                (h, s),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
                alpha=0.7,
            )

    plt.xlabel("Hard Constraint Violations")
    plt.ylabel("Soft Constraint Penalty")
    plt.title(
        f"Final Population Fitness Distribution\n({len(population)} individuals, "
        f"{len(unique_points)} unique solutions)"
    )
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "pareto_front.pdf"))
    plt.close()

    # Create a separate plot focusing only on the Pareto front
    if len(pareto_front) > 1:
        plt.figure(figsize=(8, 6))
        plt.scatter(
            pareto_hard, pareto_soft, color="red", s=100, alpha=0.8, edgecolors="black"
        )
        plt.plot(pareto_hard, pareto_soft, "r--", alpha=0.5, linewidth=1)

        # Annotate each point with its index
        for i, (h, s) in enumerate(zip(pareto_hard, pareto_soft)):
            plt.annotate(
                f"{i+1}",
                (h, s),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=10,
                fontweight="bold",
            )

        plt.xlabel("Hard Constraint Violations")
        plt.ylabel("Soft Constraint Penalty")
        plt.title(f"Pareto Front Detail ({len(pareto_front)} non-dominated solutions)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "pareto_front_detail.pdf"))
        plt.close()
