"""
Repair Heuristics for Constraint Violation Restoration

This module implements deterministic repair operators that fix hard constraint
violations in GA individuals. Repairs are applied after mutation/crossover to
project invalid solutions back onto the feasible region.

Repair Strategies (Complete Set):
1. Instructor Availability: Shift sessions away from instructor unavailable times
2. Group Overlaps: Detect time conflicts for same group, reassign to free slots
3. Room Conflicts: Fix room double-bookings by shifting times or changing rooms
4. Instructor Conflicts: Fix instructor double-bookings by shifting times
5. Instructor Qualification: Reassign unqualified instructors to qualified ones
6. Room Type Mismatch: Reassign rooms to match course requirements (lab vs classroom)
7. Incomplete/Extra Sessions: Add missing or remove extra session genes

Note: Room and group availability are NOT checked because:
- Rooms are always available during operating hours
- Groups default to all operating hours (QuantumTimeSystem guarantees this)
- Schedules are only generated within operating hours

Architecture:
- Individual repairs target specific constraint types
- repair_individual() orchestrates all repairs iteratively
- Repairs preserve gene structure (course-group relationships)
- Greedy approach: First-fit slot assignment

Usage:
    from src.ga.operators.repair import repair_individual

    # After mutation
    mutate(individual)
    stats = repair_individual(individual, context, max_iterations=3)
    print(f"Fixed {stats['total_fixes']} violations")
"""

from typing import List, Dict, Set, Tuple
import random
from collections import defaultdict

from src.ga.sessiongene import SessionGene
from src.core.types import SchedulingContext
from src.encoder.quantum_time_system import QuantumTimeSystem


# ============================================================================
# 1. INSTRUCTOR AVAILABILITY REPAIR (Priority 1)
# ============================================================================


def repair_instructor_availability(
    individual: List[SessionGene], context: SchedulingContext
) -> int:
    """
    Fix instructor availability violations by shifting genes to valid time slots.

    Checks ONLY instructor availability. Room and group availability are not checked because:
    - Rooms are always available during operating hours
    - Groups default to all operating hours (implicit in QuantumTimeSystem)
    - Schedules are only generated within operating hours

    For each gene:
    1. Check if instructor is available at all current quanta
    2. If ANY quantum violates instructor availability, find new time slot
    3. Shift gene to new slot that respects instructor availability

    Args:
        individual: List of SessionGene objects (GA chromosome)
        context: Scheduling context with entities and available quanta

    Returns:
        Number of genes repaired

    Note:
        Full-time instructors have full operating hours availability.
        Part-time instructors may have restricted availability.
    """
    fixes = 0

    for gene in individual:
        # Get instructor object
        instructor = context.instructors.get(gene.instructor_id)

        if not instructor:
            continue  # Skip invalid genes

        # Check if current quanta violate instructor availability
        needs_repair = False
        for q in gene.quanta:
            if q not in instructor.available_quanta:
                needs_repair = True
                break

        if not needs_repair:
            continue

        # Find valid replacement quanta (only checking instructor availability)
        required_duration = len(gene.quanta)
        new_quanta = _find_instructor_available_slot(
            individual,
            gene,
            required_duration,
            instructor,
            context.available_quanta,
        )

        if new_quanta:
            gene.quanta = new_quanta
            fixes += 1

    return fixes


def _find_instructor_available_slot(
    individual: List[SessionGene],
    current_gene: SessionGene,
    duration: int,
    instructor,
    available_quanta: List[int],
) -> List[int]:
    """
    Find a valid time slot where instructor is available and no conflicts exist.

    Only checks:
    - Instructor availability (primary check)
    - No conflicts with other genes (group/room/instructor overlaps)

    Does NOT check room or group availability (not needed - see module docstring).

    Args:
        individual: Full chromosome (to check for conflicts)
        current_gene: Gene being repaired
        duration: Required number of consecutive quanta
        instructor: Instructor entity
        available_quanta: List of all operating quanta

    Returns:
        List of quanta if valid slot found, None otherwise
    """
    # Build conflict map from other genes
    occupied = _build_occupied_quanta_map(individual, current_gene)

    # Get room and group IDs from current gene
    room_id = current_gene.room_id
    group_ids = current_gene.group_ids

    # Try to find consecutive available quanta
    for start_q in available_quanta:
        candidate_quanta = list(range(start_q, start_q + duration))

        # Check if all quanta in range are valid operating times
        if not all(q in available_quanta for q in candidate_quanta):
            continue

        # Check instructor availability (PRIMARY CHECK)
        if not all(q in instructor.available_quanta for q in candidate_quanta):
            continue

        # Check no conflicts with other genes
        conflict_free = True
        for q in candidate_quanta:
            # Instructor conflict check
            if instructor.instructor_id in occupied["instructors"].get(q, set()):
                conflict_free = False
                break

            # Room conflict check
            if room_id in occupied["rooms"].get(q, set()):
                conflict_free = False
                break

            # Group conflict check
            for group_id in group_ids:
                if group_id in occupied["groups"].get(q, set()):
                    conflict_free = False
                    break

            if not conflict_free:
                break

        if conflict_free:
            return candidate_quanta

    return None  # No valid slot found


# ============================================================================
# Helper Functions
# ============================================================================


def _find_available_slot_smart(
    individual: List[SessionGene],
    current_gene: SessionGene,
    duration: int,
    course,
    instructor,
    room,
    groups: List,
    available_quanta: List[int],
    context: SchedulingContext,
    prefer_clustering: bool = True,
) -> Tuple[List[int], str, str]:
    """
    SMART slot finder that considers alternative qualified instructors and clustering.

    Enhanced strategy:
    1. Check course subject to find ALL qualified instructors
    2. For each qualified instructor, find available slots
    3. Prioritize slots that maintain/improve clustering (adjacent to existing sessions)
    4. Return best slot + potentially better instructor + potentially better room

    Args:
        individual: Full chromosome
        current_gene: Gene being repaired
        duration: Required consecutive quanta
        course: Course entity
        instructor: Current instructor
        room: Current room
        groups: List of Group entities
        available_quanta: All operating quanta
        context: Scheduling context
        prefer_clustering: If True, prefer slots adjacent to existing sessions

    Returns:
        Tuple of (quanta_list, instructor_id, room_id) or (None, None, None)
    """
    from config.time_config import quantum_to_day_and_within_day

    qts = QuantumTimeSystem()

    # Build conflict map
    occupied = _build_occupied_quanta_map(individual, current_gene)

    # Get all qualified instructors for this course
    course_key = (course.course_id, course.course_type)
    qualified_instructors = []

    for inst_id, inst in context.instructors.items():
        if hasattr(inst, "qualifications") and inst.qualifications:
            if course.subject in inst.qualifications:
                qualified_instructors.append(inst)

    # If no qualified instructors found, use current instructor
    if not qualified_instructors:
        qualified_instructors = [instructor]

    # Get existing sessions for this course-group to understand current clustering
    existing_sessions = []
    for gene in individual:
        if gene is current_gene:
            continue
        if (gene.course_id, gene.course_type) == course_key:
            # Check if same groups
            if any(gid in gene.group_ids for gid in current_gene.group_ids):
                existing_sessions.extend(gene.quanta)

    # Try each qualified instructor
    best_slot = None
    best_instructor = None
    best_room = None
    best_score = -1

    for inst in qualified_instructors:
        # Try to find slots with this instructor
        for start_q in available_quanta:
            candidate_quanta = list(range(start_q, start_q + duration))

            # Validate candidate
            if not _validate_candidate_slot(
                candidate_quanta, available_quanta, inst, room, groups, occupied
            ):
                continue

            # Score this slot based on clustering
            score = 0
            if prefer_clustering and existing_sessions:
                score = _score_clustering(candidate_quanta, existing_sessions, qts)

            if score > best_score:
                best_score = score
                best_slot = candidate_quanta
                best_instructor = inst.instructor_id
                best_room = room.room_id

    return (best_slot, best_instructor, best_room) if best_slot else (None, None, None)


def _validate_candidate_slot(
    candidate_quanta: List[int],
    available_quanta: List[int],
    instructor,
    room,
    groups: List,
    occupied: Dict,
) -> bool:
    """Validate that a candidate slot is free from conflicts."""
    # Check if all quanta are valid operating times
    if not all(q in available_quanta for q in candidate_quanta):
        return False

    # Check instructor availability
    if not all(q in instructor.available_quanta for q in candidate_quanta):
        return False

    # Check room availability
    if not all(q in room.available_quanta for q in candidate_quanta):
        return False

    # Check all groups' availability
    for group in groups:
        if not all(q in group.available_quanta for q in candidate_quanta):
            return False

    # Check no conflicts with other genes
    for q in candidate_quanta:
        # Instructor conflict
        if instructor.instructor_id in occupied["instructors"].get(q, set()):
            return False
        # Room conflict
        if room.room_id in occupied["rooms"].get(q, set()):
            return False
        # Group conflicts
        for group in groups:
            if group.group_id in occupied["groups"].get(q, set()):
                return False

    return True


def _score_clustering(
    candidate_quanta: List[int],
    existing_sessions: List[int],
    qts: QuantumTimeSystem,
) -> int:
    """
    Score how well candidate quanta cluster with existing sessions.

    Higher score = better clustering (adjacent or same day).

    Returns:
        Score: 100 for adjacent, 10 for same day, 0 otherwise
    """
    from config.time_config import quantum_to_day_and_within_day

    if not existing_sessions:
        return 0

    max_score = 0

    for cand_q in candidate_quanta:
        cand_day, cand_within = quantum_to_day_and_within_day(cand_q, qts)

        for exist_q in existing_sessions:
            exist_day, exist_within = quantum_to_day_and_within_day(exist_q, qts)

            # Adjacent quantum (best)
            if cand_day == exist_day and abs(cand_within - exist_within) == 1:
                max_score = max(max_score, 100)
            # Same day (good)
            elif cand_day == exist_day:
                max_score = max(max_score, 10)

    return max_score


def _find_available_slot(
    individual: List[SessionGene],
    current_gene: SessionGene,
    duration: int,
    instructor,
    room,
    groups: List,
    available_quanta: List[int],
) -> List[int]:
    """
    Find a valid time slot where instructor, room, and all groups are available.

    Uses first-fit strategy: scan available quanta sequentially for valid slot.

    Args:
        individual: Full chromosome (to check for conflicts)
        current_gene: Gene being repaired
        duration: Required number of consecutive quanta
        instructor: Instructor entity
        room: Room entity
        groups: List of Group entities
        available_quanta: List of all operating quanta

    Returns:
        List of quanta if valid slot found, None otherwise
    """
    # Build conflict map from other genes
    occupied = _build_occupied_quanta_map(individual, current_gene)

    # Try to find consecutive available quanta
    for start_q in available_quanta:
        candidate_quanta = list(range(start_q, start_q + duration))

        # Check if all quanta in range are valid
        if not all(q in available_quanta for q in candidate_quanta):
            continue

        # Check instructor availability
        if not all(q in instructor.available_quanta for q in candidate_quanta):
            continue

        # Check room availability
        if not all(q in room.available_quanta for q in candidate_quanta):
            continue

        # Check all groups' availability
        all_groups_available = True
        for group in groups:
            if not all(q in group.available_quanta for q in candidate_quanta):
                all_groups_available = False
                break

        if not all_groups_available:
            continue

        # Check no conflicts with other genes (group/room overlap)
        conflict_free = True
        for q in candidate_quanta:
            # Room conflict check
            if room.room_id in occupied["rooms"].get(q, set()):
                conflict_free = False
                break

            # Group conflict check
            for group in groups:
                if group.group_id in occupied["groups"].get(q, set()):
                    conflict_free = False
                    break

            if not conflict_free:
                break

        if conflict_free:
            return candidate_quanta

    return None  # No valid slot found


# ============================================================================
# 2. GROUP OVERLAP REPAIRS (Priority 2: ~58 violations)
# ============================================================================


def repair_group_overlaps(
    individual: List[SessionGene], context: SchedulingContext
) -> int:
    """
    Detect overlapping sessions for same group, shift conflicting genes.

    Builds a group-to-quanta mapping, detects overlaps, then reassigns
    conflicting sessions to free time slots.

    Args:
        individual: List of SessionGene objects
        context: Scheduling context

    Returns:
        Number of conflicts resolved

    Note:
        For multi-group sessions, checks all assigned groups.
        Priority given to genes earlier in chromosome (assumes better fitness).
    """
    fixes = 0

    # Build group occupation map: {group_id: {quantum: gene}}
    group_schedule = defaultdict(lambda: defaultdict(list))

    for gene in individual:
        for group_id in gene.group_ids:
            for q in gene.quanta:
                group_schedule[group_id][q].append(gene)

    # Detect overlaps and repair
    for group_id, quanta_map in group_schedule.items():
        for quantum, genes in quanta_map.items():
            if len(genes) > 1:
                # Overlap detected - keep first gene, repair others
                for gene in genes[1:]:
                    # Try to find new slot for conflicting gene
                    course_key = (gene.course_id, gene.course_type)
                    course = context.courses.get(course_key)
                    instructor = context.instructors.get(gene.instructor_id)
                    room = context.rooms.get(gene.room_id)
                    groups = [context.groups.get(gid) for gid in gene.group_ids]

                    if not all([course, instructor, room] + groups):
                        continue

                    required_duration = len(gene.quanta)

                    # Use SMART slot finder (considers alternative instructors + clustering)
                    new_quanta, new_instructor, new_room = _find_available_slot_smart(
                        individual,
                        gene,
                        required_duration,
                        course,
                        instructor,
                        room,
                        groups,
                        context.available_quanta,
                        context,
                        prefer_clustering=True,
                    )

                    if new_quanta:
                        gene.quanta = new_quanta
                        if new_instructor and new_instructor != gene.instructor_id:
                            gene.instructor_id = new_instructor
                        if new_room and new_room != gene.room_id:
                            gene.room_id = new_room
                        fixes += 1

    return fixes


# ============================================================================
# 3. ROOM CONFLICT REPAIRS (Priority 3: ~35 violations)
# ============================================================================


def repair_room_conflicts(
    individual: List[SessionGene], context: SchedulingContext
) -> int:
    """
    Fix room double-bookings by reassigning rooms or shifting times.

    Strategy:
    1. Build room occupation map
    2. Detect double-bookings
    3. Try shifting time first (preserve room preference)
    4. If no valid time, try alternative room with same features
    5. If no alternative, shift time to any valid slot

    Args:
        individual: List of SessionGene objects
        context: Scheduling context

    Returns:
        Number of conflicts resolved
    """
    fixes = 0

    # Build room occupation map: {room_id: {quantum: gene}}
    room_schedule = defaultdict(lambda: defaultdict(list))

    for gene in individual:
        for q in gene.quanta:
            room_schedule[gene.room_id][q].append(gene)

    # Detect overlaps and repair
    for room_id, quanta_map in room_schedule.items():
        for quantum, genes in quanta_map.items():
            if len(genes) > 1:
                # Double-booking detected - keep first gene, repair others
                for gene in genes[1:]:
                    course_key = (gene.course_id, gene.course_type)
                    course = context.courses.get(course_key)
                    instructor = context.instructors.get(gene.instructor_id)
                    current_room = context.rooms.get(gene.room_id)
                    groups = [context.groups.get(gid) for gid in gene.group_ids]

                    if not all([course, instructor, current_room] + groups):
                        continue

                    # Strategy 1: Try shifting time with same room
                    required_duration = len(gene.quanta)
                    new_quanta = _find_available_slot(
                        individual,
                        gene,
                        required_duration,
                        instructor,
                        current_room,
                        groups,
                        context.available_quanta,
                    )

                    if new_quanta:
                        gene.quanta = new_quanta
                        fixes += 1
                        continue

                    # Strategy 2: Try alternative room at same time
                    alternative_room = _find_alternative_room(
                        individual,
                        gene,
                        course,
                        current_room,
                        context.rooms,
                        gene.quanta,
                    )

                    if alternative_room:
                        gene.room_id = alternative_room.room_id
                        fixes += 1
                        continue

                    # Strategy 3: Try any room at any time (last resort)
                    for room in context.rooms.values():
                        if _room_matches_requirements(room, course):
                            new_quanta = _find_available_slot(
                                individual,
                                gene,
                                required_duration,
                                instructor,
                                room,
                                groups,
                                context.available_quanta,
                            )

                            if new_quanta:
                                gene.room_id = room.room_id
                                gene.quanta = new_quanta
                                fixes += 1
                                break

    return fixes


def _find_alternative_room(
    individual: List[SessionGene],
    gene: SessionGene,
    course,
    current_room,
    all_rooms: Dict,
    desired_quanta: List[int],
) -> object:
    """
    Find alternative room with same features, available at desired time.

    Args:
        individual: Full chromosome
        gene: Gene needing room reassignment
        course: Course entity
        current_room: Current (conflicting) room
        all_rooms: Dictionary of all available rooms
        desired_quanta: Desired time slots

    Returns:
        Room object if suitable alternative found, None otherwise
    """
    occupied = _build_occupied_quanta_map(individual, gene)

    for room in all_rooms.values():
        if room.room_id == current_room.room_id:
            continue  # Skip current room

        # Check if room matches course requirements
        if not _room_matches_requirements(room, course):
            continue

        # Check if room is available at desired quanta
        if not all(q in room.available_quanta for q in desired_quanta):
            continue

        # Check no conflicts with other genes
        conflict_free = True
        for q in desired_quanta:
            if room.room_id in occupied["rooms"].get(q, set()):
                conflict_free = False
                break

        if conflict_free:
            return room

    return None


def _room_matches_requirements(room, course) -> bool:
    """
    Check if room satisfies course requirements (type and capacity).

    Uses intelligent matching:
    1. Exact match: room.room_features == course.required_room_features
    2. Flexible match: Room.is_suitable_for_course_type() compatibility
    3. Fallback compatibility rules for common types

    Args:
        room: Room entity
        course: Course entity

    Returns:
        True if room is suitable, False otherwise
    """
    # Get normalized feature strings
    required = getattr(course, "required_room_features", "classroom")
    room_feature = getattr(room, "room_features", "classroom")

    # Normalize to lowercase strings
    required_str = (
        (required if isinstance(required, str) else str(required)).lower().strip()
    )
    room_str = (
        (room_feature if isinstance(room_feature, str) else str(room_feature))
        .lower()
        .strip()
    )

    # PRIORITY 1: Exact match
    if room_str == required_str:
        return True

    # PRIORITY 2: Use Room's built-in flexible matching
    if hasattr(room, "is_suitable_for_course_type"):
        if room.is_suitable_for_course_type(required_str):
            return True

    # PRIORITY 3: Additional fallback compatibility rules
    # Lab courses: Accept any lab variant
    if required_str in ["lab", "laboratory"]:
        if any(lab_type in room_str for lab_type in ["lab", "computer", "science"]):
            return True

    # Classroom/lecture courses: Accept classroom, lecture hall, auditorium, seminar
    if required_str in ["classroom", "lecture", "theory"]:
        if room_str in [
            "classroom",
            "lecture",
            "auditorium",
            "seminar",
            "lecture_hall",
        ]:
            return True

    # Practical courses without specific requirements
    if course.course_type == "practical":
        if any(lab_type in room_str for lab_type in ["lab", "practical", "workshop"]):
            return True

    # Theory courses without specific requirements
    if course.course_type == "theory":
        if room_str in ["classroom", "lecture", "auditorium", "seminar", "tutorial"]:
            return True

    return False


# ============================================================================
# 4. INSTRUCTOR CONFLICT REPAIRS (Priority 4)
# ============================================================================


def repair_instructor_conflicts(
    individual: List[SessionGene], context: SchedulingContext
) -> int:
    """
    Fix instructor double-bookings by shifting conflicting sessions to free time slots.

    Similar to group overlap repair, but for instructors.

    Args:
        individual: List of SessionGene objects
        context: Scheduling context

    Returns:
        Number of conflicts resolved
    """
    fixes = 0

    # Build instructor occupation map: {instructor_id: {quantum: gene}}
    instructor_schedule = defaultdict(lambda: defaultdict(list))

    for gene in individual:
        for q in gene.quanta:
            instructor_schedule[gene.instructor_id][q].append(gene)

    # Detect overlaps and repair
    for instructor_id, quanta_map in instructor_schedule.items():
        for quantum, genes in quanta_map.items():
            if len(genes) > 1:
                # Overlap detected - keep first gene, repair others
                for gene in genes[1:]:
                    course_key = (gene.course_id, gene.course_type)
                    course = context.courses.get(course_key)
                    instructor = context.instructors.get(gene.instructor_id)
                    room = context.rooms.get(gene.room_id)
                    groups = [context.groups.get(gid) for gid in gene.group_ids]

                    if not all([course, instructor, room] + groups):
                        continue

                    required_duration = len(gene.quanta)

                    # Use SMART slot finder (considers alternative instructors + clustering)
                    new_quanta, new_instructor, new_room = _find_available_slot_smart(
                        individual,
                        gene,
                        required_duration,
                        course,
                        instructor,
                        room,
                        groups,
                        context.available_quanta,
                        context,
                        prefer_clustering=True,
                    )

                    if new_quanta:
                        gene.quanta = new_quanta
                        if new_instructor and new_instructor != gene.instructor_id:
                            gene.instructor_id = new_instructor
                        if new_room and new_room != gene.room_id:
                            gene.room_id = new_room
                        fixes += 1

    return fixes


# ============================================================================
# 5. INSTRUCTOR QUALIFICATION REPAIRS (Priority 5)
# ============================================================================


def repair_instructor_qualifications(
    individual: List[SessionGene], context: SchedulingContext
) -> int:
    """
    Fix instructor qualification mismatches by reassigning qualified instructors.

    For each gene with unqualified instructor:
    1. Find list of qualified instructors for that course
    2. Check which qualified instructors are available at gene's time
    3. Reassign to first available qualified instructor

    Args:
        individual: List of SessionGene objects
        context: Scheduling context

    Returns:
        Number of genes repaired

    Note:
        If no qualified instructor available, gene remains unchanged (data limitation).
    """
    fixes = 0

    for gene in individual:
        course_key = (gene.course_id, gene.course_type)
        course = context.courses.get(course_key)
        current_instructor = context.instructors.get(gene.instructor_id)

        if not course or not current_instructor:
            continue

        # Check if current instructor is qualified
        if current_instructor.instructor_id in course.qualified_instructor_ids:
            continue  # Already qualified, no repair needed

        # Find qualified instructors
        qualified_ids = course.qualified_instructor_ids
        if not qualified_ids:
            continue  # No qualified instructors available (data limitation)

        # Find qualified instructor available at this time
        for qualified_id in qualified_ids:
            qualified_instructor = context.instructors.get(qualified_id)
            if not qualified_instructor:
                continue

            # Check if qualified instructor is available at all gene quanta
            if all(q in qualified_instructor.available_quanta for q in gene.quanta):
                # Check no conflict with other genes
                occupied = _build_occupied_quanta_map(individual, gene)
                conflict_free = True

                for q in gene.quanta:
                    if qualified_id in occupied["instructors"].get(q, set()):
                        conflict_free = False
                        break

                if conflict_free:
                    # Reassign to qualified instructor
                    gene.instructor_id = qualified_id
                    fixes += 1
                    break

    return fixes


# ============================================================================
# 6. ROOM TYPE MISMATCH REPAIRS (Priority 6)
# ============================================================================


def repair_room_type_mismatches(
    individual: List[SessionGene], context: SchedulingContext
) -> int:
    """
    Fix room type mismatches by reassigning rooms to match course requirements.

    Enhanced strategy:
    1. Try to find suitable room at current time (prioritized: exact > flexible > any)
    2. If no suitable room at current time, try time-shifting to slots with suitable rooms
    3. Fallback: Keep current room if no better alternative exists

    This ensures repair attempts are comprehensive before giving up.

    Args:
        individual: List of SessionGene objects
        context: Scheduling context

    Returns:
        Number of genes repaired
    """
    fixes = 0

    for gene in individual:
        course_key = (gene.course_id, gene.course_type)
        course = context.courses.get(course_key)
        current_room = context.rooms.get(gene.room_id)

        if not course or not current_room:
            continue

        # Check if current room matches requirements
        if _room_matches_requirements(current_room, course):
            continue  # Already correct type

        # Strategy 1: Find suitable room at current time
        suitable_room = _find_suitable_room_for_gene(individual, gene, course, context)

        if suitable_room:
            gene.room_id = suitable_room.room_id
            fixes += 1
            continue

        # Strategy 2: Try time-shifting to find slots with suitable rooms
        # Only attempt if we couldn't find a suitable room at current time
        shifted = _try_time_shift_for_better_room(individual, gene, course, context)

        if shifted:
            fixes += 1
            # Note: gene.room_id and gene.quanta are modified by _try_time_shift_for_better_room

    return fixes


def _find_suitable_room_for_gene(
    individual: List[SessionGene], gene: SessionGene, course, context: SchedulingContext
) -> object:
    """
    Find a room that matches course requirements and is available at gene's time.

    Enhanced with prioritized search:
    1. Exact match rooms (highest priority)
    2. Flexible match rooms (medium priority)
    3. Any available room with capacity (lowest priority - fallback)

    Args:
        individual: Full chromosome
        gene: Gene needing room reassignment
        course: Course entity
        context: Scheduling context

    Returns:
        Room object if suitable room found, None otherwise
    """
    occupied = _build_occupied_quanta_map(individual, gene)

    # Get required features and enrolled group sizes for capacity check
    required_features = getattr(course, "required_room_features", "classroom")
    required_str = (
        (
            required_features
            if isinstance(required_features, str)
            else str(required_features)
        )
        .lower()
        .strip()
    )

    # Calculate minimum capacity needed
    min_capacity = 30  # default
    for group_id in gene.group_ids:
        group = context.groups.get(group_id)
        if group:
            group_size = getattr(group, "student_count", 30)
            min_capacity = max(min_capacity, group_size)

    # Categorize rooms by match quality
    exact_match_rooms = []
    flexible_match_rooms = []
    fallback_rooms = []

    for room in context.rooms.values():
        # Skip current room
        if room.room_id == gene.room_id:
            continue

        # Check capacity (hard constraint)
        room_capacity = getattr(room, "capacity", 50)
        if room_capacity < min_capacity:
            continue

        # Check if room is available at all gene quanta
        if not all(q in room.available_quanta for q in gene.quanta):
            continue

        # Check no conflicts with other genes
        conflict_free = True
        for q in gene.quanta:
            if room.room_id in occupied["rooms"].get(q, set()):
                conflict_free = False
                break

        if not conflict_free:
            continue

        # Categorize by match quality
        room_str = getattr(room, "room_features", "classroom")
        room_str_normalized = (
            (room_str if isinstance(room_str, str) else str(room_str)).lower().strip()
        )

        # Exact match
        if room_str_normalized == required_str:
            exact_match_rooms.append(room)
        # Flexible match
        elif _room_matches_requirements(room, course):
            flexible_match_rooms.append(room)
        # Fallback (any available room with capacity)
        else:
            fallback_rooms.append(room)

    # Return best available room (prioritized)
    if exact_match_rooms:
        return exact_match_rooms[0]
    if flexible_match_rooms:
        return flexible_match_rooms[0]
    if fallback_rooms:
        return fallback_rooms[0]

    return None


def _try_time_shift_for_better_room(
    individual: List[SessionGene], gene: SessionGene, course, context: SchedulingContext
) -> bool:
    """
    Attempt to shift gene's time to a slot where suitable rooms are available.

    This is a last-resort strategy when no suitable room exists at current time.

    Args:
        individual: Full chromosome
        gene: Gene needing both time and room reassignment
        course: Course entity
        context: Scheduling context

    Returns:
        True if successfully shifted time and assigned suitable room, False otherwise
    """
    occupied = _build_occupied_quanta_map(individual, gene)
    required_duration = len(gene.quanta)

    # Get required features
    required_features = getattr(course, "required_room_features", "classroom")

    # Calculate minimum capacity
    min_capacity = 30
    for group_id in gene.group_ids:
        group = context.groups.get(group_id)
        if group:
            group_size = getattr(group, "student_count", 30)
            min_capacity = max(min_capacity, group_size)

    # Find suitable rooms (don't worry about time conflicts yet)
    suitable_rooms = [
        room
        for room in context.rooms.values()
        if _room_matches_requirements(room, course)
        and getattr(room, "capacity", 50) >= min_capacity
    ]

    if not suitable_rooms:
        return False  # No suitable rooms exist at all

    # Try to find time slots where these suitable rooms are available
    instructor = context.instructors.get(gene.instructor_id)
    groups = [context.groups.get(gid) for gid in gene.group_ids]

    if not instructor or not all(groups):
        return False

    # Try different time slots
    available_quanta_list = sorted(context.available_quanta)

    for start_idx in range(len(available_quanta_list) - required_duration + 1):
        candidate_quanta = available_quanta_list[
            start_idx : start_idx + required_duration
        ]

        # Check if instructor is available
        if not all(q in instructor.available_quanta for q in candidate_quanta):
            continue

        # Check if all groups are available
        groups_available = True
        for group in groups:
            if not all(q in group.available_quanta for q in candidate_quanta):
                groups_available = False
                break

        if not groups_available:
            continue

        # Check for conflicts with other genes
        has_conflict = False
        for q in candidate_quanta:
            # Check instructor conflicts
            if gene.instructor_id in occupied["instructors"].get(q, set()):
                has_conflict = True
                break
            # Check group conflicts
            for group_id in gene.group_ids:
                if group_id in occupied["groups"].get(q, set()):
                    has_conflict = True
                    break
            if has_conflict:
                break

        if has_conflict:
            continue

        # Try to find a suitable room available at this time
        for room in suitable_rooms:
            if not all(q in room.available_quanta for q in candidate_quanta):
                continue

            # Check room conflicts
            room_conflict = False
            for q in candidate_quanta:
                if room.room_id in occupied["rooms"].get(q, set()):
                    room_conflict = True
                    break

            if not room_conflict:
                # Success! Update gene with new time and room
                gene.quanta = candidate_quanta
                gene.room_id = room.room_id
                return True

    return False  # Could not find suitable time-room combination


# ============================================================================
# 7. SESSION BLOCK CLUSTERING REPAIR (Priority 7 - Soft Constraint)
# ============================================================================


def repair_session_clustering(
    individual: List[SessionGene], context: SchedulingContext
) -> int:
    """
    Improve session block clustering by REARRANGING quanta to form 2-3 quantum blocks.

    CRITICAL: This repair ONLY rearranges existing quanta - it NEVER adds or removes quanta.
    This preserves the population invariant that each course-group pair has exactly the
    required number of quanta.

    Strategy:
    1. For each gene with multiple isolated 1-quantum sessions:
       - Try to move isolated quanta to adjacent free slots to form blocks
       - Only rearrange within the same gene (same course-group-instructor-room)
    2. Never change the total quanta count per gene

    Args:
        individual: List of SessionGene objects to repair
        context: Scheduling context with courses, groups, instructors, rooms

    Returns:
        Number of clustering improvements made
    """
    from config.time_config import quantum_to_day_and_within_day

    qts = QuantumTimeSystem()
    fixes = 0

    # Process each gene individually
    for gene in individual:
        if len(gene.quanta) < 2:
            # Can't cluster single-quantum courses
            continue

        # Analyze blocks in this gene
        day_quanta_map = defaultdict(
            list
        )  # day -> list of (within_day, global_quantum)

        for q in gene.quanta:
            day, within_day = quantum_to_day_and_within_day(q, qts)
            day_quanta_map[day].append((within_day, q))

        # Find isolated 1-quantum blocks on each day
        for day, quanta_pairs in day_quanta_map.items():
            if len(quanta_pairs) < 2:
                continue

            sorted_pairs = sorted(quanta_pairs, key=lambda x: x[0])
            within_day_quanta = [w for w, _ in sorted_pairs]
            global_quanta = [g for _, g in sorted_pairs]

            # Identify blocks
            blocks = []
            current_block = [0]  # indices into sorted_pairs

            for i in range(1, len(within_day_quanta)):
                if within_day_quanta[i] == within_day_quanta[i - 1] + 1:
                    current_block.append(i)
                else:
                    blocks.append(current_block)
                    current_block = [i]
            blocks.append(current_block)

            # Try to rearrange isolated blocks
            for block_indices in blocks:
                if len(block_indices) == 1:  # Isolated 1-quantum block
                    isolated_idx = block_indices[0]
                    isolated_within = within_day_quanta[isolated_idx]
                    isolated_global = global_quanta[isolated_idx]

                    # Try to move this quantum to adjacent position of another block
                    success = _try_rearrange_isolated_quantum(
                        gene,
                        isolated_global,
                        isolated_within,
                        day,
                        within_day_quanta,
                        global_quanta,
                        isolated_idx,
                        individual,
                        context,
                        qts,
                    )

                    if success:
                        fixes += 1
                        break  # Re-analyze after modification

    return fixes


def _try_rearrange_isolated_quantum(
    gene: SessionGene,
    isolated_global: int,
    isolated_within: int,
    day: str,
    all_within_day: List[int],
    all_global: List[int],
    isolated_idx: int,
    individual: List[SessionGene],
    context: SchedulingContext,
    qts: QuantumTimeSystem,
) -> bool:
    """
    Try to rearrange an isolated quantum to form a better block WITHOUT changing total quanta.

    Strategy: Move the isolated quantum to a position adjacent to an existing block
    on the same day, if that position is free.

    CRITICAL: This only MOVES quanta, never adds or removes them.

    Args:
        gene: The gene containing the isolated quantum
        isolated_global: Global quantum index of isolated session
        isolated_within: Within-day quantum index
        day: Day name where isolated quantum exists
        all_within_day: All within-day quanta for this gene on this day
        all_global: All global quanta for this gene on this day
        isolated_idx: Index of isolated quantum in the sorted lists
        individual: Full individual to check conflicts
        context: Scheduling context
        qts: QuantumTimeSystem instance

    Returns:
        True if successfully rearranged, False otherwise
    """
    day_offset = qts.day_quanta_offset[day]

    # Find positions adjacent to existing blocks that would form a better cluster
    target_positions = []

    # Look for existing blocks to attach to
    for i, within in enumerate(all_within_day):
        if i == isolated_idx:
            continue

        # Check if adjacent positions are free
        for adj_offset in [-1, +1]:
            adj_within = within + adj_offset

            if adj_within < 0 or adj_within >= qts.day_quanta_count[day]:
                continue

            # Skip if this position is already occupied by this gene
            if adj_within in all_within_day:
                continue

            adj_global = day_offset + adj_within

            # Check if this position is free (no conflicts with other genes)
            if _is_quantum_free_for_gene(adj_global, gene, individual, context):
                target_positions.append(adj_global)

    if not target_positions:
        return False

    # Move isolated quantum to the first available target position
    target_global = target_positions[0]

    # Simply replace the isolated quantum with the target quantum
    new_quanta = list(gene.quanta)
    new_quanta.remove(isolated_global)
    new_quanta.append(target_global)

    gene.quanta = sorted(new_quanta)
    return True


def _is_quantum_free_for_gene(
    quantum: int,
    gene: SessionGene,
    individual: List[SessionGene],
    context: SchedulingContext,
) -> bool:
    """
    Check if a quantum is free for all resources needed by a gene.

    Checks:
    - No group conflicts
    - No instructor conflicts
    - No room conflicts
    - Instructor availability

    Args:
        quantum: Global quantum index to check
        gene: Gene that wants to use this quantum
        individual: Full individual to check conflicts
        context: Scheduling context

    Returns:
        True if quantum is free for all gene's resources
    """
    instructor = context.instructors.get(gene.instructor_id)

    # Check instructor availability
    if instructor and hasattr(instructor, "available_quanta"):
        if quantum not in instructor.available_quanta:
            return False

    # Check for conflicts with other genes
    for other_gene in individual:
        if other_gene is gene:
            continue

        if quantum not in other_gene.quanta:
            continue

        # Check group overlap
        if any(gid in other_gene.group_ids for gid in gene.group_ids):
            return False

        # Check instructor conflict
        if other_gene.instructor_id == gene.instructor_id:
            return False

        # Check room conflict
        if other_gene.room_id == gene.room_id:
            return False

    return True


# ============================================================================
# 8. INCOMPLETE/EXTRA SESSIONS REPAIRS (Priority 8 - Complex)
# ============================================================================


def repair_incomplete_or_extra_sessions(
    individual: List[SessionGene], context: SchedulingContext
) -> int:
    """
    Fix incomplete or over-scheduled courses by adding/removing genes.

    Strategy:
    1. Count quanta per (course, type, group) combination
    2. If under-scheduled: Create new gene for missing quanta
    3. If over-scheduled: Remove genes until correct quanta count

    Args:
        individual: List of SessionGene objects (modified in-place)
        context: Scheduling context

    Returns:
        Number of genes added/removed

    Note:
        This is the most complex repair as it modifies individual length.
        Use with caution - may destabilize population structure.
    """
    fixes = 0

    # Count quanta per (course_code, course_type, group_id)
    course_group_quanta = defaultdict(int)
    course_group_genes = defaultdict(list)

    for gene in individual:
        for group_id in gene.group_ids:
            key = ((gene.course_id, gene.course_type), group_id)
            course_group_quanta[key] += len(gene.quanta)
            course_group_genes[key].append(gene)

    # Check each course's enrolled groups
    for course_key, course in context.courses.items():
        expected_quanta = course.quanta_per_week
        enrolled_groups = course.enrolled_group_ids

        for group_id in enrolled_groups:
            key = (course_key, group_id)
            actual_quanta = course_group_quanta.get(key, 0)

            if actual_quanta == expected_quanta:
                continue  # Correctly scheduled

            elif actual_quanta > expected_quanta:
                # Over-scheduled: Remove excess genes
                excess = actual_quanta - expected_quanta
                genes_for_this = course_group_genes.get(key, [])

                # Remove genes until we reach expected quanta (remove smallest first)
                genes_for_this.sort(key=lambda g: len(g.quanta))

                for gene in genes_for_this:
                    if excess <= 0:
                        break
                    if gene in individual:
                        individual.remove(gene)
                        excess -= len(gene.quanta)
                        fixes += 1

            elif actual_quanta < expected_quanta:
                # Under-scheduled: Add missing gene
                missing = expected_quanta - actual_quanta

                # Create new gene for missing quanta (if possible)
                new_gene = _create_session_gene_for_course_group(
                    course_key, group_id, missing, context, individual
                )

                if new_gene:
                    individual.append(new_gene)
                    fixes += 1

    return fixes


def _create_session_gene_for_course_group(
    course_key: Tuple[str, str],
    group_id: str,
    required_quanta: int,
    context: SchedulingContext,
    existing_individual: List[SessionGene],
) -> SessionGene:
    """
    Create a new SessionGene for a missing course-group combination.

    Args:
        course_key: (course_id, course_type) tuple
        group_id: Group ID
        required_quanta: Number of quanta needed
        context: Scheduling context
        existing_individual: Current individual (to avoid conflicts)

    Returns:
        SessionGene if successfully created, None otherwise
    """
    course = context.courses.get(course_key)
    group = context.groups.get(group_id)

    if not course or not group:
        return None

    # Find qualified instructor
    qualified_ids = course.qualified_instructor_ids
    if not qualified_ids:
        qualified_ids = list(context.instructors.keys())  # Fallback

    # Find suitable room
    suitable_rooms = [
        r for r in context.rooms.values() if _room_matches_requirements(r, course)
    ]
    if not suitable_rooms:
        suitable_rooms = list(context.rooms.values())  # Fallback

    # Try to find valid slot
    occupied = _build_occupied_quanta_map(existing_individual)

    for instructor_id in qualified_ids:
        instructor = context.instructors.get(instructor_id)
        if not instructor:
            continue

        for room in suitable_rooms:
            # Try to find consecutive quanta
            for start_q in context.available_quanta:
                candidate_quanta = list(range(start_q, start_q + required_quanta))

                # Validate
                if not all(q in context.available_quanta for q in candidate_quanta):
                    continue

                # Check availability and conflicts
                if not all(q in instructor.available_quanta for q in candidate_quanta):
                    continue
                if not all(q in room.available_quanta for q in candidate_quanta):
                    continue
                if not all(q in group.available_quanta for q in candidate_quanta):
                    continue

                # Check no conflicts
                conflict = False
                for q in candidate_quanta:
                    if (
                        room.room_id in occupied["rooms"].get(q, set())
                        or instructor_id in occupied["instructors"].get(q, set())
                        or group_id in occupied["groups"].get(q, set())
                    ):
                        conflict = True
                        break

                if not conflict:
                    # Create gene
                    return SessionGene(
                        course_id=course_key[0],
                        course_type=course_key[1],
                        instructor_id=instructor_id,
                        group_ids=[group_id],
                        room_id=room.room_id,
                        quanta=candidate_quanta,
                    )

    return None  # Could not create valid gene


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _build_occupied_quanta_map(
    individual: List[SessionGene], exclude_gene: SessionGene = None
) -> Dict[str, Dict[int, Set[str]]]:
    """
    Build occupation map for detecting conflicts.

    Args:
        individual: Full chromosome
        exclude_gene: Gene to exclude from map (the one being repaired)

    Returns:
        {
            "groups": {quantum: {group_id, ...}},
            "rooms": {quantum: {room_id, ...}},
            "instructors": {quantum: {instructor_id, ...}}
        }
    """
    occupied = {
        "groups": defaultdict(set),
        "rooms": defaultdict(set),
        "instructors": defaultdict(set),
    }

    for gene in individual:
        if exclude_gene and gene is exclude_gene:
            continue

        for q in gene.quanta:
            occupied["rooms"][q].add(gene.room_id)
            occupied["instructors"][q].add(gene.instructor_id)
            for group_id in gene.group_ids:
                occupied["groups"][q].add(group_id)

    return occupied


# ============================================================================
# ORCHESTRATION: Apply repairs in priority order
# ============================================================================


def repair_individual(
    individual: List[SessionGene],
    context: SchedulingContext,
    max_iterations: int = 3,
) -> dict:
    """
    Apply enabled repair heuristics iteratively using registry pattern.

    Dynamically loads enabled repairs from REPAIR_HEURISTICS_CONFIG and applies
    them in priority order until no violations remain or max_iterations reached.

    Registry-based architecture allows:
    - Enable/disable individual repairs via config
    - Reorder repair priority without code changes
    - Easy experimentation and ablation studies

    Args:
        individual: GA individual (chromosome) to repair
        context: Scheduling context with entities
        max_iterations: Maximum repair passes (prevents infinite loops)

    Returns:
        Dict with repair statistics:
        {
            "iterations": int,
            "availability_violations_fixes": int,
            "group_overlaps_fixes": int,
            "room_conflicts_fixes": int,
            "instructor_conflicts_fixes": int,
            "instructor_qualifications_fixes": int,
            "room_type_mismatches_fixes": int,
            "incomplete_or_extra_sessions_fixes": int,
            "total_fixes": int
        }

    Note:
        Repairs modify individual in-place. Fitness should be invalidated after repair.
        Some repairs (e.g., incomplete_or_extra_sessions) can change individual length.

    Example:
        >>> stats = repair_individual(individual, context, max_iterations=3)
        >>> print(f"Total fixes: {stats['total_fixes']} in {stats['iterations']} iterations")
    """
    # Import registry here to avoid circular dependency issues
    from src.ga.operators.repair_registry import (
        get_enabled_repair_heuristics,
        get_repair_statistics_template,
    )

    # Initialize statistics tracking
    stats = get_repair_statistics_template()

    # Get enabled repair heuristics (sorted by priority)
    enabled_repairs = get_enabled_repair_heuristics()

    if not enabled_repairs:
        # No repairs enabled - return zero stats
        return stats

    # Iterative repair loop
    for iteration in range(max_iterations):
        stats["iterations"] += 1
        iteration_fixes = 0

        # Apply each enabled repair in priority order
        for repair_name, repair_info in enabled_repairs.items():
            repair_func = repair_info["function"]

            # Call repair function
            fixes = repair_func(individual, context)

            # Update statistics
            stat_key = repair_name.replace("repair_", "") + "_fixes"
            stats[stat_key] += fixes
            iteration_fixes += fixes

        # Check convergence
        if iteration_fixes == 0:
            break  # Converged (no more repairs possible)

    # Calculate total fixes
    stats["total_fixes"] = sum(v for k, v in stats.items() if k.endswith("_fixes"))

    return stats
