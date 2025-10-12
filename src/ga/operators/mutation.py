import random
from src.ga.sessiongene import SessionGene
from typing import List


def mutate_gene(gene: SessionGene, context) -> SessionGene:
    """
    Performs intelligent constraint-aware mutation on a single gene.
    Preserves course-group relationships and uses domain knowledge.
    """
    # Get course info for constraint-aware mutation
    course = context["courses"].get(gene.course_id)

    # CRITICAL: Preserve course-group enrollment relationship
    # Only mutate to groups that are actually enrolled in this course
    enrolled_groups = []
    for grp_id, grp in context["groups"].items():
        if gene.course_id in getattr(grp, "enrolled_courses", []):
            enrolled_groups.append(grp_id)

    # If current group is valid, keep it with very high probability (90%)
    if gene.group_id in enrolled_groups and random.random() < 0.9:
        new_group = gene.group_id  # Keep existing valid group
    else:
        new_group = random.choice(
            enrolled_groups if enrolled_groups else [gene.group_id]
        )

    # Find qualified instructors for this course
    qualified_instructors = [
        inst_id
        for inst_id, inst in context["instructors"].items()
        if gene.course_id in getattr(inst, "qualified_courses", [gene.course_id])
    ]

    # If current instructor is qualified, keep with high probability (70%)
    if gene.instructor_id in qualified_instructors and random.random() < 0.7:
        new_instructor = gene.instructor_id
    else:
        new_instructor = random.choice(
            qualified_instructors if qualified_instructors else [gene.instructor_id]
        )

    # Smart room selection with capacity and feature constraints
    suitable_rooms = find_suitable_rooms_for_course(gene.course_id, new_group, context)
    if gene.room_id in suitable_rooms and random.random() < 0.5:
        new_room = gene.room_id  # Keep current room if suitable
    else:
        new_room = random.choice(
            suitable_rooms if suitable_rooms else list(context["rooms"].keys())
        )

    # Intelligent time assignment with conflict avoidance
    new_quanta = mutate_time_quanta(gene, course, context)

    return SessionGene(
        course_id=gene.course_id,  # Always preserve course ID
        instructor_id=new_instructor,
        group_id=new_group,
        room_id=new_room,
        quanta=new_quanta,
    )


def mutate_time_quanta(gene: SessionGene, course, context) -> List[int]:
    """
    Intelligently mutate time quanta while respecting course requirements.
    """
    # Determine required quanta based on course info
    if course:
        # Check if course has L, T, P components
        lecture_hours = getattr(course, "L", 0)
        tutorial_hours = getattr(course, "T", 0)
        practical_hours = getattr(course, "P", 0)

        # Calculate total required quanta (4 quanta per hour)
        total_hours = lecture_hours + tutorial_hours + practical_hours
        if total_hours > 0:
            num_quanta = int(total_hours * 4)
        else:
            num_quanta = getattr(course, "quanta_per_week", len(gene.quanta))
    else:
        num_quanta = len(gene.quanta)

    # Ensure we don't exceed available quanta
    num_quanta = min(num_quanta, len(context["available_quanta"]))
    num_quanta = max(1, num_quanta)  # At least 1 quantum

    # 30% chance to keep current time if it's reasonable
    if len(gene.quanta) == num_quanta and random.random() < 0.3:
        return gene.quanta

    # Try to assign consecutive quanta for better scheduling
    available_quanta = list(context["available_quanta"])

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


def find_suitable_rooms_for_course(course_id: str, group_id: str, context) -> List[str]:
    """
    Find rooms suitable for a specific course and group combination.
    Takes into account group size, course requirements, and room features.
    """
    course = context["courses"].get(course_id)
    group = context["groups"].get(group_id)

    if not course:
        return list(context["rooms"].keys())

    # Get course requirements
    required_features = getattr(course, "PracticalRoomFeatures", "")
    room_type_needed = getattr(course, "room_type", "")

    # Get group size for capacity matching
    group_size = getattr(group, "student_count", 30) if group else 30

    suitable_room_ids = []

    for room_id, room in context["rooms"].items():
        room_features = getattr(room, "features", [])
        room_capacity = getattr(room, "capacity", 50)
        room_type = getattr(room, "type", "Classroom")

        # Check capacity requirement first
        if room_capacity < group_size:
            continue

        # Check feature requirements
        if required_features:
            if isinstance(room_features, list):
                room_features_str = " ".join(room_features).lower()
            else:
                room_features_str = str(room_features).lower()

            if required_features.lower() in room_features_str:
                suitable_room_ids.append(room_id)
        elif room_type_needed:
            # Check room type requirement
            if room_type_needed.lower() in room_type.lower():
                suitable_room_ids.append(room_id)
        else:
            # No specific requirements, any room with adequate capacity
            suitable_room_ids.append(room_id)

    return suitable_room_ids if suitable_room_ids else list(context["rooms"].keys())


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
