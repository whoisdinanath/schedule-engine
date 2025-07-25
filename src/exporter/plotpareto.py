import os

import matplotlib.pyplot as plt


def plot_pareto_front(population, output_dir):
    hard_vals, soft_vals = zip(*[ind.fitness.values for ind in population])
    plt.figure(figsize=(6, 5))
    plt.scatter(hard_vals, soft_vals, color="blue", alpha=0.6)
    plt.xlabel("Hard Constraint Violations")
    plt.ylabel("Soft Constraint Penalty")
    plt.title("Final Pareto Front")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "pareto_front.pdf"))
    plt.close()
