#!/usr/bin/env python3
"""
Debug script to analyze why constraint violations are not decreasing.
This will help identify the specific constraint violations causing high fitness scores.
"""

import random
from src.encoder.quantum_time_system import QuantumTimeSystem
from src.encoder.input_encoder import (
    load_courses,
    load_groups,
    load_instructors,
    load_rooms,
    link_courses_and_groups,
    link_courses_and_instructors,
)
from src.ga.population import generate_course_group_aware_population
from src.ga.evaluator.fitness import evaluate
from src.decoder.individual_decoder import decode_individual

# Import constraint functions directly for detailed analysis
from src.constraints.hard import (
    no_group_overlap,
    no_instructor_conflict,
    instructor_not_qualified,
    room_type_mismatch,
    availability_violations,
    incomplete_or_extra_sessions,
)

from src.constraints.soft import (
    group_gaps_penalty,
    instructor_gaps_penalty,
    group_midday_break_violation,
    course_split_penalty,
    early_or_late_session_penalty,
)


def analyze_constraint_violations():
    """Analyze constraint violations in detail."""

    print("Analyzing Constraint Violations...")
    print("=" * 50)

    # Initialize RNG
    random.seed(42)

    # Initialize quantum time system
    qts = QuantumTimeSystem()

    # Load data
    print("Loading data...")
    courses = load_courses("data/Course.json")
    groups = load_groups("data/Groups.json", qts)
    instructors = load_instructors("data/Instructors.json", qts)
    rooms = load_rooms("data/Rooms.json", qts)

    link_courses_and_groups(courses, groups)
    link_courses_and_instructors(courses, instructors)

    # Prepare context
    context = {
        "courses": courses,
        "instructors": instructors,
        "groups": groups,
        "rooms": rooms,
        "available_quanta": qts.get_all_operating_quanta(),
    }

    print(
        f"Loaded {len(courses)} courses, {len(groups)} groups, {len(instructors)} instructors, {len(rooms)} rooms"
    )
    print(f"Available time quanta: {len(context['available_quanta'])}")

    # Generate one individual for testing
    population = generate_course_group_aware_population(1, context)
    individual = population[0]

    print(f"\nGenerated individual with {len(individual)} genes")

    # Decode individual for constraint checking
    sessions = decode_individual(individual, courses, instructors, groups, rooms)
    print(f"Decoded to {len(sessions)} sessions")

    # Analyze each hard constraint individually
    print("\nHARD CONSTRAINT ANALYSIS:")
    print("-" * 30)

    try:
        violation = no_group_overlap(sessions)
        print(f"Group overlap violations: {violation}")
    except Exception as e:
        print(f"Group overlap check failed: {e}")

    try:
        violation = no_instructor_conflict(sessions)
        print(f"Instructor conflict violations: {violation}")
    except Exception as e:
        print(f"Instructor conflict check failed: {e}")

    try:
        violation = instructor_not_qualified(sessions, courses)
        print(f"Instructor qualification violations: {violation}")
    except Exception as e:
        print(f"Instructor qualification check failed: {e}")

    try:
        violation = room_type_mismatch(sessions)
        print(f"Room type mismatch violations: {violation}")
    except Exception as e:
        print(f"Room type mismatch check failed: {e}")

    try:
        violation = availability_violations(sessions)
        print(f"Availability violations: {violation}")
    except Exception as e:
        print(f"Availability check failed: {e}")

    try:
        violation = incomplete_or_extra_sessions(sessions, courses)
        print(f"Incomplete/extra sessions violations: {violation}")
    except Exception as e:
        print(f"Session completeness check failed: {e}")

    # Analyze soft constraints
    print("\nSOFT CONSTRAINT ANALYSIS:")
    print("-" * 30)

    try:
        penalty = group_gaps_penalty(sessions)
        print(f"Group gaps penalty: {penalty}")
    except Exception as e:
        print(f"Group gaps check failed: {e}")

    try:
        penalty = instructor_gaps_penalty(sessions)
        print(f"Instructor gaps penalty: {penalty}")
    except Exception as e:
        print(f"Instructor gaps check failed: {e}")

    try:
        penalty = group_midday_break_violation(sessions)
        print(f"Midday break violation penalty: {penalty}")
    except Exception as e:
        print(f"Midday break check failed: {e}")

    try:
        penalty = course_split_penalty(sessions)
        print(f"Course split penalty: {penalty}")
    except Exception as e:
        print(f"Course split check failed: {e}")

    try:
        penalty = early_or_late_session_penalty(sessions)
        print(f"Early/late session penalty: {penalty}")
    except Exception as e:
        print(f"Early/late session check failed: {e}")

    # Overall fitness
    fitness = evaluate(individual, courses, instructors, groups, rooms)
    print(f"\nOVERALL FITNESS: Hard={fitness[0]}, Soft={fitness[1]}")

    # Sample session analysis
    print(f"\nSAMPLE SESSIONS (first 5):")
    print("-" * 30)
    for i, session in enumerate(sessions[:5]):
        print(f"Session {i+1}:")
        print(f"  Course: {session.course_id}")
        print(f"  Instructor: {session.instructor_id}")
        print(f"  Group: {session.group_ids}")
        print(f"  Room: {session.room_id}")
        print(f"  Time Quanta: {session.session_quanta}")

        # Check specific issues for this session
        group_obj = groups.get(session.group_ids[0]) if session.group_ids else None
        if group_obj:
            if session.course_id in group_obj.enrolled_courses:
                print(f"  ✓ Valid course-group enrollment")
            else:
                print(f"  ✗ Invalid course-group enrollment!")

        instructor_obj = instructors.get(session.instructor_id)
        if instructor_obj:
            if session.course_id in getattr(instructor_obj, "qualified_courses", []):
                print(f"  ✓ Qualified instructor")
            else:
                print(f"  ✗ Unqualified instructor!")

        room_obj = rooms.get(session.room_id)
        if room_obj:
            print(f"  Room capacity: {getattr(room_obj, 'capacity', 'unknown')}")

        print()


if __name__ == "__main__":
    analyze_constraint_violations()
