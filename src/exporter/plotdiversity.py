import os
import csv

import matplotlib.pyplot as plt


def plot_diversity_trend(diversity_trend, output_dir):
    # Create CSVs subdirectory
    csv_dir = os.path.join(output_dir, "CSVs")
    os.makedirs(csv_dir, exist_ok=True)

    # Save data to CSV
    csv_path = os.path.join(csv_dir, "diversity_trend.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Generation", "Average_Chromosome_Distance"])
        for gen, value in enumerate(diversity_trend):
            writer.writerow([gen, value])

    plt.figure(figsize=(8, 4))
    plt.plot(diversity_trend, color="#F39C12", linewidth=2.5, label="Diversity")
    plt.xlabel("Generation")
    plt.ylabel("Avg. Chromosome Distance")
    plt.title("Diversity Over Generations")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "diversity.pdf"))
    plt.close()
