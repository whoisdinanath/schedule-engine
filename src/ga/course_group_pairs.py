"""
Course-Group Pair Generator

Generates (Course, Group) pairs following parent-subgroup rules:
- Theory (L+T): Parent group (all subgroups attend together)
- Practical (P): Each subgroup separately
"""

from typing import Dict, List, Tuple
from src.entities.course import Course
from src.entities.group import Group


def generate_course_group_pairs(
    courses: Dict[str, Course], groups: Dict[str, Group], hierarchy: Dict
) -> List[Tuple[str, List[str], str, int]]:
    """
    Generates (course_id, group_ids, session_type, num_quanta) tuples.

    Rules:
    - Theory sessions: Assign to parent group (subgroups attend together)
    - Practical sessions: Assign to each subgroup separately
    - Standalone groups: Get both theory and practical

    Args:
        courses: Dictionary of course_id -> Course
        groups: Dictionary of group_id -> Group
        hierarchy: Output from analyze_group_hierarchy()

    Returns:
        List of tuples: (course_id, group_ids, session_type, num_quanta)

    Example:
        [
            ("ENME 151", ["BAE2"], "theory", 5),           # Theory for parent
            ("ENME 151-PR", ["BAE2A"], "practical", 3),    # Practical for subgroup A
            ("ENME 151-PR", ["BAE2B"], "practical", 3),    # Practical for subgroup B
        ]
    """
    pairs = []

    # Get all parent and standalone groups (these are the ones we iterate)
    scheduling_groups = hierarchy["parents"] + hierarchy["standalone"]

    for group_id in scheduling_groups:
        group = groups.get(group_id)
        if not group:
            continue

        enrolled_courses = group.enrolled_courses
        has_subs = group_id in hierarchy.get("subgroups", {})
        subgroup_list = hierarchy["subgroups"].get(group_id, []) if has_subs else []

        for course_id in enrolled_courses:
            course = courses.get(course_id)
            if not course:
                print(f"⚠️  Warning: Course {course_id} not found for group {group_id}")
                continue

            # Get L, T, P values
            L = getattr(course, "L", getattr(course, "lecture_hours", 0))
            T = getattr(course, "T", getattr(course, "tutorial_hours", 0))
            P = getattr(course, "P", getattr(course, "practical_hours", 0))

            # Theory sessions (L+T)
            if L + T > 0:
                theory_quanta = L + T

                # Theory always uses parent group (whole class together)
                # Even if subgroups exist, they attend theory together
                pairs.append((course_id, [group_id], "theory", theory_quanta))

            # Practical sessions (P)
            if P > 0:
                practical_course_id = (
                    course_id + "-PR" if not course_id.endswith("-PR") else course_id
                )

                if has_subs:
                    # Split practical across subgroups
                    for subgroup_id in subgroup_list:
                        pairs.append(
                            (practical_course_id, [subgroup_id], "practical", P)
                        )
                else:
                    # No subgroups, assign practical to parent/standalone group
                    pairs.append((practical_course_id, [group_id], "practical", P))

    return pairs


def count_total_genes(pairs: List[Tuple]) -> int:
    """Count total number of genes that will be created."""
    return sum(num_quanta for _, _, _, num_quanta in pairs)


def group_pairs_by_course(pairs: List[Tuple]) -> Dict[str, List[Tuple]]:
    """Group pairs by course for analysis."""
    from collections import defaultdict

    course_pairs = defaultdict(list)
    for pair in pairs:
        course_id = pair[0]
        course_pairs[course_id].append(pair)
    return dict(course_pairs)


if __name__ == "__main__":
    # Quick test
    from src.encoder.input_encoder import load_groups, load_courses
    from src.encoder.quantum_time_system import QuantumTimeSystem
    from src.ga.group_hierarchy import analyze_group_hierarchy

    qts = QuantumTimeSystem()
    groups = load_groups("data/Groups.json", qts)
    courses = load_courses("data/Course.json")
    hierarchy = analyze_group_hierarchy(groups)

    pairs = generate_course_group_pairs(courses, groups, hierarchy)

    print("=" * 70)
    print("Course-Group Pair Generation")
    print("=" * 70)
    print(f"\n📊 Total pairs: {len(pairs)}")
    print(f"🧬 Total genes to create: {count_total_genes(pairs)}")
    print()

    # Show some examples
    print("Example Theory Pairs (Parent Group):")
    theory_pairs = [p for p in pairs if p[2] == "theory"][:5]
    for course_id, group_ids, session_type, num_quanta in theory_pairs:
        print(f"  {course_id} → {group_ids} ({num_quanta} quanta)")
    print()

    print("Example Practical Pairs (Subgroups):")
    practical_pairs = [p for p in pairs if p[2] == "practical"][:5]
    for course_id, group_ids, session_type, num_quanta in practical_pairs:
        print(f"  {course_id} → {group_ids} ({num_quanta} quanta)")
    print()

    # Analyze one course
    course_groups = group_pairs_by_course(pairs)
    if course_groups:
        sample_course = list(course_groups.keys())[0]
        print(f"Detailed breakdown for {sample_course}:")
        for course_id, group_ids, session_type, num_quanta in course_groups[
            sample_course
        ]:
            print(f"  {session_type.upper()}: {group_ids} ({num_quanta} quanta)")
