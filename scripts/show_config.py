"""
Display current constraint configuration (both hard and soft).
Quick utility to see which constraints are enabled and their weights.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.constraints import HARD_CONSTRAINTS_CONFIG, SOFT_CONSTRAINTS_CONFIG
from src.constraints.hard import get_enabled_hard_constraints
from src.constraints.soft import get_enabled_soft_constraints


def main():
    print("=" * 80)
    print("CONSTRAINT CONFIGURATION (HARD + SOFT)")
    print("=" * 80)

    # Hard Constraints Section
    print("\n" + "=" * 80)
    print("HARD CONSTRAINTS (Feasibility)")
    print("=" * 80)

    hard_enabled_count = sum(
        1 for cfg in HARD_CONSTRAINTS_CONFIG.values() if cfg["enabled"]
    )
    hard_total_count = len(HARD_CONSTRAINTS_CONFIG)

    print(
        f"\nStatus: {hard_enabled_count}/{hard_total_count} hard constraints enabled\n"
    )

    # Show enabled hard constraints
    hard_enabled = get_enabled_hard_constraints()
    if hard_enabled:
        print("ENABLED HARD CONSTRAINTS:")
        print("-" * 80)
        for name, info in hard_enabled.items():
            print(f"  ✓ {name:<45} weight = {info['weight']:.2f}")
        print()

    # Show disabled hard constraints
    hard_disabled = [
        name for name, cfg in HARD_CONSTRAINTS_CONFIG.items() if not cfg["enabled"]
    ]
    if hard_disabled:
        print("DISABLED HARD CONSTRAINTS:")
        print("-" * 80)
        for name in hard_disabled:
            print(
                f"  ✗ {name:<45} (weight = {HARD_CONSTRAINTS_CONFIG[name]['weight']:.2f})"
            )
        print()

    # Show total hard weight
    total_hard_weight = sum(info["weight"] for info in hard_enabled.values())
    print(f"Total enabled hard weight: {total_hard_weight:.2f}")

    # Soft Constraints Section
    print("\n" + "=" * 80)
    print("SOFT CONSTRAINTS (Quality)")
    print("=" * 80)

    soft_enabled_count = sum(
        1 for cfg in SOFT_CONSTRAINTS_CONFIG.values() if cfg["enabled"]
    )
    soft_total_count = len(SOFT_CONSTRAINTS_CONFIG)

    print(
        f"\nStatus: {soft_enabled_count}/{soft_total_count} soft constraints enabled\n"
    )

    # Show enabled soft constraints
    soft_enabled = get_enabled_soft_constraints()
    if soft_enabled:
        print("ENABLED SOFT CONSTRAINTS:")
        print("-" * 80)
        for name, info in soft_enabled.items():
            print(f"  ✓ {name:<45} weight = {info['weight']:.2f}")
        print()

    # Show disabled soft constraints
    soft_disabled = [
        name for name, cfg in SOFT_CONSTRAINTS_CONFIG.items() if not cfg["enabled"]
    ]
    if soft_disabled:
        print("DISABLED SOFT CONSTRAINTS:")
        print("-" * 80)
        for name in soft_disabled:
            print(
                f"  ✗ {name:<45} (weight = {SOFT_CONSTRAINTS_CONFIG[name]['weight']:.2f})"
            )
        print()

    # Show total soft weight
    total_soft_weight = sum(info["weight"] for info in soft_enabled.values())
    print(f"Total enabled soft weight: {total_soft_weight:.2f}")

    # Summary
    print("\n" + "=" * 80)
    print(
        f"SUMMARY: {hard_enabled_count + soft_enabled_count} total constraints enabled"
    )
    print(f"  - Hard: {hard_enabled_count}/{hard_total_count}")
    print(f"  - Soft: {soft_enabled_count}/{soft_total_count}")
    print("=" * 80)
    print(f"\nTo modify: Edit config/constraints.py")


if __name__ == "__main__":
    main()
