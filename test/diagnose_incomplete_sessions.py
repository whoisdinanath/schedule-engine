"""
Diagnostic script to find root cause of incomplete/extra sessions issue.

Compares:
1. What the population generator creates (course-group pairs)
2. What the constraint checker expects (enrolled_group_ids in courses)
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.encoder.input_encoder import (
    load_groups,
    load_courses,
    link_courses_and_groups,
)
from src.encoder.quantum_time_system import QuantumTimeSystem
from src.ga.group_hierarchy import analyze_group_hierarchy
from src.ga.course_group_pairs import generate_course_group_pairs
from collections import defaultdict


def main():
    print("=" * 80)
    print("DIAGNOSING INCOMPLETE OR EXTRA SESSIONS ISSUE")
    print("=" * 80)

    # Load data
    qts = QuantumTimeSystem()
    groups = load_groups("data/Groups.json", qts)

    # Load all courses
    all_courses = load_courses("data/Course.json")

    # Filter to enrolled courses only
    enrolled_course_codes = set()
    for group in groups.values():
        enrolled_course_codes.update(group.enrolled_courses)

    courses = {}
    for course_key, course in all_courses.items():
        course_code = course_key[0]
        if course_code in enrolled_course_codes:
            courses[course_key] = course

    print(f"\nData loaded:")
    print(f"   Groups: {len(groups)}")
    print(f"   Enrolled course codes: {len(enrolled_course_codes)}")
    print(f"   Course objects (filtered): {len(courses)}")

    # Link courses and groups (this populates enrolled_group_ids)
    link_courses_and_groups(courses, groups)

    print("\n" + "=" * 80)
    print("PART 1: What POPULATION GENERATOR creates")
    print("=" * 80)

    # Generate course-group pairs (what population generator uses)
    hierarchy = analyze_group_hierarchy(groups)
    pair_tuples = generate_course_group_pairs(courses, groups, hierarchy)

    # Convert to (course_key, group_ids) format for analysis
    population_pairs = set()
    for course_key, group_ids, session_type, num_quanta in pair_tuples:
        # For multi-group sessions (theory), create tuple with sorted groups
        group_tuple = tuple(sorted(group_ids))
        population_pairs.add((course_key, group_tuple))

    print(f"\nTotal pairs created by population generator: {len(population_pairs)}")

    # Count by course type
    theory_pairs = [p for p in pair_tuples if p[2] == "theory"]
    practical_pairs = [p for p in pair_tuples if p[2] == "practical"]
    print(f"   Theory sessions: {len(theory_pairs)}")
    print(f"   Practical sessions: {len(practical_pairs)}")

    print("\n" + "=" * 80)
    print("PART 2: What CONSTRAINT CHECKER expects")
    print("=" * 80)

    # What the constraint expects (from enrolled_group_ids)
    constraint_expectations = set()
    for course_key, course in courses.items():
        for group_id in course.enrolled_group_ids:
            # Constraint checks EACH (course, group) combination individually
            constraint_expectations.add((course_key, (group_id,)))

    print(
        f"\nTotal (course, group) combinations expected by constraint: {len(constraint_expectations)}"
    )

    # Group by course type
    theory_expectations = [
        exp for exp in constraint_expectations if exp[0][1] == "theory"
    ]
    practical_expectations = [
        exp for exp in constraint_expectations if exp[0][1] == "practical"
    ]
    print(f"   Theory course expectations: {len(theory_expectations)}")
    print(f"   Practical course expectations: {len(practical_expectations)}")

    print("\n" + "=" * 80)
    print("PART 3: COMPARISON - Finding the mismatch")
    print("=" * 80)

    # Expand population pairs to individual groups for comparison with constraint
    population_individual_groups = set()
    for course_key, group_tuple in population_pairs:
        for group_id in group_tuple:
            population_individual_groups.add((course_key, (group_id,)))

    print(
        f"\nPopulation pairs (expanded to individual groups): {len(population_individual_groups)}"
    )
    print(f"Constraint expectations: {len(constraint_expectations)}")

    # Find differences
    missing_in_population = constraint_expectations - population_individual_groups
    extra_in_population = population_individual_groups - constraint_expectations

    if missing_in_population:
        print(
            f"\n[X] MISSING in population (but expected by constraint): {len(missing_in_population)}"
        )
        print("\nFirst 10 missing pairs:")
        for i, (course_key, group_tuple) in enumerate(
            list(missing_in_population)[:10], 1
        ):
            course_code, course_type = course_key
            group_id = group_tuple[0]
            print(f"   {i}. ({course_code}, {course_type}) + Group {group_id}")

            # Check if this group enrolled this course
            group = groups.get(group_id)
            if group:
                enrolled = (
                    course_code in group.enrolled_courses
                    if hasattr(group, "enrolled_courses")
                    else False
                )
                print(f"      Group enrolled: {enrolled}")
                if enrolled:
                    print(f"      Group's enrolled courses: {group.enrolled_courses}")

    if extra_in_population:
        print(
            f"\n[X] EXTRA in population (not expected by constraint): {len(extra_in_population)}"
        )
        print("\nFirst 10 extra pairs:")
        for i, (course_key, group_tuple) in enumerate(
            list(extra_in_population)[:10], 1
        ):
            course_code, course_type = course_key
            group_id = group_tuple[0]
            print(f"   {i}. ({course_code}, {course_type}) + Group {group_id}")

    if not missing_in_population and not extra_in_population:
        print("\n[OK] PERFECT MATCH! No discrepancies found.")
        print("   Population generator and constraint checker are aligned.")
    else:
        print("\n" + "=" * 80)
        print("ROOT CAUSE ANALYSIS")
        print("=" * 80)

        if missing_in_population:
            # Analyze why population generator missed these pairs
            print("\n[?] Why are pairs MISSING from population?")
            sample_missing = list(missing_in_population)[0]
            course_key, group_tuple = sample_missing
            course_code, course_type = course_key
            group_id = group_tuple[0]

            print(f"\nSample: ({course_code}, {course_type}) + Group {group_id}")

            # Check if course exists in courses dict
            if course_key in courses:
                course = courses[course_key]
                print(f"   [+] Course exists in courses dict")
                print(f"   Course enrolled_group_ids: {course.enrolled_group_ids}")
            else:
                print(f"   [-] Course NOT in courses dict!")

            # Check if group exists
            if group_id in groups:
                group = groups[group_id]
                print(f"   [+] Group exists in groups dict")
                print(f"   Group enrolled_courses: {group.enrolled_courses}")
                print(
                    f"   Is '{course_code}' in group's enrolled_courses? {course_code in group.enrolled_courses}"
                )
            else:
                print(f"   [-] Group NOT in groups dict!")

        if extra_in_population:
            print("\n[?] Why are pairs EXTRA in population?")
            sample_extra = list(extra_in_population)[0]
            course_key, group_tuple = sample_extra
            course_code, course_type = course_key
            group_id = group_tuple[0]

            print(f"\nSample: ({course_code}, {course_type}) + Group {group_id}")

            if course_key in courses:
                course = courses[course_key]
                print(f"   [+] Course exists in courses dict")
                print(f"   Course enrolled_group_ids: {course.enrolled_group_ids}")
                print(
                    f"   Is group {group_id} in enrolled_group_ids? {group_id in course.enrolled_group_ids}"
                )

            if group_id in groups:
                group = groups[group_id]
                print(f"   [+] Group exists in groups dict")
                print(f"   Group enrolled_courses: {group.enrolled_courses}")

    print("\n" + "=" * 80)
    print("DIAGNOSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
