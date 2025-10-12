import matplotlib.pyplot as plt
import os


def plot_hard_constraint_violation_over_generation(hard_trend, output_dir):
    """
    Plots the trend of hard constraint violations over generations.

    Args:
        hard_trend (List[int]): List of hard constraint violation counts per generation.
        output_dir (str): Directory to save the plot.
    """
    plt.figure(figsize=(8, 4))
    plt.plot(hard_trend, color="red", label="Hard Constraint Violations")
    # plt.yscale("log")
    plt.xlabel("Generation")
    plt.ylabel("Violations")
    plt.title("Hard Constraint Violations Over Generations")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "hard_constraint_trend.pdf"))
    plt.close()  # Close the figure to free memory
