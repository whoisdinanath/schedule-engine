import random
from src.ga.sessiongene import SessionGene
from src.core.types import SchedulingContext
from typing import List


def mutate_gene(gene: SessionGene, context: SchedulingContext) -> SessionGene:
    """
    Performs constraint-aware mutation on a single gene.

    CRITICAL: Course and Group are NEVER mutated!
    Only mutates: Instructor, Room, Time slots

    This preserves the fundamental (course, group) enrollment structure
    and prevents incomplete_or_extra_sessions violations.
    """
    # Get course info for constraint-aware mutation
    # Look up using tuple key (course_id, course_type)
    course_key = (gene.course_id, gene.course_type)
    course = context.courses.get(course_key)

    # ========================================
    # COURSE & GROUP: NEVER MUTATED
    # ========================================
    # Keep course_id and group_ids exactly as they are
    new_course_id = gene.course_id
    new_group_ids = gene.group_ids

    # Find qualified instructors for this course
    # instructor.qualified_courses now contains tuples (course_code, course_type)
    qualified_instructors = [
        inst_id
        for inst_id, inst in context.instructors.items()
        if course_key in getattr(inst, "qualified_courses", [])
    ]

    # If current instructor is qualified, keep with high probability (70%)
    if gene.instructor_id in qualified_instructors and random.random() < 0.7:
        new_instructor = gene.instructor_id
    else:
        new_instructor = random.choice(
            qualified_instructors if qualified_instructors else [gene.instructor_id]
        )

    # ========================================
    # ROOM: Mutate intelligently
    # ========================================
    # Smart room selection with capacity and feature constraints
    # Use first group for room suitability check
    primary_group = gene.group_ids[0] if gene.group_ids else None
    suitable_rooms = find_suitable_rooms_for_course(
        gene.course_id, primary_group, context
    )
    if gene.room_id in suitable_rooms and random.random() < 0.5:
        new_room = gene.room_id  # Keep current room if suitable
    else:
        new_room = random.choice(
            suitable_rooms if suitable_rooms else list(context.rooms.keys())
        )

    # ========================================
    # TIME: Mutate intelligently (preserve quanta count!)
    # ========================================
    # CRITICAL: Keep the SAME number of quanta to preserve course requirements
    new_quanta = mutate_time_quanta(gene, course, context)

    return SessionGene(
        course_id=new_course_id,  # NEVER MUTATED
        course_type=gene.course_type,  # NEVER MUTATED
        instructor_id=new_instructor,  # Mutated
        group_ids=new_group_ids,  # NEVER MUTATED
        room_id=new_room,  # Mutated
        quanta=new_quanta,  # Mutated (but count preserved)
    )


def mutate_time_quanta(gene: SessionGene, course, context) -> List[int]:
    """
    Intelligently mutate time quanta while PRESERVING quanta count.

    CRITICAL: Number of quanta MUST stay the same to avoid
    incomplete_or_extra_sessions violations!

    Only changes WHEN the session happens, not HOW LONG it is.
    """
    # CRITICAL: Preserve the exact number of quanta
    num_quanta = len(gene.quanta)

    # Validate against course requirements (sanity check)
    if course:
        expected_quanta = getattr(course, "quanta_per_week", num_quanta)
        if num_quanta != expected_quanta:
            # If current gene has wrong count, fix it
            num_quanta = expected_quanta

    # Ensure we don't exceed available quanta
    num_quanta = min(num_quanta, len(context.available_quanta))
    num_quanta = max(1, num_quanta)  # At least 1 quantum

    # 30% chance to keep current time slots completely unchanged
    if random.random() < 0.3:
        return gene.quanta

    # Try to assign consecutive quanta for better scheduling
    available_quanta = list(context.available_quanta)

    # Attempt to find consecutive slots
    for attempt in range(5):  # Try 5 times to find consecutive slots
        start_idx = random.randint(0, max(0, len(available_quanta) - num_quanta))
        consecutive_quanta = available_quanta[start_idx : start_idx + num_quanta]

        if len(consecutive_quanta) == num_quanta:
            # Check if quanta are somewhat consecutive (simplified check)
            if (
                num_quanta == 1
                or (max(consecutive_quanta) - min(consecutive_quanta)) < num_quanta * 2
            ):
                return consecutive_quanta

    # Fallback to random selection
    return random.sample(available_quanta, min(num_quanta, len(available_quanta)))


def find_suitable_rooms_for_course(
    course_id: str, group_id: str, context: SchedulingContext
) -> List[str]:
    """
    Find rooms suitable for a specific course and group combination.
    Takes into account group size, course requirements, and room features.
    """
    course = context.courses.get(course_id)
    group = context.groups.get(group_id)

    if not course:
        return list(context.rooms.keys())

    # Get course requirements
    required_features = getattr(course, "required_room_features", [])
    room_type_needed = getattr(course, "room_type", "")

    # Get group size for capacity matching
    group_size = getattr(group, "student_count", 30) if group else 30

    suitable_room_ids = []

    for room_id, room in context.rooms.items():
        room_features = getattr(room, "room_features", [])
        room_capacity = getattr(room, "capacity", 50)
        room_type = getattr(room, "type", "Classroom")

        # Check capacity requirement first
        if room_capacity < group_size:
            continue

        # Check feature requirements
        if required_features:
            # Normalize to list
            req_list = (
                required_features
                if isinstance(required_features, list)
                else [required_features]
            )
            room_list = (
                room_features if isinstance(room_features, list) else [room_features]
            )

            # Check if ALL required features match ANY room feature (substring matching)
            # This handles cases where course needs "computer" and room has "computer graphics"
            all_matched = True
            for req in req_list:
                req_lower = req.lower().strip()
                if not req_lower:  # Skip empty requirements
                    continue
                # Check if this requirement matches any room feature
                matched = any(req_lower in room_feat.lower() for room_feat in room_list)
                if not matched:
                    all_matched = False
                    break

            if (
                all_matched and req_list
            ):  # Only add if there were requirements and all matched
                suitable_room_ids.append(room_id)
        elif room_type_needed:
            # Check room type requirement
            if room_type_needed.lower() in room_type.lower():
                suitable_room_ids.append(room_id)
        else:
            # No specific requirements, any room with adequate capacity
            suitable_room_ids.append(room_id)

    return suitable_room_ids if suitable_room_ids else list(context.rooms.keys())


def mutate_individual(individual, context, mut_prob=0.2):
    """
    Applies constraint-aware mutation to an individual.
    Reduced mutation probability to preserve good structures.

    Args:
        individual: List of SessionGene
        context: Dict with instructor, rooms, available_quanta,
        mut_prob (float): Probability of mutation for each gene.
    """
    for i in range(len(individual)):
        if random.random() < mut_prob:
            individual[i] = mutate_gene(individual[i], context)
    return (individual,)  # Return as a tuple for DEAP compatibility
