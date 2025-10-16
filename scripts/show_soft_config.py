"""
Display current soft constraint configuration.
Quick utility to see which constraints are enabled and their weights.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.constraints import SOFT_CONSTRAINTS_CONFIG
from src.constraints.soft import get_enabled_soft_constraints
from src.utils.console import write_header, write_separator, write_info


def main():
    write_header("SOFT CONSTRAINT CONFIGURATION")

    enabled_count = sum(1 for cfg in SOFT_CONSTRAINTS_CONFIG.values() if cfg["enabled"])
    total_count = len(SOFT_CONSTRAINTS_CONFIG)

    write_info(f"Status: {enabled_count}/{total_count} constraints enabled")
    write_info("")

    # Show enabled constraints
    enabled = get_enabled_soft_constraints()
    if enabled:
        write_info("ENABLED CONSTRAINTS:")
        write_separator("-")
        for name, info in enabled.items():
            write_info(f"  {name:<40} weight = {info['weight']:.2f}")
        write_info("")

    # Show disabled constraints
    disabled = [
        name for name, cfg in SOFT_CONSTRAINTS_CONFIG.items() if not cfg["enabled"]
    ]
    if disabled:
        write_info("DISABLED CONSTRAINTS:")
        write_separator("-")
        for name in disabled:
            write_info(
                f"  {name:<40} (weight = {SOFT_CONSTRAINTS_CONFIG[name]['weight']:.2f})"
            )
        write_info("")

    # Show total weight
    total_weight = sum(info["weight"] for info in enabled.values())
    write_info(f"Total enabled weight: {total_weight:.2f}")
    write_separator()
    write_info("")
    write_info("To modify: Edit config/constraints.py")


if __name__ == "__main__":
    main()
