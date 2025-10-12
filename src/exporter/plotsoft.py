import matplotlib.pyplot as plt
import os


def plot_soft_constraint_violation_over_generation(soft_trend, output_dir):
    """
    Plots the trend of soft constraint penalties over generations.

    Args:
        soft_trend (List[int]): List of soft constraint penalty counts per generation.
        output_dir (str): Directory to save the plot.
    """
    plt.figure(figsize=(8, 4))
    plt.plot(soft_trend, color="green", label="Soft Constraint Penalties")
    plt.xlabel("Generation")
    plt.ylabel("Penalty")
    plt.title("Soft Constraint Penalties Over Generations")
    # plt.yscale("log")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "soft_constraint_trend.pdf"))
