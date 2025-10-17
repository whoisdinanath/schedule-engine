from typing import List, Tuple
import random
from rich.console import Console

from src.ga.sessiongene import SessionGene
from src.ga.individual import create_individual
from src.ga.group_hierarchy import analyze_group_hierarchy
from src.ga.course_group_pairs import generate_course_group_pairs
from src.core.types import SchedulingContext

console = Console()


def generate_course_group_aware_population(n: int, context: SchedulingContext) -> List:
    """
    Generate population using simple course-group enrollment structure.

    NEW ARCHITECTURE: No parent groups!
    - Each group is independent (subgroups are just regular groups)
    - Each (course, group) pair gets ONE session gene
    - Simple iteration: for each group, create genes for all enrolled courses

    This ensures no duplicate genes.

    [!]  CRITICAL: GENE ORDERING GUARANTEE

    This function creates genes in DETERMINISTIC ORDER for all individuals:
    1. Iterates through context["groups"] (dict maintains insertion order in Python 3.7+)
    2. For each group, iterates through enrolled_courses
    3. Creates exactly ONE gene per (course, group) pair

    This deterministic ordering ensures ALL individuals have genes at the SAME
    POSITIONS representing the SAME (course, group) pairs. This is required by
    the position-independent crossover operator (crossover_course_group_aware),
    which validates this structure and matches genes by (course_id, group_ids)
    identity rather than relying on position.

    MUTATION REQUIREMENT: Mutation operators MUST NOT reorder genes or change
    (course_id, group_ids) values. See src/ga/operators/mutation.py for details.

    Args:
        n: Population size
        context: Dict containing courses, groups, instructors, rooms, available_quanta

    Returns:
        List of individuals (each is a list of SessionGenes)
    """
    population = []

    # Step 1: Analyze group hierarchy and generate proper course-group pairs
    # This respects parent-subgroup relationships:
    # - Theory: Lists all subgroups explicitly (e.g., ["BAE2A", "BAE2B"])
    # - Practical: Each subgroup separately (e.g., ["BAE2A"], then ["BAE2B"])
    hierarchy = analyze_group_hierarchy(context.groups)

    # Generate course-group pairs using the proper function
    # Returns: List[Tuple[course_key, group_ids, session_type, num_quanta]]
    pair_tuples = generate_course_group_pairs(
        context.courses, context.groups, hierarchy
    )

    # Convert to simpler format for gene creation
    # (course_key, group_ids, session_type, num_quanta) -> (course_key, group_ids)
    course_group_pairs = [
        (course_key, group_ids) for course_key, group_ids, _, _ in pair_tuples
    ]

    if not course_group_pairs:
        print("Warning: No valid course-group pairs found!")
        return []

    print(f"Found {len(course_group_pairs)} course-group pairs to schedule")

    # Generate population without progress bar for simplicity
    # Progress is already shown at higher level in ga_scheduler
    for individual_idx in range(n):
        genes = []
        used_quanta = set()  # Track used quanta for this individual to avoid conflicts
        instructor_schedule = {}  # Track instructor schedules to avoid conflicts
        group_schedule = {}  # Track group schedules to avoid conflicts

        # Step 2: For each (course, groups) pair, create ONE session gene
        for course_id, group_ids in course_group_pairs:
            course = context.courses.get(course_id)
            if not course:
                continue

            # Get session type from Course object (not from name parsing)
            session_type = course.course_type
            num_quanta = course.quanta_per_week

            # Create ONE session gene for this (course, groups) combination
            # group_ids is already a list (may contain multiple groups for theory)
            session_gene = create_session_gene_with_conflict_avoidance(
                course_id,
                group_ids,  # List of groups (multiple for theory, single for practical)
                session_type,
                num_quanta,
                course,
                context,
                used_quanta,
                instructor_schedule,
                group_schedule,
            )
            if session_gene:
                genes.append(session_gene)

        if genes:
            population.append(create_individual(genes))
        else:
            print(f"Warning: Individual {individual_idx+1} has no genes!")

    print(
        f"Generated {len(population)} individuals with average {sum(len(ind) for ind in population)/len(population):.1f} genes each"
    )
    return population


def extract_course_group_relationships(
    context: SchedulingContext,
) -> List[Tuple[str, str]]:
    """
    Extract valid course-group enrollment pairs from the context.

    IMPORTANT: When a course has both theory and practical components,
    we need to create genes for BOTH. Groups' enrolled_courses contains
    course_codes like "ENSH 252", but the courses dict is keyed by
    (course_code, course_type) tuples.

    Returns:
        List of (course_key, group_id) tuples where course_key is (course_code, course_type)
    """
    course_group_pairs = []

    for group_id, group in context.groups.items():
        # Get enrolled courses for this group (these are course_codes)
        enrolled_courses = getattr(group, "enrolled_courses", [])

        for course_code in enrolled_courses:
            # Check for both theory and practical versions
            # courses dict is keyed by (course_code, course_type) tuples
            theory_key = (course_code, "theory")
            practical_key = (course_code, "practical")

            if theory_key in context.courses:
                course_group_pairs.append((theory_key, group_id))

            if practical_key in context.courses:
                course_group_pairs.append((practical_key, group_id))

    return course_group_pairs


def create_course_component_sessions(
    course_id: str, group_id: str, course, context: SchedulingContext
) -> List[SessionGene]:
    """
    Create session genes for a course-group combination.

    Clean architecture: NO suffixes!
    - All courses have plain course_id (e.g., "ENME 103")
    - course_type attribute distinguishes "theory" vs "practical"
    - Dict keyed by (course_code, course_type) tuples

    Args:
        course_id: Can be either course_code string OR (course_code, course_type) tuple
        group_id: Group identifier
        course: Course object (already has correct quanta_per_week)
        context: GA context with resources

    Returns:
        List of SessionGene objects (typically 1 gene per course-group pair)
    """
    session_genes = []

    # Use the quanta_per_week from Course entity (already correctly set during loading)
    quanta_needed = course.quanta_per_week

    # Get component type from Course object (not from name parsing)
    component_type = course.course_type

    # Create a single session gene for this course-group combination
    gene = create_component_session(
        course_id,
        group_id,
        component_type,
        quanta_needed,
        context,
        require_special_room=(component_type == "practical"),
    )

    if gene:
        session_genes.append(gene)
    else:
        print(f"[!]  Failed to create gene for {course_id} with group {group_id}")

    return session_genes


def create_course_component_sessions_with_conflict_avoidance(
    course_id: str,
    group_id: str,
    course,
    context: SchedulingContext,
    used_quanta: set,
    instructor_schedule: dict,
    group_schedule: dict,
) -> List[SessionGene]:
    """
    Create session genes while avoiding time conflicts.

    Clean architecture: NO suffixes!
    - All courses have plain course_id (e.g., "ENME 103")
    - course_type attribute distinguishes "theory" vs "practical"

    Args:
        course_id: Can be course_code string OR (course_code, course_type) tuple
        group_id: Group identifier
        course: Course object (already has correct quanta_per_week)
        context: GA context with resources
        used_quanta: Set of already used time quanta for this individual
        instructor_schedule: Dict tracking instructor time assignments
        group_schedule: Dict tracking group time assignments

    Returns:
        List of SessionGene objects (typically 1 gene per course-group pair)
    """
    session_genes = []

    # Use the quanta_per_week from Course entity (already correctly set during loading)
    quanta_needed = course.quanta_per_week

    # Get component type from Course object (not from name parsing)
    component_type = course.course_type

    # Create a single session gene for this course-group combination
    gene = create_component_session_with_conflict_avoidance(
        course_id,
        group_id,
        component_type,
        quanta_needed,
        context,
        used_quanta,
        instructor_schedule,
        group_schedule,
        require_special_room=(component_type == "practical"),
    )

    if gene:
        session_genes.append(gene)
    else:
        print(
            f"[!]  Failed to create gene for {course_id} with group {group_id} (conflict-avoidance)"
        )

    return session_genes


def create_session_gene_with_conflict_avoidance(
    course_id: str,
    group_ids: List[str],
    session_type: str,
    num_quanta: int,
    course,
    context: SchedulingContext,
    used_quanta: set,
    instructor_schedule: dict,
    group_schedule: dict,
) -> SessionGene:
    """
    Create ONE session gene for a (course, groups) combination.

    Args:
        course_id: Course identifier
        group_ids: List of group IDs (can be single or multiple)
        session_type: "theory" or "practical"
        num_quanta: Number of quanta needed (from course.quanta_per_week)
        course: Course entity
        context: GA context
        used_quanta, instructor_schedule, group_schedule: Conflict tracking

    Returns:
        SessionGene or None if creation failed
    """
    # Find qualified instructors
    qualified_instructors = find_qualified_instructors(course_id, context)
    if not qualified_instructors:
        qualified_instructors = list(context.instructors.values())

    if not qualified_instructors:
        return None

    instructor = random.choice(qualified_instructors)

    # Find suitable rooms
    is_practical = session_type == "practical"
    suitable_rooms = find_suitable_rooms(
        course, session_type, context, require_special_room=is_practical
    )
    if not suitable_rooms:
        suitable_rooms = list(context.rooms.values())

    if not suitable_rooms:
        return None

    room = random.choice(suitable_rooms)

    # Find available quanta that don't conflict
    available_quanta = [q for q in context.available_quanta if q not in used_quanta]

    if len(available_quanta) < num_quanta:
        # Fall back to all if not enough free
        available_quanta = list(context.available_quanta)

    quanta_needed = min(num_quanta, len(available_quanta))

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

    # Update group schedules for ALL groups in this session
    for gid in group_ids:
        if gid not in group_schedule:
            group_schedule[gid] = set()
        group_schedule[gid].update(assigned_quanta)

    # Create session gene with multi-group support
    # Extract actual course_id from course object (plain code, no tuple)
    actual_course_id = (
        course.course_id
        if hasattr(course, "course_id")
        else (course_id[0] if isinstance(course_id, tuple) else course_id)
    )

    # Get course_type from course object
    actual_course_type = (
        course.course_type if hasattr(course, "course_type") else session_type
    )

    session_gene = SessionGene(
        course_id=actual_course_id,
        course_type=actual_course_type,
        instructor_id=instructor_id,
        group_ids=group_ids,  # Can be multiple groups
        room_id=room.room_id,
        quanta=assigned_quanta,
    )

    return session_gene


def create_component_session_with_conflict_avoidance(
    course_id: str,
    group_id: str,
    component_type: str,
    hours: int,
    context: SchedulingContext,
    used_quanta: set,
    instructor_schedule: dict,
    group_schedule: dict,
    require_special_room: bool = False,
) -> SessionGene:
    """
    Create a single session while avoiding instructor and group conflicts.

    DEPRECATED: Use create_session_gene_with_conflict_avoidance instead.
    Kept for backwards compatibility with old population generators.
    """
    course = context.courses[course_id]

    # Find qualified instructors
    qualified_instructors = find_qualified_instructors(course_id, context)
    if not qualified_instructors:
        qualified_instructors = list(context.instructors.values())

    if not qualified_instructors:
        return None

    instructor = random.choice(qualified_instructors)

    # Find suitable rooms
    suitable_rooms = find_suitable_rooms(
        course, component_type, context, require_special_room
    )
    if not suitable_rooms:
        suitable_rooms = list(context.rooms.values())

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
    available_quanta = [q for q in context.available_quanta if q not in used_quanta]

    if len(available_quanta) < quanta_needed:
        # If not enough conflict-free quanta, use some that are already used (allow some conflicts for now)
        available_quanta = list(context.available_quanta)

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
    # Extract course_id and course_type
    actual_course_id = course_id[0] if isinstance(course_id, tuple) else course_id
    actual_course_type = component_type

    session_gene = SessionGene(
        course_id=actual_course_id,
        course_type=actual_course_type,
        instructor_id=instructor_id,
        group_ids=[group_id],  # Changed to list for multi-group support
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


def create_component_session(
    course_id: str,
    group_id: str,
    component_type: str,
    hours: int,
    context: SchedulingContext,
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
    course = context.courses[course_id]

    # Find qualified instructors
    qualified_instructors = find_qualified_instructors(course_id, context)
    if not qualified_instructors:
        # Fallback to any instructor if none qualified
        qualified_instructors = list(context.instructors.values())

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
        suitable_rooms = list(context.rooms.values())

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
    quanta_needed = min(quanta_needed, len(context.available_quanta))

    # Assign time quanta with some intelligence
    assigned_quanta = assign_intelligent_quanta(quanta_needed, context.available_quanta)

    if not assigned_quanta:
        print(f"Warning: No time quanta available for course {course_id}")
        return None

    # Create session gene
    # Extract course_id and course_type
    actual_course_id = course_id[0] if isinstance(course_id, tuple) else course_id
    actual_course_type = component_type

    session_gene = SessionGene(
        course_id=actual_course_id,
        course_type=actual_course_type,
        instructor_id=instructor.instructor_id,
        group_ids=[group_id],  # Changed to list for multi-group support
        room_id=room.room_id,
        quanta=assigned_quanta,
    )

    return session_gene


def find_qualified_instructors(course_id, context: SchedulingContext) -> List:
    """
    Find instructors qualified to teach this course.

    Args:
        course_id: Can be plain string or (course_code, course_type) tuple
    """
    qualified = []

    for instructor in context.instructors.values():
        # Check if instructor is qualified for this course
        # instructor.qualified_courses now contains tuples (course_code, course_type)
        qualified_courses = getattr(instructor, "qualified_courses", [])
        if course_id in qualified_courses:
            qualified.append(instructor)

    return qualified


def find_suitable_rooms(
    course,
    component_type: str,
    context: SchedulingContext,
    require_special_room: bool = False,
) -> List:
    """
    Find rooms suitable for this course component.
    Takes into account special room requirements and capacity.
    """
    suitable = []

    # Get required room features from course
    required_features = getattr(course, "required_room_features", [])
    course_id = getattr(course, "course_id", "")

    # Find the group size for capacity matching
    # Look through all groups to find ones enrolled in this course
    max_group_size = 30  # default
    for group in context.groups.values():
        if course_id in getattr(group, "enrolled_courses", []):
            group_size = getattr(group, "student_count", 30)
            max_group_size = max(max_group_size, group_size)

    for room in context.rooms.values():
        room_features = getattr(room, "room_features", [])
        room_capacity = getattr(room, "capacity", 50)
        room_type = getattr(room, "type", "Classroom")

        # Check capacity requirement
        if room_capacity < max_group_size:
            continue

        if require_special_room and required_features:
            # For practicals, check if room has required features
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
        course_type=getattr(course, "course_type", "theory"),  # Default to theory
        instructor_id=instructor.instructor_id,
        group_ids=[group.group_id],  # Changed to list for multi-group support
        room_id=room.room_id,
        quanta=quanta,
    )


def generate_population(
    n: int, session_count: int = None, context: SchedulingContext = None
) -> List:
    """
    Wrapper function for backward compatibility.
    Now uses course-group aware generation instead of random.
    """
    if context is None:
        raise ValueError("Context must be provided for population generation")

    return generate_course_group_aware_population(n, context)
