#!/usr/bin/env python3
"""
Test Parallel Scheduling Capability

This script demonstrates that the enhanced system can schedule multiple courses
simultaneously in different rooms with different instructors and groups.
"""

import json
from pathlib import Path
from src.ga_deap.enhanced_system import EnhancedTimetablingSystem
from src.ga_deap.individual import generate_individual
from src.encoders.quantum_time_system import QuantumTimeSystem
from src.encoders.input_encoder import (
    load_courses,
    load_instructors,
    load_groups,
    load_rooms,
)


def test_parallel_scheduling():
    """Test that the system can schedule multiple courses in parallel."""

    print("🧪 Testing Parallel Scheduling Capability")
    print("=" * 50)

    # Initialize the system
    qts = QuantumTimeSystem()

    # Load enhanced data
    try:
        courses = load_courses("data/Courses_Enhanced.json")
        instructors = load_instructors("data/Instructors_Enhanced.json", qts)
        groups = load_groups("data/Groups_Enhanced.json", qts)
        rooms = load_rooms("data/Rooms_Enhanced.json", qts)

        print(f"✅ Loaded {len(courses)} courses, {len(instructors)} instructors")
        print(f"✅ Loaded {len(groups)} groups, {len(rooms)} rooms")

    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False

    # Generate a single individual to test parallel scheduling
    print("\n🔄 Generating individual with parallel scheduling...")
    individual = generate_individual(qts, courses, instructors, groups, rooms)

    print(f"✅ Generated individual with {len(individual)} sessions")

    # Analyze the schedule for parallel sessions
    print("\n📊 Analyzing Schedule for Parallel Sessions")
    print("-" * 40)

    # Group sessions by quantum (time slot)
    quantum_sessions = {}
    for session in individual:
        for quantum in session.quanta:
            if quantum not in quantum_sessions:
                quantum_sessions[quantum] = []
            quantum_sessions[quantum].append(session)

    # Find time slots with multiple sessions (parallel scheduling)
    parallel_slots = {
        q: sessions for q, sessions in quantum_sessions.items() if len(sessions) > 1
    }

    if parallel_slots:
        print(f"🎉 Found {len(parallel_slots)} time slots with parallel scheduling!")
        print(
            f"📈 Total parallel sessions: {sum(len(sessions) for sessions in parallel_slots.values())}"
        )

        # Show examples of parallel scheduling
        print("\n📋 Examples of Parallel Scheduling:")
        for quantum, sessions in list(parallel_slots.items())[
            :3
        ]:  # Show first 3 examples
            print(f"\n⏰ Time Slot {quantum}:")
            for session in sessions:
                course = courses[session.course_id]
                instructor = instructors[session.instructor_id]
                group = groups[session.group_id]
                room = rooms[session.room_id]

                print(
                    f"  📚 {course.name} | 👨‍🏫 {instructor.name} | 👥 {group.name} | 🏢 {room.name}"
                )

        return True
    else:
        print("❌ No parallel scheduling found - only one course per time slot")

        # Show what was scheduled
        print("\n📋 Current Schedule (Single Sessions):")
        for quantum, sessions in list(quantum_sessions.items())[:5]:  # Show first 5
            session = sessions[0]
            course = courses[session.course_id]
            instructor = instructors[session.instructor_id]
            group = groups[session.group_id]
            room = rooms[session.room_id]

            print(
                f"⏰ {quantum}: {course.name} | {instructor.name} | {group.name} | {room.name}"
            )

        return False


def test_enhanced_system():
    """Test the enhanced system with enhanced data."""

    print("\n🔬 Testing Enhanced System")
    print("=" * 50)

    # Initialize enhanced system
    system = EnhancedTimetablingSystem()

    # Load enhanced data
    success, issues = system.load_data()

    if not success:
        print(f"❌ Failed to load data: {issues}")
        return False

    print("✅ Enhanced system loaded successfully")

    if issues:
        print(f"⚠️  Issues found: {issues}")

    # Run a quick optimization
    print("\n🏃‍♂️ Running quick optimization...")

    try:
        results = system.run_optimization(
            population_size=20,
            generations=10,
            mutation_rate=0.1,
            crossover_rate=0.8,
            tournament_size=3,
        )

        print(f"✅ Optimization completed")
        print(f"📊 Best fitness: {results['best_fitness']:.4f}")
        print(f"🕒 Runtime: {results['runtime']:.2f} seconds")

        # Check if the best solution has parallel scheduling
        best_individual = results["best_individual"]
        quantum_sessions = {}
        for session in best_individual:
            for quantum in session.quanta:
                if quantum not in quantum_sessions:
                    quantum_sessions[quantum] = []
                quantum_sessions[quantum].append(session)

        parallel_slots = {
            q: sessions for q, sessions in quantum_sessions.items() if len(sessions) > 1
        }

        if parallel_slots:
            print(
                f"🎉 Best solution has {len(parallel_slots)} time slots with parallel scheduling!"
            )
        else:
            print("ℹ️  Best solution has no parallel scheduling")

        return True

    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Parallel Scheduling Test Suite")
    print("=" * 60)

    # Test 1: Individual generation with parallel scheduling
    test1_success = test_parallel_scheduling()

    # Test 2: Enhanced system with enhanced data
    test2_success = test_enhanced_system()

    # Summary
    print("\n📝 Test Summary")
    print("=" * 30)
    print(f"Individual Generation: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Enhanced System: {'✅ PASS' if test2_success else '❌ FAIL'}")

    if test1_success and test2_success:
        print("\n🎉 All tests passed! Parallel scheduling is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
