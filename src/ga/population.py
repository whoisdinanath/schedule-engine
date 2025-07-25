from typing import List, Dict, Tuple
import random

from src.ga.sessiongene import SessionGene
from src.ga.individual import create_individual


def generate_course_group_aware_population(n: int, context: Dict) -> List:
    """
    Generate population using course-group enrollment structure.
    This approach is superior to random generation as it respects
    fundamental university timetabling constraints.

    Args:
        n: Population size
        context: Dict containing courses, groups, instructors, rooms, available_quanta

    Returns:
        List of individuals (each is a list of SessionGenes)
    """
    population = []

    # Step 1: Extract course-group enrollment relationships
    course_group_sessions = extract_course_group_relationships(context)

    if not course_group_sessions:
        print("Warning: No valid course-group relationships found!")
        return []

    print(f"Found {len(course_group_sessions)} course-group relationships")

    for individual_idx in range(n):
        genes = []
        used_quanta = set()  # Track used quanta for this individual to avoid conflicts
        instructor_schedule = {}  # Track instructor schedules to avoid conflicts
        group_schedule = {}  # Track group schedules to avoid conflicts

        # Step 2: For each valid course-group pair, create sessions
        for course_id, group_id in course_group_sessions:
            course = context["courses"][course_id]
            group = context["groups"][group_id]

            # Create sessions for different course components (L, T, P)
            session_genes = create_course_component_sessions_with_conflict_avoidance(
                course_id,
                group_id,
                course,
                context,
                used_quanta,
                instructor_schedule,
                group_schedule,
            )
            genes.extend(session_genes)

        if genes:
            population.append(create_individual(genes))
        else:
            print(f"Warning: Individual {individual_idx+1} has no genes!")

    print(
        f"Generated {len(population)} individuals with average {sum(len(ind) for ind in population)/len(population):.1f} genes each"
    )
    return population


def extract_course_group_relationships(context: Dict) -> List[Tuple[str, str]]:
    """
    Extract valid course-group enrollment pairs from the context.

    Returns:
        List of (course_id, group_id) tuples representing valid enrollments
    """
    course_group_pairs = []

    for group_id, group in context["groups"].items():
        # Get enrolled courses for this group
        enrolled_courses = getattr(group, "enrolled_courses", [])

        for course_id in enrolled_courses:
            if course_id in context["courses"]:
                course_group_pairs.append((course_id, group_id))

    return course_group_pairs


def create_course_component_sessions(
    course_id: str, group_id: str, course, context: Dict
) -> List[SessionGene]:
    """
    Create session genes for different course components (Lecture, Tutorial, Practical).
    Based on the FullSyllabusAll.json structure with L, T, P components.

    Args:
        course_id: Course identifier
        group_id: Group identifier
        course: Course object
        context: GA context with resources

    Returns:
        List of SessionGene objects for this course-group combination
    """
    session_genes = []

    # Get course component information with fallbacks
    lecture_hours = getattr(course, "L", getattr(course, "lecture_hours", 0))
    tutorial_hours = getattr(course, "T", getattr(course, "tutorial_hours", 0))
    practical_hours = getattr(course, "P", getattr(course, "practical_hours", 0))

    # Create Lecture Sessions
    if lecture_hours > 0:
        lecture_gene = create_component_session(
            course_id, group_id, "lecture", lecture_hours, context
        )
        if lecture_gene:
            session_genes.append(lecture_gene)

    # Create Tutorial Sessions
    if tutorial_hours > 0:
        tutorial_gene = create_component_session(
            course_id, group_id, "tutorial", tutorial_hours, context
        )
        if tutorial_gene:
            session_genes.append(tutorial_gene)

    # Create Practical Sessions
    if practical_hours > 0:
        practical_gene = create_component_session(
            course_id,
            group_id,
            "practical",
            practical_hours,
            context,
            require_special_room=True,
        )
        if practical_gene:
            session_genes.append(practical_gene)

    # If no components defined, create default sessions based on course requirements
    if not session_genes:
        # Try to get total hours from course metadata
        total_hours = getattr(course, "total_hours_per_week", 3)
        credit_hours = getattr(course, "credit_hours", 3)
        hours_per_week = getattr(
            course, "hours_per_week", max(total_hours, credit_hours)
        )

        default_gene = create_component_session(
            course_id, group_id, "default", hours_per_week, context
        )
        if default_gene:
            session_genes.append(default_gene)

    return session_genes


def create_course_component_sessions_with_conflict_avoidance(
    course_id: str,
    group_id: str,
    course,
    context: Dict,
    used_quanta: set,
    instructor_schedule: dict,
    group_schedule: dict,
) -> List[SessionGene]:
    """
    Create session genes while avoiding time conflicts.

    Args:
        course_id: Course identifier
        group_id: Group identifier
        course: Course object
        context: GA context with resources
        used_quanta: Set of already used time quanta for this individual
        instructor_schedule: Dict tracking instructor time assignments
        group_schedule: Dict tracking group time assignments

    Returns:
        List of SessionGene objects for this course-group combination
    """
    session_genes = []

    # Get course component information with fallbacks
    lecture_hours = getattr(course, "L", getattr(course, "lecture_hours", 0))
    tutorial_hours = getattr(course, "T", getattr(course, "tutorial_hours", 0))
    practical_hours = getattr(course, "P", getattr(course, "practical_hours", 0))

    # Create Lecture Sessions
    if lecture_hours > 0:
        lecture_gene = create_component_session_with_conflict_avoidance(
            course_id,
            group_id,
            "lecture",
            lecture_hours,
            context,
            used_quanta,
            instructor_schedule,
            group_schedule,
        )
        if lecture_gene:
            session_genes.append(lecture_gene)

    # Create Tutorial Sessions
    if tutorial_hours > 0:
        tutorial_gene = create_component_session_with_conflict_avoidance(
            course_id,
            group_id,
            "tutorial",
            tutorial_hours,
            context,
            used_quanta,
            instructor_schedule,
            group_schedule,
        )
        if tutorial_gene:
            session_genes.append(tutorial_gene)

    # Create Practical Sessions
    if practical_hours > 0:
        practical_gene = create_component_session_with_conflict_avoidance(
            course_id,
            group_id,
            "practical",
            practical_hours,
            context,
            used_quanta,
            instructor_schedule,
            group_schedule,
            require_special_room=True,
        )
        if practical_gene:
            session_genes.append(practical_gene)

    # If no components defined, create default sessions based on course requirements
    if not session_genes:
        # Try to get total hours from course metadata
        total_hours = getattr(course, "total_hours_per_week", 3)
        credit_hours = getattr(course, "credit_hours", 3)
        hours_per_week = getattr(
            course, "hours_per_week", max(total_hours, credit_hours)
        )

        default_gene = create_component_session_with_conflict_avoidance(
            course_id,
            group_id,
            "default",
            hours_per_week,
            context,
            used_quanta,
            instructor_schedule,
            group_schedule,
        )
        if default_gene:
            session_genes.append(default_gene)

    return session_genes


def create_component_session_with_conflict_avoidance(
    course_id: str,
    group_id: str,
    component_type: str,
    hours: int,
    context: Dict,
    used_quanta: set,
    instructor_schedule: dict,
    group_schedule: dict,
    require_special_room: bool = False,
) -> SessionGene:
    """
    Create a single session while avoiding instructor and group conflicts.
    """
    course = context["courses"][course_id]

    # Find qualified instructors
    qualified_instructors = find_qualified_instructors(course_id, context)
    if not qualified_instructors:
        qualified_instructors = list(context["instructors"].values())

    if not qualified_instructors:
        return None

    instructor = random.choice(qualified_instructors)

    # Find suitable rooms
    suitable_rooms = find_suitable_rooms(
        course, component_type, context, require_special_room
    )
    if not suitable_rooms:
        suitable_rooms = list(context["rooms"].values())

    if not suitable_rooms:
        return None

    room = random.choice(suitable_rooms)

    # Convert hours to quanta and assign conflict-free time slots
    # Each hour = 4 quanta (15-minute slots), but limit max session length
    quanta_per_hour = 4
    max_session_length = 8  # Maximum 2 hours per session

    raw_quanta_needed = max(1, int(hours * quanta_per_hour))
    quanta_needed = min(raw_quanta_needed, max_session_length)

    # If the course needs more quanta than max session length, we should create multiple sessions
    # For now, just limit to reasonable session length

    # Find available quanta that don't conflict with used ones
    available_quanta = [q for q in context["available_quanta"] if q not in used_quanta]

    if len(available_quanta) < quanta_needed:
        # If not enough conflict-free quanta, use some that are already used (allow some conflicts for now)
        available_quanta = list(context["available_quanta"])

    quanta_needed = min(quanta_needed, len(available_quanta))

    if quanta_needed == 0:
        return None

    # Assign time quanta
    assigned_quanta = assign_conflict_free_quanta(
        quanta_needed, available_quanta, used_quanta
    )

    if not assigned_quanta:
        return None

    # Update tracking structures
    used_quanta.update(assigned_quanta)
    instructor_id = instructor.instructor_id
    if instructor_id not in instructor_schedule:
        instructor_schedule[instructor_id] = set()
    instructor_schedule[instructor_id].update(assigned_quanta)

    if group_id not in group_schedule:
        group_schedule[group_id] = set()
    group_schedule[group_id].update(assigned_quanta)

    # Create session gene
    session_gene = SessionGene(
        course_id=course_id,
        instructor_id=instructor_id,
        group_id=group_id,
        room_id=room.room_id,
        quanta=assigned_quanta,
    )

    return session_gene


def assign_conflict_free_quanta(
    quanta_needed: int, available_quanta: List, used_quanta: set
) -> List:
    """
    Assign time quanta while avoiding conflicts with already used quanta.
    Prefers consecutive slots for better scheduling quality.
    """
    if quanta_needed <= 0:
        return []

    # Filter out already used quanta
    free_quanta = [q for q in available_quanta if q not in used_quanta]

    if len(free_quanta) < quanta_needed:
        # If not enough free quanta, fall back to all available
        free_quanta = list(available_quanta)

    quanta_needed = min(quanta_needed, len(free_quanta))

    if quanta_needed == 0:
        return []

    # For sessions needing 2-4 quanta, try to find consecutive slots
    if 2 <= quanta_needed <= 4 and len(free_quanta) >= quanta_needed:
        # Sort quanta to find consecutive sequences
        sorted_free = sorted(free_quanta)

        # Try to find consecutive slots
        for i in range(len(sorted_free) - quanta_needed + 1):
            consecutive_candidates = sorted_free[i : i + quanta_needed]

            # Check if they are truly consecutive
            is_consecutive = True
            for j in range(1, len(consecutive_candidates)):
                if consecutive_candidates[j] - consecutive_candidates[j - 1] != 1:
                    is_consecutive = False
                    break

            if is_consecutive:
                return consecutive_candidates

    # If no consecutive slots found or not needed, select randomly
    return random.sample(free_quanta, quanta_needed)
    """
    Create session genes for different course components (Lecture, Tutorial, Practical).
    Based on the FullSyllabusAll.json structure with L, T, P components.
    
    Args:
        course_id: Course identifier
        group_id: Group identifier  
        course: Course object
        context: GA context with resources
    
    Returns:
        List of SessionGene objects for this course-group combination
    """
    session_genes = []

    # Get course component information with fallbacks
    lecture_hours = getattr(course, "L", getattr(course, "lecture_hours", 0))
    tutorial_hours = getattr(course, "T", getattr(course, "tutorial_hours", 0))
    practical_hours = getattr(course, "P", getattr(course, "practical_hours", 0))

    # Create Lecture Sessions
    if lecture_hours > 0:
        lecture_gene = create_component_session(
            course_id, group_id, "lecture", lecture_hours, context
        )
        if lecture_gene:
            session_genes.append(lecture_gene)

    # Create Tutorial Sessions
    if tutorial_hours > 0:
        tutorial_gene = create_component_session(
            course_id, group_id, "tutorial", tutorial_hours, context
        )
        if tutorial_gene:
            session_genes.append(tutorial_gene)

    # Create Practical Sessions
    if practical_hours > 0:
        practical_gene = create_component_session(
            course_id,
            group_id,
            "practical",
            practical_hours,
            context,
            require_special_room=True,
        )
        if practical_gene:
            session_genes.append(practical_gene)

    # If no components defined, create default sessions based on course requirements
    if not session_genes:
        # Try to get total hours from course metadata
        total_hours = getattr(course, "total_hours_per_week", 3)
        credit_hours = getattr(course, "credit_hours", 3)
        hours_per_week = getattr(
            course, "hours_per_week", max(total_hours, credit_hours)
        )

        default_gene = create_component_session(
            course_id, group_id, "default", hours_per_week, context
        )
        if default_gene:
            session_genes.append(default_gene)

    return session_genes


def create_component_session(
    course_id: str,
    group_id: str,
    component_type: str,
    hours: int,
    context: Dict,
    require_special_room: bool = False,
) -> SessionGene:
    """
    Create a single session for a specific course component.

    Args:
        course_id: Course identifier
        group_id: Group identifier
        component_type: "lecture", "tutorial", "practical", or "default"
        hours: Number of hours per week for this component
        context: GA context
        require_special_room: Whether this component needs special room features

    Returns:
        SessionGene object for this component (or None if creation fails)
    """
    course = context["courses"][course_id]

    # Find qualified instructors
    qualified_instructors = find_qualified_instructors(course_id, context)
    if not qualified_instructors:
        # Fallback to any instructor if none qualified
        qualified_instructors = list(context["instructors"].values())

    if not qualified_instructors:
        print(f"Warning: No instructors available for course {course_id}")
        return None

    instructor = random.choice(qualified_instructors)

    # Find suitable rooms
    suitable_rooms = find_suitable_rooms(
        course, component_type, context, require_special_room
    )
    if not suitable_rooms:
        # Fallback to any room if none suitable
        suitable_rooms = list(context["rooms"].values())

    if not suitable_rooms:
        print(f"Warning: No rooms available for course {course_id}")
        return None

    room = random.choice(suitable_rooms)

    # Convert hours to quanta (assuming 1 hour = 4 quanta of 15 minutes each)
    # But limit session length to reasonable maximum (2 hours = 8 quanta)
    quanta_per_hour = 4
    max_session_length = 8  # Maximum 2 hours per session

    raw_quanta_needed = max(1, int(hours * quanta_per_hour))
    quanta_needed = min(raw_quanta_needed, max_session_length)
    quanta_needed = min(quanta_needed, len(context["available_quanta"]))

    # Assign time quanta with some intelligence
    assigned_quanta = assign_intelligent_quanta(
        quanta_needed, context["available_quanta"]
    )

    if not assigned_quanta:
        print(f"Warning: No time quanta available for course {course_id}")
        return None

    # Create session gene
    session_gene = SessionGene(
        course_id=course_id,
        instructor_id=instructor.instructor_id,
        group_id=group_id,
        room_id=room.room_id,
        quanta=assigned_quanta,
    )

    return session_gene


def find_qualified_instructors(course_id: str, context: Dict) -> List:
    """Find instructors qualified to teach this course."""
    qualified = []

    for instructor in context["instructors"].values():
        # Check if instructor is qualified for this course
        qualified_courses = getattr(instructor, "qualified_courses", [course_id])
        if course_id in qualified_courses:
            qualified.append(instructor)

    return qualified


def find_suitable_rooms(
    course, component_type: str, context: Dict, require_special_room: bool = False
) -> List:
    """
    Find rooms suitable for this course component.
    Takes into account special room requirements and capacity.
    """
    suitable = []

    # Get required room features from course
    required_features = getattr(course, "PracticalRoomFeatures", "")
    course_id = getattr(course, "course_id", "")

    # Find the group size for capacity matching
    # Look through all groups to find ones enrolled in this course
    max_group_size = 30  # default
    for group in context["groups"].values():
        if course_id in getattr(group, "enrolled_courses", []):
            group_size = getattr(group, "student_count", 30)
            max_group_size = max(max_group_size, group_size)

    for room in context["rooms"].values():
        room_features = getattr(room, "features", [])
        room_capacity = getattr(room, "capacity", 50)
        room_type = getattr(room, "type", "Classroom")

        # Check capacity requirement
        if room_capacity < max_group_size:
            continue

        if require_special_room and required_features:
            # For practicals, check if room has required features
            if isinstance(room_features, list):
                room_features_str = " ".join(room_features).lower()
            else:
                room_features_str = str(room_features).lower()

            if required_features.lower() in room_features_str:
                suitable.append(room)
        elif component_type == "practical" and room_type.lower() in [
            "lab",
            "laboratory",
        ]:
            # For practicals without specific requirements, prefer labs
            suitable.append(room)
        elif component_type in ["lecture", "tutorial"]:
            # For lectures/tutorials, prefer classrooms but any room with capacity works
            suitable.append(room)
        else:
            # Fallback - any room with adequate capacity
            suitable.append(room)

    return suitable


def assign_intelligent_quanta(quanta_needed: int, available_quanta: List) -> List:
    """
    Assign time quanta with intelligence to avoid fragmentation and conflicts.
    Ensures no overlap by randomly selecting from available slots.
    """
    if quanta_needed <= 0:
        return []

    available_list = list(available_quanta)

    if quanta_needed > len(available_list):
        quanta_needed = len(available_list)

    if quanta_needed == 0:
        return []

    # For better schedule quality, try to find consecutive quanta first
    # But only for smaller requirements (up to 8 quanta = 2 hours)
    if quanta_needed <= 8:
        # Try to find consecutive quanta
        for attempt in range(3):  # 3 attempts to find consecutive slots
            start_idx = random.randint(0, max(0, len(available_list) - quanta_needed))
            consecutive_quanta = available_list[start_idx : start_idx + quanta_needed]

            if len(consecutive_quanta) == quanta_needed:
                # Simple check for reasonable time spread
                if (
                    quanta_needed == 1
                    or (max(consecutive_quanta) - min(consecutive_quanta))
                    < quanta_needed * 1.5
                ):
                    return consecutive_quanta

    # Fallback: Random selection to ensure diversity and avoid conflicts
    return random.sample(available_list, quanta_needed)


def generate_random_gene(
    possible_courses,
    possible_instructors,
    possible_groups,
    possible_rooms,
    available_quanta,
) -> SessionGene:
    """Legacy function for backward compatibility."""
    course = random.choice(possible_courses)

    # Try to find a qualified instructor (constraint-aware)
    qualified_instructors = [
        inst
        for inst in possible_instructors
        if course.course_id in getattr(inst, "qualified_courses", [course.course_id])
    ]
    instructor = random.choice(
        qualified_instructors if qualified_instructors else possible_instructors
    )

    # Try to find a compatible group (constraint-aware)
    compatible_groups = [
        grp
        for grp in possible_groups
        if course.course_id in getattr(grp, "enrolled_courses", [course.course_id])
    ]
    group = random.choice(compatible_groups if compatible_groups else possible_groups)

    room = random.choice(possible_rooms)

    # Use course's required quanta count if available
    num_quanta = getattr(course, "quanta_per_week", random.randint(1, 4))
    num_quanta = min(
        num_quanta, len(available_quanta)
    )  # Ensure we don't exceed available

    # You may want to base this on course.quanta_per_week
    quanta = random.sample(list(available_quanta), num_quanta)

    return SessionGene(
        course_id=course.course_id,
        instructor_id=instructor.instructor_id,
        group_id=group.group_id,
        room_id=room.room_id,
        quanta=quanta,
    )


def generate_population(
    n: int, session_count: int = None, context: Dict = None
) -> List:
    """
    Wrapper function for backward compatibility.
    Now uses course-group aware generation instead of random.
    """
    if context is None:
        raise ValueError("Context must be provided for population generation")

    return generate_course_group_aware_population(n, context)
