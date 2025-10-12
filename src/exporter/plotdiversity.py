import os

import matplotlib.pyplot as plt


def plot_diversity_trend(diversity_trend, output_dir):
    plt.figure(figsize=(8, 4))
    plt.plot(diversity_trend, color="orange", label="Diversity")
    plt.xlabel("Generation")
    plt.ylabel("Avg. Chromosome Distance")
    plt.title("Diversity Over Generations")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "diversity.pdf"))
    plt.close()
