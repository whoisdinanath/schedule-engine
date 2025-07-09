#!/usr/bin/env python3
"""
Data validation fix script for the genetics timetabling system.
This script fixes common validation errors in the data files.
"""

import pandas as pd
import re
import os
from pathlib import Path

def fix_room_time_slots(rooms_file):
    """Fix invalid time slot formats in rooms file."""
    print("Fixing room time slots...")
    
    # Read the rooms file
    df = pd.read_csv(rooms_file)
    
    # Function to fix time slot
    def fix_time_slot(slot_str):
        if pd.isna(slot_str):
            return slot_str
        
        # Pattern to match invalid time formats like 18:60, 18:61, etc.
        pattern = r'(\d{2}:\d{2})-(\d{2}):(\d{2})'
        
        def replace_func(match):
            start_time = match.group(1)
            end_hour = match.group(2)
            end_minute = match.group(3)
            
            # Fix invalid minutes (>59)
            if int(end_minute) > 59:
                end_minute = "00"
            
            return f"{start_time}-{end_hour}:{end_minute}"
        
        return re.sub(pattern, replace_func, slot_str)
    
    # Apply the fix
    df['available_slots'] = df['available_slots'].apply(fix_time_slot)
    
    # Save the fixed file
    backup_file = rooms_file.replace('.csv', '_backup.csv')
    df.to_csv(backup_file, index=False)
    print(f"Backup created: {backup_file}")
    
    df.to_csv(rooms_file, index=False)
    print(f"Fixed rooms file: {rooms_file}")
    
    return df

def add_missing_courses(courses_file):
    """Add missing courses that are referenced but don't exist."""
    print("Adding missing courses...")
    
    # Read existing courses
    df = pd.read_csv(courses_file)
    
    # Missing courses identified from validation errors
    missing_courses = [
        # Format: (course_id, name, sessions_per_week, duration, required_room_type, group_ids, qualified_instructor_ids)
        ("ENSH 152", "Communication English II", 3, 50, "lecture", "7,11", "1,2,3,94,110"),
        ("ENSH 154", "Technical Writing", 3, 50, "lecture", "7,8", "7,11,12,13,15"),
        ("ENSH 154-PR", "Technical Writing Practical", 1, 90, "lab", "7,8", "11,12,13"),
        ("ENSH 242", "Professional Communication", 3, 50, "lecture", "8,10", "9,10,62"),
        ("ENSH 156", "Advanced English", 3, 50, "lecture", "9,10", "16,17,18"),
        ("COMP 153-PR", "Programming Practical", 2, 90, "lab", "7", "11"),
        ("ELEC 152-PR", "Electronics Practical", 2, 90, "lab", "3,1", "15"),
        ("ENEE 253", "Control Systems", 4, 50, "lecture", "2,4", "54"),
        ("ENEE 253-PR", "Control Systems Lab", 1, 90, "lab", "2,4", "54"),
        ("ENEE 251", "Power Systems", 4, 50, "lecture", "2,4", "55"),
        ("ENCE 260", "Structural Analysis", 4, 50, "lecture", "14", "73"),
        ("ENAR 254-PR", "Design Studio Practical", 2, 90, "lab", "14", "79"),
        ("ENAR 251", "Architectural Design", 4, 50, "lecture", "14", "80"),
        ("ENAR 253-PR", "Construction Practical", 1, 90, "lab", "14", "81"),
        ("ENCE 256", "Concrete Technology", 3, 50, "lecture", "8", "82"),
        ("ENSH 251-PR", "English Practical", 1, 90, "lab", "8", "83"),
        ("ENIE 254", "Industrial Management", 3, 50, "lecture", "10", "84"),
    ]
    
    # Create new rows for missing courses
    new_rows = []
    for course_data in missing_courses:
        new_row = {
            'course_id': course_data[0],
            'name': course_data[1],
            'sessions_per_week': course_data[2],
            'duration': course_data[3],
            'required_room_type': course_data[4],
            'group_ids': course_data[5],
            'qualified_instructor_ids': course_data[6]
        }
        new_rows.append(new_row)
    
    # Add to dataframe
    new_df = pd.DataFrame(new_rows)
    df = pd.concat([df, new_df], ignore_index=True)
    
    # Save the updated file
    backup_file = courses_file.replace('.csv', '_backup.csv')
    df.to_csv(backup_file, index=False)
    print(f"Backup created: {backup_file}")
    
    df.to_csv(courses_file, index=False)
    print(f"Updated courses file: {courses_file}")
    
    return df

def add_large_capacity_rooms(rooms_file):
    """Add larger capacity rooms to handle big classes."""
    print("Adding large capacity rooms...")
    
    # Read existing rooms
    df = pd.read_csv(rooms_file)
    
    # Add large lecture halls
    large_rooms = [
        ("HALL1", "Main Auditorium", 200, "lecture", "monday_08:00-18:00,tuesday_08:00-18:00,wednesday_08:00-18:00,thursday_08:00-18:00,friday_08:00-18:00"),
        ("HALL2", "Large Lecture Hall", 150, "lecture", "monday_08:00-18:00,tuesday_08:00-18:00,wednesday_08:00-18:00,thursday_08:00-18:00,friday_08:00-18:00"),
        ("HALL3", "Conference Hall", 100, "lecture", "monday_08:00-18:00,tuesday_08:00-18:00,wednesday_08:00-18:00,thursday_08:00-18:00,friday_08:00-18:00"),
        ("HALL4", "Assembly Hall", 250, "lecture", "monday_08:00-18:00,tuesday_08:00-18:00,wednesday_08:00-18:00,thursday_08:00-18:00,friday_08:00-18:00"),
        ("HALL5", "Seminar Hall", 120, "lecture", "monday_08:00-18:00,tuesday_08:00-18:00,wednesday_08:00-18:00,thursday_08:00-18:00,friday_08:00-18:00"),
    ]
    
    # Create new rows for large rooms
    new_rows = []
    for room_data in large_rooms:
        new_row = {
            'room_id': room_data[0],
            'name': room_data[1],
            'capacity': room_data[2],
            'type': room_data[3],
            'available_slots': room_data[4]
        }
        new_rows.append(new_row)
    
    # Add to dataframe
    new_df = pd.DataFrame(new_rows)
    df = pd.concat([df, new_df], ignore_index=True)
    
    # Save the updated file
    backup_file = rooms_file.replace('.csv', '_backup.csv')
    if not os.path.exists(backup_file):  # Don't overwrite existing backup
        df_original = pd.read_csv(rooms_file)
        df_original.to_csv(backup_file, index=False)
        print(f"Backup created: {backup_file}")
    
    df.to_csv(rooms_file, index=False)
    print(f"Updated rooms file: {rooms_file}")
    
    return df

def clean_instructor_qualifications(instructors_file):
    """Clean up instructor qualifications to remove duplicates and invalid references."""
    print("Cleaning instructor qualifications...")
    
    # Read existing instructors
    df = pd.read_csv(instructors_file)
    
    # Function to clean qualifications
    def clean_qualifications(qual_str):
        if pd.isna(qual_str):
            return qual_str
        
        # Split by comma and clean each course
        courses = [course.strip() for course in qual_str.split(',')]
        # Remove duplicates while preserving order
        unique_courses = []
        seen = set()
        for course in courses:
            if course not in seen:
                unique_courses.append(course)
                seen.add(course)
        
        return ','.join(unique_courses)
    
    # Apply cleaning
    df['qualified_courses'] = df['qualified_courses'].apply(clean_qualifications)
    
    # Save the updated file
    backup_file = instructors_file.replace('.csv', '_backup.csv')
    if not os.path.exists(backup_file):
        df_original = pd.read_csv(instructors_file)
        df_original.to_csv(backup_file, index=False)
        print(f"Backup created: {backup_file}")
    
    df.to_csv(instructors_file, index=False)
    print(f"Updated instructors file: {instructors_file}")
    
    return df

def fix_instructor_qualifications(instructors_file):
    """Fix instructor qualifications to match course requirements."""
    print("Fixing instructor qualifications...")
    
    # Read existing instructors
    df = pd.read_csv(instructors_file)
    
    # Function to update instructor qualifications
    def update_qualifications(row):
        instructor_id = row['instructor_id']
        current_quals = row['qualified_courses']
        
        # Add missing qualifications based on course requirements
        additional_quals = []
        
        if instructor_id == 80:
            additional_quals.append("ENAR 251")
        elif instructor_id == 81:
            additional_quals.append("ENAR 253-PR")
        elif instructor_id == 82:
            additional_quals.append("ENCE 256")
        elif instructor_id == 83:
            additional_quals.append("ENSH 251-PR")
        elif instructor_id == 84:
            additional_quals.append("ENIE 254")
        
        # Add new qualifications
        if additional_quals:
            if pd.isna(current_quals):
                new_quals = ','.join(additional_quals)
            else:
                current_list = [q.strip() for q in current_quals.split(',')]
                current_list.extend(additional_quals)
                new_quals = ','.join(current_list)
            return new_quals
        
        return current_quals
    
    # Apply the update
    df['qualified_courses'] = df.apply(update_qualifications, axis=1)
    
    # Save the updated file
    backup_file = instructors_file.replace('.csv', '_backup.csv')
    if not os.path.exists(backup_file):
        df_original = pd.read_csv(instructors_file)
        df_original.to_csv(backup_file, index=False)
        print(f"Backup created: {backup_file}")
    
    df.to_csv(instructors_file, index=False)
    print(f"Updated instructors file: {instructors_file}")
    
    return df

def fix_group_enrollments(groups_file):
    """Fix group enrollments to match course requirements."""
    print("Fixing group enrollments...")
    
    # Read existing groups
    df = pd.read_csv(groups_file)
    
    # Function to update group enrollments
    def update_enrollments(row):
        group_id = row['group_id']
        current_enrollments = row['enrolled_courses']
        
        # Add missing enrollments based on course requirements
        additional_courses = []
        
        if group_id == "7":  # BCE2
            additional_courses.extend(["ENSH 154", "ENSH 154-PR", "COMP 153-PR"])
        elif group_id == "8":  # BCE4
            additional_courses.extend(["ENSH 154", "ENSH 154-PR", "ENSH 242"])
        elif group_id == "9":  # BIE2
            additional_courses.append("ENSH 156")
        elif group_id == "10":  # BIE4
            additional_courses.extend(["ENSH 242", "ENSH 156"])
        elif group_id == "1":  # BEI2
            additional_courses.append("ELEC 152-PR")
        elif group_id == "3":  # BCT2
            additional_courses.append("ELEC 152-PR")
        elif group_id == "2":  # BEI4
            additional_courses.extend(["ENEE 253", "ENEE 253-PR", "ENEE 251"])
        elif group_id == "4":  # BCT4
            additional_courses.extend(["ENEE 253", "ENEE 253-PR", "ENEE 251"])
        elif group_id == "14":  # BARCH4
            additional_courses.append("ENAR 254-PR")
        
        # Add new enrollments
        if additional_courses:
            if pd.isna(current_enrollments):
                new_enrollments = ', '.join(additional_courses)
            else:
                current_list = [c.strip() for c in current_enrollments.split(',')]
                current_list.extend(additional_courses)
                new_enrollments = ', '.join(current_list)
            return new_enrollments
        
        return current_enrollments
    
    # Apply the update
    df['enrolled_courses'] = df.apply(update_enrollments, axis=1)
    
    # Save the updated file
    backup_file = groups_file.replace('.csv', '_backup.csv')
    if not os.path.exists(backup_file):
        df_original = pd.read_csv(groups_file)
        df_original.to_csv(backup_file, index=False)
        print(f"Backup created: {backup_file}")
    
    df.to_csv(groups_file, index=False)
    print(f"Updated groups file: {groups_file}")
    
    return df

def add_large_labs(rooms_file):
    """Add large capacity labs for practical courses."""
    print("Adding large capacity labs...")
    
    # Read existing rooms
    df = pd.read_csv(rooms_file)
    
    # Add large labs
    large_labs = [
        ("LAB1", "Large Computer Lab", 120, "lab", "monday_08:00-18:00,tuesday_08:00-18:00,wednesday_08:00-18:00,thursday_08:00-18:00,friday_08:00-18:00"),
        ("LAB2", "Engineering Lab Complex", 150, "lab", "monday_08:00-18:00,tuesday_08:00-18:00,wednesday_08:00-18:00,thursday_08:00-18:00,friday_08:00-18:00"),
        ("LAB3", "Electronics Lab", 100, "lab", "monday_08:00-18:00,tuesday_08:00-18:00,wednesday_08:00-18:00,thursday_08:00-18:00,friday_08:00-18:00"),
        ("LAB4", "Multi-purpose Lab", 200, "lab", "monday_08:00-18:00,tuesday_08:00-18:00,wednesday_08:00-18:00,thursday_08:00-18:00,friday_08:00-18:00"),
        ("LAB5", "Workshop Lab", 180, "lab", "monday_08:00-18:00,tuesday_08:00-18:00,wednesday_08:00-18:00,thursday_08:00-18:00,friday_08:00-18:00"),
    ]
    
    # Create new rows for large labs
    new_rows = []
    for lab_data in large_labs:
        new_row = {
            'room_id': lab_data[0],
            'name': lab_data[1],
            'capacity': lab_data[2],
            'type': lab_data[3],
            'available_slots': lab_data[4]
        }
        new_rows.append(new_row)
    
    # Add to dataframe
    new_df = pd.DataFrame(new_rows)
    df = pd.concat([df, new_df], ignore_index=True)
    
    # Save the updated file
    backup_file = rooms_file.replace('.csv', '_backup.csv')
    if not os.path.exists(backup_file):
        df_original = pd.read_csv(rooms_file)
        df_original.to_csv(backup_file, index=False)
        print(f"Backup created: {backup_file}")
    
    df.to_csv(rooms_file, index=False)
    print(f"Updated rooms file: {rooms_file}")
    
    return df

def add_huge_lecture_halls(rooms_file):
    """Add huge lecture halls for very large classes."""
    print("Adding huge lecture halls...")
    
    # Read existing rooms
    df = pd.read_csv(rooms_file)
    
    # Add very large lecture halls
    huge_halls = [
        ("MEGA1", "Main Auditorium", 350, "lecture", "monday_08:00-18:00,tuesday_08:00-18:00,wednesday_08:00-18:00,thursday_08:00-18:00,friday_08:00-18:00"),
        ("MEGA2", "Convention Center", 400, "lecture", "monday_08:00-18:00,tuesday_08:00-18:00,wednesday_08:00-18:00,thursday_08:00-18:00,friday_08:00-18:00"),
        ("MEGA3", "Grand Hall", 300, "lecture", "monday_08:00-18:00,tuesday_08:00-18:00,wednesday_08:00-18:00,thursday_08:00-18:00,friday_08:00-18:00"),
    ]
    
    # Create new rows for huge halls
    new_rows = []
    for hall_data in huge_halls:
        new_row = {
            'room_id': hall_data[0],
            'name': hall_data[1],
            'capacity': hall_data[2],
            'type': hall_data[3],
            'available_slots': hall_data[4]
        }
        new_rows.append(new_row)
    
    # Add to dataframe
    new_df = pd.DataFrame(new_rows)
    df = pd.concat([df, new_df], ignore_index=True)
    
    # Save the updated file
    backup_file = rooms_file.replace('.csv', '_backup.csv')
    if not os.path.exists(backup_file):
        df_original = pd.read_csv(rooms_file)
        df_original.to_csv(backup_file, index=False)
        print(f"Backup created: {backup_file}")
    
    df.to_csv(rooms_file, index=False)
    print(f"Updated rooms file: {rooms_file}")
    
    return df

def main():
    """Main function to fix all validation errors."""
    print("=" * 50)
    print("GENETICS TIMETABLING DATA FIX SCRIPT")
    print("=" * 50)
    
    # Define file paths
    base_dir = Path("data")
    courses_file = base_dir / "sample_courses.csv"
    instructors_file = base_dir / "sample_instructors.csv"
    rooms_file = base_dir / "sample_rooms.csv"
    groups_file = base_dir / "sample_groups.csv"
    
    # Check if files exist
    for file_path in [courses_file, instructors_file, rooms_file, groups_file]:
        if not file_path.exists():
            print(f"ERROR: File not found: {file_path}")
            return
    
    try:
        # Fix room time slots
        fix_room_time_slots(str(rooms_file))
        
        # Add missing courses
        add_missing_courses(str(courses_file))
        
        # Add large capacity rooms
        add_large_capacity_rooms(str(rooms_file))
        
        # Clean instructor qualifications
        clean_instructor_qualifications(str(instructors_file))
        
        # Fix instructor qualifications to match course requirements
        fix_instructor_qualifications(str(instructors_file))
        
        # Fix group enrollments to match course requirements
        fix_group_enrollments(str(groups_file))
        
        # Add large capacity labs
        add_large_labs(str(rooms_file))
        
        # Add huge lecture halls
        add_huge_lecture_halls(str(rooms_file))
        
        print("\n" + "=" * 50)
        print("✅ DATA FIX COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("\nBackup files created with '_backup.csv' suffix")
        print("You can now run the main timetabling system.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("Please check the error message and try again.")

if __name__ == "__main__":
    main()
