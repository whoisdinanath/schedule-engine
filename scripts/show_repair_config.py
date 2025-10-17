"""
Display current repair heuristics configuration.
Quick utility to see which repair heuristics are enabled and their priorities.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from config.ga_params import REPAIR_HEURISTICS_CONFIG
from src.ga.operators.repair_registry import (
    get_all_repair_heuristics,
    get_enabled_repair_heuristics,
)

console = Console()


def main():
    """Display repair heuristics configuration in a readable format."""

    # Header
    console.print()
    console.rule("[bold cyan]REPAIR HEURISTICS CONFIGURATION[/bold cyan]", style="cyan")
    console.print()

    # Global settings
    global_enabled = REPAIR_HEURISTICS_CONFIG.get("enabled", True)
    max_iterations = REPAIR_HEURISTICS_CONFIG.get("max_iterations", 3)
    apply_after_mutation = REPAIR_HEURISTICS_CONFIG.get("apply_after_mutation", True)
    apply_after_crossover = REPAIR_HEURISTICS_CONFIG.get("apply_after_crossover", False)
    memetic_mode = REPAIR_HEURISTICS_CONFIG.get("memetic_mode", False)

    # Global settings panel
    global_status = "✓ ENABLED" if global_enabled else "✗ DISABLED"
    global_color = "green" if global_enabled else "red"

    console.print(
        Panel(
            f"[bold]Master Switch:[/bold] [{global_color}]{global_status}[/{global_color}]\n"
            f"[bold]Max Iterations:[/bold] {max_iterations}\n"
            f"[bold]Apply After Mutation:[/bold] {'✓ Yes' if apply_after_mutation else '✗ No'}\n"
            f"[bold]Apply After Crossover:[/bold] {'✓ Yes' if apply_after_crossover else '✗ No'}\n"
            f"[bold]Memetic Mode:[/bold] {'✓ Enabled' if memetic_mode else '✗ Disabled'}",
            title="[bold]Global Settings[/bold]",
            border_style="cyan",
        )
    )
    console.print()

    # Get repair heuristics
    all_repairs = get_all_repair_heuristics()
    enabled_repairs = get_enabled_repair_heuristics()

    enabled_count = len(enabled_repairs)
    total_count = len(all_repairs)

    console.print(
        f"[bold]Status:[/bold] {enabled_count}/{total_count} repair heuristics enabled"
    )
    console.print()

    # Enabled repairs table
    if enabled_repairs:
        console.print("[bold green]✓ ENABLED REPAIR HEURISTICS[/bold green]")

        table = Table(show_header=True, header_style="bold green", box=None)
        table.add_column("Priority", justify="center", style="cyan", width=8)
        table.add_column("Heuristic Name", style="green")
        table.add_column("Modifies Length", justify="center", width=15)
        table.add_column("Description", style="dim")

        for name, info in enabled_repairs.items():
            priority = str(info["priority"])
            modifies = "⚠️  YES" if info.get("modifies_length", False) else "NO"
            description = info.get("description", "")

            table.add_row(priority, name, modifies, description)

        console.print(table)
        console.print()

    # Disabled repairs table
    disabled_repairs = {
        name: info for name, info in all_repairs.items() if name not in enabled_repairs
    }

    if disabled_repairs:
        console.print("[bold red]✗ DISABLED REPAIR HEURISTICS[/bold red]")

        table = Table(show_header=True, header_style="bold red", box=None)
        table.add_column("Priority", justify="center", style="dim", width=8)
        table.add_column("Heuristic Name", style="red dim")
        table.add_column("Description", style="dim")

        # Sort by priority
        sorted_disabled = sorted(
            disabled_repairs.items(), key=lambda x: x[1]["priority"]
        )

        for name, info in sorted_disabled:
            priority = str(info["priority"])
            description = info.get("description", "")

            table.add_row(priority, name, description)

        console.print(table)
        console.print()

    # Summary
    console.rule(
        "[dim]Configuration loaded from config/ga_params.py::REPAIR_HEURISTICS_CONFIG[/dim]"
    )
    console.print()


if __name__ == "__main__":
    main()
