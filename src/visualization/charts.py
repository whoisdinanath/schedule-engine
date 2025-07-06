"""
Visualization charts for monitoring GA evolution and analyzing results.
Provides tools for plotting fitness evolution, constraint violations, and schedule analysis.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from ..ga.chromosome import Chromosome
from ..entities import Course, Instructor, Room, Group
from ..utils.logger import get_logger
from ..utils.config import TIME_SLOTS


class EvolutionVisualizer:
    """
    Creates visualizations for GA evolution monitoring and result analysis.
    """
    
    def __init__(self):
        """Initialize the visualizer."""
        self.logger = get_logger(self.__class__.__name__)
        
        # Set up matplotlib style
        plt.style.use('default')
        sns.set_palette("husl")
        
    def plot_fitness_evolution(self, 
                              fitness_history: List[Dict[str, Any]], 
                              save_path: Optional[str] = None,
                              show_plot: bool = True) -> None:
        """
        Plot fitness evolution over generations.
        
        Args:
            fitness_history: List of fitness statistics per generation
            save_path: Path to save the plot (optional)
            show_plot: Whether to display the plot
        """
        if not fitness_history:
            self.logger.warning("No fitness history data to plot")
            return
        
        # Extract data
        generations = [entry['generation'] for entry in fitness_history]
        best_fitness = [entry['best'] for entry in fitness_history]
        avg_fitness = [entry['average'] for entry in fitness_history]
        worst_fitness = [entry['worst'] for entry in fitness_history]
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot lines
        ax.plot(generations, best_fitness, 'g-', linewidth=2, label='Best Fitness', marker='o', markersize=3)
        ax.plot(generations, avg_fitness, 'b-', linewidth=1.5, label='Average Fitness', alpha=0.7)
        ax.plot(generations, worst_fitness, 'r-', linewidth=1, label='Worst Fitness', alpha=0.5)
        
        # Fill area between best and worst
        ax.fill_between(generations, best_fitness, worst_fitness, alpha=0.2, color='gray')
        
        # Formatting
        ax.set_xlabel('Generation', fontsize=12)
        ax.set_ylabel('Fitness Score', fontsize=12)
        ax.set_title('Fitness Evolution Over Generations', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Add statistics text
        final_best = best_fitness[-1] if best_fitness else 0
        improvement = final_best - best_fitness[0] if len(best_fitness) > 1 else 0
        
        stats_text = f'Final Best: {final_best:.4f}\\nImprovement: {improvement:+.4f}'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Fitness evolution plot saved to: {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_constraint_violations(self, 
                                  violation_history: List[Dict[str, Any]], 
                                  save_path: Optional[str] = None,
                                  show_plot: bool = True) -> None:
        """
        Plot constraint violations over generations.
        
        Args:
            violation_history: List of violation statistics per generation
            save_path: Path to save the plot (optional)
            show_plot: Whether to display the plot
        """
        if not violation_history:
            self.logger.warning("No violation history data to plot")
            return
        
        # Extract data
        generations = list(range(len(violation_history)))
        hard_violations = [entry.get('total_hard', 0) for entry in violation_history]
        soft_violations = [entry.get('total_soft', 0) for entry in violation_history]
        
        # Create subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Hard constraints plot
        ax1.plot(generations, hard_violations, 'r-', linewidth=2, marker='o', markersize=3)
        ax1.fill_between(generations, hard_violations, alpha=0.3, color='red')
        ax1.set_xlabel('Generation', fontsize=12)
        ax1.set_ylabel('Hard Constraint Violations', fontsize=12)
        ax1.set_title('Hard Constraint Violations Over Generations', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Add horizontal line at zero
        ax1.axhline(y=0, color='green', linestyle='--', alpha=0.7, label='Feasible (0 violations)')
        ax1.legend()
        
        # Soft constraints plot
        ax2.plot(generations, soft_violations, 'orange', linewidth=2, marker='s', markersize=3)
        ax2.fill_between(generations, soft_violations, alpha=0.3, color='orange')
        ax2.set_xlabel('Generation', fontsize=12)
        ax2.set_ylabel('Soft Constraint Violations', fontsize=12)
        ax2.set_title('Soft Constraint Violations Over Generations', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Constraint violations plot saved to: {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_diversity_evolution(self, 
                                diversity_history: List[float], 
                                save_path: Optional[str] = None,
                                show_plot: bool = True) -> None:
        """
        Plot population diversity over generations.
        
        Args:
            diversity_history: List of diversity scores per generation
            save_path: Path to save the plot (optional)
            show_plot: Whether to display the plot
        """
        if not diversity_history:
            self.logger.warning("No diversity history data to plot")
            return
        
        generations = list(range(len(diversity_history)))
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(generations, diversity_history, 'purple', linewidth=2, marker='^', markersize=3)
        ax.fill_between(generations, diversity_history, alpha=0.3, color='purple')
        
        ax.set_xlabel('Generation', fontsize=12)
        ax.set_ylabel('Population Diversity', fontsize=12)
        ax.set_title('Population Diversity Over Generations', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Add statistics
        avg_diversity = np.mean(diversity_history)
        ax.axhline(y=avg_diversity, color='red', linestyle='--', alpha=0.7, 
                  label=f'Average: {avg_diversity:.3f}')
        ax.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Diversity evolution plot saved to: {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_schedule_heatmap(self, 
                             chromosome: Chromosome,
                             courses: Dict[str, Course],
                             instructors: Dict[str, Instructor],
                             rooms: Dict[str, Room],
                             groups: Dict[str, Group],
                             view_type: str = 'room',
                             save_path: Optional[str] = None,
                             show_plot: bool = True) -> None:
        """
        Create a heatmap visualization of the schedule.
        
        Args:
            chromosome: Chromosome representing the schedule
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
            view_type: Type of heatmap ('room', 'instructor', 'course')
            save_path: Path to save the plot (optional)
            show_plot: Whether to display the plot
        """
        # Create schedule matrix
        days = TIME_SLOTS['days']
        time_slots = TIME_SLOTS['slots']
        
        if view_type == 'room':
            entities = list(rooms.keys())
            title = 'Room Utilization Schedule'
        elif view_type == 'instructor':
            entities = list(instructors.keys())
            title = 'Instructor Schedule'
        else:
            entities = list(courses.keys())
            title = 'Course Schedule'
        
        # Initialize matrix
        schedule_matrix = np.zeros((len(entities), len(days) * len(time_slots)))
        entity_labels = entities
        time_labels = [f"{day[:3]}\\n{slot}" for day in days for slot in time_slots]
        
        # Fill matrix
        for gene in chromosome.genes:
            try:
                if view_type == 'room' and gene.room_id in entities:
                    entity_idx = entities.index(gene.room_id)
                elif view_type == 'instructor' and gene.instructor_id in entities:
                    entity_idx = entities.index(gene.instructor_id)
                elif view_type == 'course' and gene.course_id in entities:
                    entity_idx = entities.index(gene.course_id)
                else:
                    continue
                
                day_idx = days.index(gene.day.lower())
                slot_idx = time_slots.index(gene.time_slot)
                time_idx = day_idx * len(time_slots) + slot_idx
                
                schedule_matrix[entity_idx, time_idx] = 1
                
            except (ValueError, IndexError):
                continue
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(16, max(8, len(entities) * 0.4)))
        
        sns.heatmap(schedule_matrix, 
                   xticklabels=time_labels,
                   yticklabels=entity_labels,
                   cmap='YlOrRd',
                   cbar_kws={'label': 'Scheduled (1) / Free (0)'},
                   ax=ax,
                   linewidths=0.5)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Day / Time Slot', fontsize=12)
        ax.set_ylabel(view_type.title(), fontsize=12)
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Schedule heatmap saved to: {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_workload_distribution(self, 
                                  chromosome: Chromosome,
                                  instructors: Dict[str, Instructor],
                                  courses: Dict[str, Course],
                                  save_path: Optional[str] = None,
                                  show_plot: bool = True) -> None:
        """
        Plot instructor workload distribution.
        
        Args:
            chromosome: Chromosome representing the schedule
            instructors: Dictionary of instructor entities
            courses: Dictionary of course entities
            save_path: Path to save the plot (optional)
            show_plot: Whether to display the plot
        """
        # Calculate workloads
        workloads = {}
        for instructor_id in instructors.keys():
            workloads[instructor_id] = 0
        
        for gene in chromosome.genes:
            if gene.instructor_id in instructors and gene.course_id in courses:
                course = courses[gene.course_id]
                workloads[gene.instructor_id] += course.duration / 60  # Convert to hours
        
        # Create bar plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        instructor_names = [instructors[id_].name for id_ in workloads.keys()]
        hours = list(workloads.values())
        
        bars = ax.bar(instructor_names, hours, color=plt.cm.viridis(np.linspace(0, 1, len(hours))))
        
        # Add value labels on bars
        for bar, hour in zip(bars, hours):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{hour:.1f}h', ha='center', va='bottom')
        
        ax.set_xlabel('Instructor', fontsize=12)
        ax.set_ylabel('Weekly Teaching Hours', fontsize=12)
        ax.set_title('Instructor Workload Distribution', fontsize=14, fontweight='bold')
        
        # Add average line
        avg_workload = np.mean(hours) if hours else 0
        ax.axhline(y=avg_workload, color='red', linestyle='--', alpha=0.7, 
                  label=f'Average: {avg_workload:.1f}h')
        ax.legend()
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Workload distribution plot saved to: {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def create_comprehensive_report(self, 
                                   evolution_stats: Dict[str, Any],
                                   chromosome: Chromosome,
                                   courses: Dict[str, Course],
                                   instructors: Dict[str, Instructor],
                                   rooms: Dict[str, Room],
                                   groups: Dict[str, Group],
                                   output_dir: str) -> None:
        """
        Create a comprehensive visual report with all charts.
        
        Args:
            evolution_stats: Evolution statistics from GA engine
            chromosome: Best chromosome found
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
            output_dir: Directory to save all plots
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        self.logger.info(f"Creating comprehensive visual report in: {output_path}")
        
        # Plot fitness evolution
        fitness_history = evolution_stats.get('fitness', {}).get('fitness_history', [])
        if fitness_history:
            self.plot_fitness_evolution(
                fitness_history, 
                save_path=str(output_path / 'fitness_evolution.png'),
                show_plot=False
            )
        
        # Plot constraint violations
        violation_history = evolution_stats.get('violations', {}).get('violation_history', [])
        if violation_history:
            self.plot_constraint_violations(
                violation_history,
                save_path=str(output_path / 'constraint_violations.png'),
                show_plot=False
            )
        
        # Plot diversity evolution
        diversity_history = evolution_stats.get('fitness', {}).get('diversity_history', [])
        if diversity_history:
            self.plot_diversity_evolution(
                diversity_history,
                save_path=str(output_path / 'diversity_evolution.png'),
                show_plot=False
            )
        
        # Create schedule heatmaps
        for view_type in ['room', 'instructor', 'course']:
            self.plot_schedule_heatmap(
                chromosome, courses, instructors, rooms, groups,
                view_type=view_type,
                save_path=str(output_path / f'schedule_heatmap_{view_type}.png'),
                show_plot=False
            )
        
        # Plot workload distribution
        self.plot_workload_distribution(
            chromosome, instructors, courses,
            save_path=str(output_path / 'workload_distribution.png'),
            show_plot=False
        )
        
        self.logger.info("Comprehensive visual report completed!")
    
    def show_quick_summary(self, evolution_stats: Dict[str, Any]) -> None:
        """
        Display a quick text summary of the evolution results.
        
        Args:
            evolution_stats: Evolution statistics from GA engine
        """
        print("\\n" + "="*60)
        print("EVOLUTION SUMMARY")
        print("="*60)
        
        # Evolution metrics
        evolution = evolution_stats.get('evolution', {})
        print(f"Generations: {evolution.get('generations', 'N/A')}")
        print(f"Duration: {evolution.get('duration_seconds', 0):.2f} seconds")
        print(f"Total Evaluations: {evolution.get('total_evaluations', 'N/A')}")
        print(f"Evaluations/sec: {evolution.get('evaluations_per_second', 0):.1f}")
        
        # Fitness metrics
        fitness = evolution_stats.get('fitness', {})
        print(f"Best Fitness: {fitness.get('best_achieved', 'N/A')}")
        
        # Final solution
        final = evolution_stats.get('final_solution', {})
        if final:
            print(f"Final Solution:")
            print(f"  - Feasible: {'Yes' if final.get('is_feasible', False) else 'No'}")
            print(f"  - Hard Violations: {final.get('hard_violations', 'N/A')}")
            print(f"  - Soft Violations: {final.get('soft_violations', 'N/A')}")
            print(f"  - Total Sessions: {final.get('total_genes', 'N/A')}")
        
        print("="*60)
