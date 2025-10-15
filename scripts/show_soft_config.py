"""
Display current soft constraint configuration.
Quick utility to see which constraints are enabled and their weights.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.constraints import SOFT_CONSTRAINTS_CONFIG
from src.constraints.soft import get_enabled_soft_constraints


def main():
    print("=" * 70)
    print("SOFT CONSTRAINT CONFIGURATION")
    print("=" * 70)

    enabled_count = sum(1 for cfg in SOFT_CONSTRAINTS_CONFIG.values() if cfg["enabled"])
    total_count = len(SOFT_CONSTRAINTS_CONFIG)

    print(f"\nStatus: {enabled_count}/{total_count} constraints enabled\n")

    # Show enabled constraints
    enabled = get_enabled_soft_constraints()
    if enabled:
        print("ENABLED CONSTRAINTS:")
        print("-" * 70)
        for name, info in enabled.items():
            print(f"  ✓ {name:<40} weight = {info['weight']:.2f}")
        print()

    # Show disabled constraints
    disabled = [
        name for name, cfg in SOFT_CONSTRAINTS_CONFIG.items() if not cfg["enabled"]
    ]
    if disabled:
        print("DISABLED CONSTRAINTS:")
        print("-" * 70)
        for name in disabled:
            print(
                f"  ✗ {name:<40} (weight = {SOFT_CONSTRAINTS_CONFIG[name]['weight']:.2f})"
            )
        print()

    # Show total weight
    total_weight = sum(info["weight"] for info in enabled.values())
    print(f"Total enabled weight: {total_weight:.2f}")
    print("=" * 70)
    print(f"\nTo modify: Edit config/constraints.py")


if __name__ == "__main__":
    main()
