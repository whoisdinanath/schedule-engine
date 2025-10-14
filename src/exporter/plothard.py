import matplotlib.pyplot as plt
import os
import csv


def plot_hard_constraint_violation_over_generation(hard_trend, output_dir):
    """
    Plots the trend of hard constraint violations over generations.

    Args:
        hard_trend (List[int]): List of hard constraint violation counts per generation.
        output_dir (str): Directory to save the plot.
    """
    # Create CSVs subdirectory
    csv_dir = os.path.join(output_dir, "CSVs")
    os.makedirs(csv_dir, exist_ok=True)

    # Save data to CSV
    csv_path = os.path.join(csv_dir, "hard_constraint_trend.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Generation", "Hard_Constraint_Violations"])
        for gen, value in enumerate(hard_trend):
            writer.writerow([gen, value])

    plt.figure(figsize=(8, 4))
    plt.plot(
        hard_trend, color="#E74C3C", linewidth=2.5, label="Hard Constraint Violations"
    )
    # plt.yscale("log")
    plt.xlabel("Generation")
    plt.ylabel("Violations")
    plt.title("Hard Constraint Violations Over Generations")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "hard_constraint_trend.pdf"))
    plt.close()  # Close the figure to free memory
