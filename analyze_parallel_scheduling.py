#!/usr/bin/env python3
"""
Parallel Scheduling Analyzer

This script analyzes and displays how many courses are actually scheduled
in parallel at each time slot to demonstrate the system's parallel scheduling capability.
"""

import json
from collections import defaultdict
from pathlib import Path
from src.ga_deap.enhanced_system import EnhancedTimetablingSystem
from src.encoders.quantum_time_system import QuantumTimeSystem
from src.encoders.input_encoder import (
    load_courses,
    load_instructors,
    load_groups,
    load_rooms,
)


def analyze_parallel_scheduling():
    """Analyze and display parallel scheduling in the current solution."""

    print("🔍 PARALLEL SCHEDULING ANALYSIS")
    print("=" * 60)

    # Initialize the system
    system = EnhancedTimetablingSystem(data_path="data")

    # Load data
    success, issues = system.load_data()
    if not success:
        print("❌ Failed to load data")
        return

    # Run optimization
    print("🚀 Running optimization...")
    best_solution = system.run_optimization(generations=20, population_size=50)

    if not best_solution:
        print("❌ No solution found")
        return

    print(f"✅ Found solution with {len(best_solution)} total sessions")
    print()

    # Group sessions by quantum (time slot)
    quantum_schedule = defaultdict(list)

    for session in best_solution:
        for quantum in session.quanta:
            quantum_schedule[quantum].append(session)

    # Analyze parallel scheduling
    print("📊 TIME SLOT ANALYSIS")
    print("-" * 40)

    parallel_count = 0
    total_parallel_sessions = 0

    for quantum, sessions in sorted(quantum_schedule.items()):
        try:
            day, time = system.qts.quanta_to_time(quantum)

            print(f"\n⏰ {day} at {time} (Quantum {quantum})")
            print(f"   📈 {len(sessions)} course(s) scheduled in parallel")

            if len(sessions) > 1:
                parallel_count += 1
                total_parallel_sessions += len(sessions)

                # Show all parallel courses
                for i, session in enumerate(sessions, 1):
                    course = system.courses[session.course_id]
                    instructor = system.instructors[session.instructor_id]
                    group = system.groups[session.group_id]
                    room = system.rooms[session.room_id]

                    print(f"   {i}. 📚 {course.name}")
                    print(f"      👨‍🏫 {instructor.name}")
                    print(f"      👥 {group.name}")
                    print(f"      🏢 {room.name}")
            else:
                # Single session
                session = sessions[0]
                course = system.courses[session.course_id]
                instructor = system.instructors[session.instructor_id]
                group = system.groups[session.group_id]
                room = system.rooms[session.room_id]

                print(
                    f"   1. 📚 {course.name} | 👨‍🏫 {instructor.name} | 👥 {group.name} | 🏢 {room.name}"
                )

        except Exception as e:
            print(f"   ❌ Error processing quantum {quantum}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("📋 PARALLEL SCHEDULING SUMMARY")
    print("=" * 60)
    print(f"Total time slots used: {len(quantum_schedule)}")
    print(f"Time slots with parallel scheduling: {parallel_count}")
    print(f"Total parallel sessions: {total_parallel_sessions}")
    print(f"Single-course time slots: {len(quantum_schedule) - parallel_count}")

    if parallel_count > 0:
        print(f"✅ SUCCESS: System schedules multiple courses in parallel!")
        print(
            f"   Parallel efficiency: {(parallel_count / len(quantum_schedule)) * 100:.1f}%"
        )
    else:
        print("❌ NO PARALLEL SCHEDULING: Only one course per time slot")

    # Show course distribution
    print("\n📊 COURSE DISTRIBUTION")
    print("-" * 30)

    course_sessions = defaultdict(int)
    for session in best_solution:
        course_sessions[session.course_id] += 1

    for course_id, count in course_sessions.items():
        course = system.courses[course_id]
        print(f"📚 {course.name}: {count} sessions")

    return parallel_count > 0


def create_time_grid_visualization():
    """Create a visual grid showing parallel scheduling."""

    print("\n🎯 CREATING TIME GRID VISUALIZATION")
    print("=" * 60)

    # Initialize the system
    system = EnhancedTimetablingSystem(data_path="data")
    success, issues = system.load_data()

    if not success:
        print("❌ Failed to load data")
        return

    # Run optimization
    best_solution = system.run_optimization(generations=20, population_size=50)

    if not best_solution:
        print("❌ No solution found")
        return

    # Create time grid
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    times = ["08:00", "09:15", "10:30", "11:45", "13:00", "14:15", "15:30", "16:45"]

    # Group sessions by day and time
    schedule_grid = defaultdict(lambda: defaultdict(list))

    for session in best_solution:
        for quantum in session.quanta:
            try:
                day, time = system.qts.quanta_to_time(quantum)
                schedule_grid[day][time].append(session)
            except:
                continue

    # Display grid
    print("\n📅 WEEKLY SCHEDULE GRID")
    print("=" * 100)

    # Header
    print(f"{'Time':<8}", end=" | ")
    for day in days:
        print(f"{day:<15}", end=" | ")
    print()
    print("-" * 100)

    # Time slots
    for time in times:
        print(f"{time:<8}", end=" | ")

        for day in days:
            sessions = schedule_grid[day].get(time, [])
            if len(sessions) == 0:
                print(f"{'---':<15}", end=" | ")
            elif len(sessions) == 1:
                course = system.courses[sessions[0].course_id]
                print(f"{course.name[:12]:<15}", end=" | ")
            else:
                parallel_text = f"{len(sessions)} PARALLEL"
                print(f"{parallel_text:<15}", end=" | ")

        print()

    print("-" * 100)

    # Show parallel slots detail
    print("\n🔍 PARALLEL SCHEDULING DETAILS")
    print("-" * 50)

    parallel_found = False
    for day in days:
        for time in times:
            sessions = schedule_grid[day].get(time, [])
            if len(sessions) > 1:
                parallel_found = True
                print(f"\n⏰ {day} at {time} - {len(sessions)} courses in parallel:")

                for i, session in enumerate(sessions, 1):
                    course = system.courses[session.course_id]
                    instructor = system.instructors[session.instructor_id]
                    group = system.groups[session.group_id]
                    room = system.rooms[session.room_id]

                    print(
                        f"  {i}. {course.name} | {instructor.name} | {group.name} | {room.name}"
                    )

    if not parallel_found:
        print("❌ No parallel scheduling found in the current solution")
    else:
        print("\n✅ Parallel scheduling successfully implemented!")


if __name__ == "__main__":
    print("🧪 PARALLEL SCHEDULING VERIFICATION SUITE")
    print("=" * 70)

    # Test 1: Analyze parallel scheduling
    print("\n1️⃣ ANALYZING CURRENT SOLUTION")
    parallel_success = analyze_parallel_scheduling()

    # Test 2: Create time grid visualization
    print("\n2️⃣ CREATING TIME GRID VISUALIZATION")
    create_time_grid_visualization()

    # Final verdict
    print("\n🎯 FINAL VERDICT")
    print("=" * 30)

    if parallel_success:
        print("✅ PARALLEL SCHEDULING IS WORKING!")
        print("   Multiple courses can be scheduled simultaneously in different rooms")
        print("   with different instructors and groups.")
    else:
        print("❌ PARALLEL SCHEDULING NEEDS IMPROVEMENT")
        print("   System is scheduling only one course per time slot.")

    print("\n💡 Note: Each 'Session' in the output represents one course session.")
    print("   Multiple sessions can run in parallel at the same time slot.")
    print("   The session numbering is just for identification purposes.")
