"""
Group Hierarchy Analyzer

Identifies parent groups and their subgroups to enable proper scheduling:
- Theory sessions for parent (whole class together)
- Practical sessions for subgroups separately
"""

from typing import Dict, List, Set
from src.entities.group import Group


def analyze_group_hierarchy(groups: Dict[str, Group]) -> Dict:
    """
    Analyzes group relationships to identify parents and subgroups.

    A subgroup is identified by:
    - Having a parent group ID as prefix (e.g., BAE2A has parent BAE2)
    - Parent group must exist in groups dict

    Args:
        groups: Dictionary of group_id -> Group objects

    Returns:
        Dictionary with:
        - "parents": List of parent group IDs
        - "subgroups": Dict mapping parent_id -> [subgroup_ids]
        - "parent_map": Dict mapping subgroup_id -> parent_id
        - "standalone": List of groups with no subgroups

    Example:
        {
            "parents": ["BAE2", "BAE4"],
            "subgroups": {"BAE2": ["BAE2A", "BAE2B"], "BAE4": ["BAE4A", "BAE4B"]},
            "parent_map": {"BAE2A": "BAE2", "BAE2B": "BAE2", "BAE4A": "BAE4", "BAE4B": "BAE4"},
            "standalone": ["BAE8"]  # Groups with no subgroups
        }
    """
    parents = set()
    subgroups_dict = {}  # parent_id -> [subgroup_ids]
    parent_map = {}  # subgroup_id -> parent_id
    all_group_ids = set(groups.keys())

    # Identify parent-subgroup relationships
    for group_id in all_group_ids:
        # Check if this could be a subgroup (ends with letter)
        if len(group_id) > 1 and group_id[-1].isalpha():
            # Try to find parent by removing last character
            potential_parent = group_id[:-1]

            if potential_parent in all_group_ids:
                # This is a subgroup!
                parents.add(potential_parent)
                parent_map[group_id] = potential_parent

                if potential_parent not in subgroups_dict:
                    subgroups_dict[potential_parent] = []
                subgroups_dict[potential_parent].append(group_id)

    # Identify standalone groups (neither parent nor subgroup)
    parents_list = sorted(list(parents))
    all_subgroups = set(parent_map.keys())
    standalone = sorted(list(all_group_ids - parents - all_subgroups))

    return {
        "parents": parents_list,
        "subgroups": subgroups_dict,
        "parent_map": parent_map,
        "standalone": standalone,
    }


def is_parent_group(group_id: str, hierarchy: Dict) -> bool:
    """Check if a group is a parent group."""
    return group_id in hierarchy["parents"]


def is_subgroup(group_id: str, hierarchy: Dict) -> bool:
    """Check if a group is a subgroup."""
    return group_id in hierarchy["parent_map"]


def get_parent(group_id: str, hierarchy: Dict) -> str:
    """Get parent group ID for a subgroup."""
    return hierarchy["parent_map"].get(group_id)


def get_subgroups(parent_id: str, hierarchy: Dict) -> List[str]:
    """Get list of subgroup IDs for a parent."""
    return hierarchy["subgroups"].get(parent_id, [])


def has_subgroups(group_id: str, hierarchy: Dict) -> bool:
    """Check if a group has subgroups."""
    return group_id in hierarchy["subgroups"]


if __name__ == "__main__":
    # Quick test
    from src.encoder.input_encoder import load_groups
    from src.encoder.quantum_time_system import QuantumTimeSystem
    from src.utils.console import write_header, write_info

    qts = QuantumTimeSystem()
    groups = load_groups("data/Groups.json", qts)

    hierarchy = analyze_group_hierarchy(groups)

    write_header("Group Hierarchy Analysis")
    write_info(f"Total groups: {len(groups)}")
    write_info(f"Parent groups: {len(hierarchy['parents'])}")
    write_info(f"Standalone groups: {len(hierarchy['standalone'])}")
    write_info(f"Total subgroups: {len(hierarchy['parent_map'])}")
    write_info("")

    write_info("Parent Groups and Their Subgroups:")
    for parent in hierarchy["parents"][:5]:  # Show first 5
        subgroups = hierarchy["subgroups"][parent]
        write_info(f"  {parent} -> {subgroups}")
    print()

    print("Standalone Groups (no subgroups):")
    print(f"  {hierarchy['standalone']}")
