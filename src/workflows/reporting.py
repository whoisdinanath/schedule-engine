"""
Reporting Workflow Module

Handles plotting and export of GA results.
Extracted from main.py for modularity.
"""

from typing import List
from src.entities.decoded_session import CourseSession
from src.encoder.quantum_time_system import QuantumTimeSystem
from src.core.ga_scheduler import GAMetrics
from src.exporter.exporter import export_everything
from src.exporter.plotdiversity import plot_diversity_trend
from src.exporter.plothard import plot_hard_constraint_violation_over_generation
from src.exporter.plotsoft import plot_soft_constraint_violation_over_generation
from src.exporter.plotpareto import plot_pareto_front
from src.exporter.plot_detailed_constraints import (
    plot_individual_hard_constraints,
    plot_individual_soft_constraints,
    plot_constraint_summary,
)


def generate_reports(
    decoded_schedule: List[CourseSession],
    metrics: GAMetrics,
    population: List,
    qts: QuantumTimeSystem,
    output_dir: str,
):
    """
    Generate all output artifacts: plots, JSON, PDFs.

    Creates:
        - schedule.json: Schedule in JSON format
        - schedule.pdf: Visual calendar with color-coded sessions
        - Evolution plots: hard/soft constraint trends, diversity
        - Pareto front visualization
        - Detailed constraint breakdown plots

    Args:
        decoded_schedule: Best schedule solution (list of CourseSessions)
        metrics: GA evolution metrics
        population: Final population (for Pareto front)
        qts: Quantum time system (for time conversion)
        output_dir: Output directory path
    """

    # Export schedule (JSON + PDF)
    print("  [+] Exporting schedule...")
    export_everything(decoded_schedule, output_dir, qts)
    print("      [OK] schedule.json")
    print("      [OK] schedule.pdf")

    # Plot evolution trends
    print("  [+] Generating evolution plots...")
    plot_hard_constraint_violation_over_generation(metrics.hard_violations, output_dir)
    print("      [OK] hard_constraint_trend.pdf")

    plot_soft_constraint_violation_over_generation(metrics.soft_penalties, output_dir)
    print("      [OK] soft_constraint_trend.pdf")

    plot_diversity_trend(metrics.diversity, output_dir)
    print("      [OK] diversity_trend.pdf")

    # Plot Pareto front
    print("  [+] Generating Pareto front plot...")
    plot_pareto_front(population, output_dir)
    print("      [OK] pareto_front.pdf")

    # Plot detailed constraints
    print("  [+] Generating detailed constraint plots...")
    plot_individual_hard_constraints(metrics.detailed_hard, output_dir)
    print("      [OK] hard/individual_constraints.pdf")

    plot_individual_soft_constraints(metrics.detailed_soft, output_dir)
    print("      [OK] soft/individual_constraints.pdf")

    plot_constraint_summary(metrics.detailed_hard, metrics.detailed_soft, output_dir)
    print("      [OK] constraint_summary.pdf")

    print("  [+] All reports generated successfully!")
