#!/usr/bin/env python3
"""
Final data integrity fix for the genetics timetabling system.
This script addresses all remaining cross-reference inconsistencies.
"""

import pandas as pd
import os
import sys

def fix_instructor_course_references(courses_df, instructors_df):
    """Fix instructor-course cross-references."""
    print("Fixing instructor-course cross-references...")
    
    # Fix courses that reference instructors not in instructor qualifications
    course_instructor_issues = [
        ("ENAR 251", "80"),
        ("ENAR 253-PR", "81"),
        ("ENCE 256", "82"),
        ("ENSH 251-PR", "83"),
        ("ENIE 254", "84")
    ]
    
    for course_id, instructor_id in course_instructor_issues:
        # Add course to instructor's qualifications
        instructor_mask = instructors_df['instructor_id'] == instructor_id
        if instructor_mask.any():
            current_qualifications = instructors_df.loc[instructor_mask, 'qualified_courses'].iloc[0]
            if pd.notna(current_qualifications):
                if course_id not in current_qualifications:
                    new_qualifications = f"{current_qualifications},{course_id}"
                    instructors_df.loc[instructor_mask, 'qualified_courses'] = new_qualifications
                    print(f"  Added {course_id} to instructor {instructor_id}'s qualifications")
            else:
                instructors_df.loc[instructor_mask, 'qualified_courses'] = course_id
                print(f"  Set {course_id} as instructor {instructor_id}'s qualification")
    
    # Fix instructors that reference courses not in course qualified_instructor_ids
    instructor_course_issues = [
        ("140", "ENAR 251"),
        ("140", "ENAR 253-PR"),
        ("141", "ENCE 256"),
        ("142", "ENSH 251-PR"),
        ("143", "ENIE 254")
    ]
    
    for instructor_id, course_id in instructor_course_issues:
        # Add instructor to course's qualified_instructor_ids
        course_mask = courses_df['course_id'] == course_id
        if course_mask.any():
            current_qualified = courses_df.loc[course_mask, 'qualified_instructor_ids'].iloc[0]
            if pd.notna(current_qualified):
                if instructor_id not in current_qualified:
                    new_qualified = f"{current_qualified},{instructor_id}"
                    courses_df.loc[course_mask, 'qualified_instructor_ids'] = new_qualified
                    print(f"  Added instructor {instructor_id} to course {course_id}'s qualified list")
            else:
                courses_df.loc[course_mask, 'qualified_instructor_ids'] = instructor_id
                print(f"  Set instructor {instructor_id} as qualified for course {course_id}")
    
    return courses_df, instructors_df

def fix_course_group_references(courses_df, groups_df):
    """Fix course-group cross-references."""
    print("Fixing course-group cross-references...")
    
    # Fix courses that reference groups not in group enrollments
    course_group_issues = [
        ("ENSH 154", "7"),
        ("ENSH 154", "8"),
        ("ENSH 154-PR", "7"),
        ("ENSH 154-PR", "8"),
        ("ENSH 242", "8"),
        ("ENSH 242", "10"),
        ("ENSH 156", "9"),
        ("ENSH 156", "10"),
        ("COMP 153-PR", "7"),
        ("ELEC 152-PR", "3"),
        ("ELEC 152-PR", "1"),
        ("ENEE 253", "2"),
        ("ENEE 253", "4"),
        ("ENEE 253-PR", "2"),
        ("ENEE 253-PR", "4"),
        ("ENEE 251", "2"),
        ("ENEE 251", "4"),
        ("ENAR 254-PR", "14")
    ]
    
    for course_id, group_id in course_group_issues:
        # Add course to group's enrolled_courses
        group_mask = groups_df['group_id'] == int(group_id)
        if group_mask.any():
            current_courses = groups_df.loc[group_mask, 'enrolled_courses'].iloc[0]
            if pd.notna(current_courses):
                if course_id not in current_courses:
                    new_courses = f"{current_courses},{course_id}"
                    groups_df.loc[group_mask, 'enrolled_courses'] = new_courses
                    print(f"  Added {course_id} to group {group_id}'s enrolled courses")
            else:
                groups_df.loc[group_mask, 'enrolled_courses'] = course_id
                print(f"  Set {course_id} as group {group_id}'s enrolled course")
    
    return courses_df, groups_df

def clean_duplicate_instructor_ids(courses_df):
    """Clean up duplicate instructor IDs in courses."""
    print("Cleaning duplicate instructor IDs...")
    
    duplicate_courses = ["ENSH 253", "ENME 253", "ENME 254"]
    
    for course_id in duplicate_courses:
        course_mask = courses_df['course_id'] == course_id
        if course_mask.any():
            current_qualified = courses_df.loc[course_mask, 'qualified_instructor_ids'].iloc[0]
            if pd.notna(current_qualified):
                # Remove duplicates while preserving order
                unique_ids = []
                for instructor_id in current_qualified.split(','):
                    instructor_id = instructor_id.strip()
                    if instructor_id not in unique_ids:
                        unique_ids.append(instructor_id)
                
                new_qualified = ','.join(unique_ids)
                courses_df.loc[course_mask, 'qualified_instructor_ids'] = new_qualified
                print(f"  Cleaned duplicates for course {course_id}: {new_qualified}")
    
    return courses_df

def main():
    # File paths
    courses_file = "data/sample_courses.csv"
    instructors_file = "data/sample_instructors.csv"
    groups_file = "data/sample_groups.csv"
    
    # Create backups
    if os.path.exists(courses_file):
        courses_df = pd.read_csv(courses_file)
        courses_df.to_csv(courses_file + ".backup", index=False)
        print(f"Created backup: {courses_file}.backup")
    else:
        print(f"Error: {courses_file} not found")
        return False
    
    if os.path.exists(instructors_file):
        instructors_df = pd.read_csv(instructors_file)
        instructors_df.to_csv(instructors_file + ".backup", index=False)
        print(f"Created backup: {instructors_file}.backup")
    else:
        print(f"Error: {instructors_file} not found")
        return False
    
    if os.path.exists(groups_file):
        groups_df = pd.read_csv(groups_file)
        groups_df.to_csv(groups_file + ".backup", index=False)
        print(f"Created backup: {groups_file}.backup")
    else:
        print(f"Error: {groups_file} not found")
        return False
    
    # Fix all data integrity issues
    courses_df, instructors_df = fix_instructor_course_references(courses_df, instructors_df)
    courses_df, groups_df = fix_course_group_references(courses_df, groups_df)
    courses_df = clean_duplicate_instructor_ids(courses_df)
    
    # Save the fixed data
    courses_df.to_csv(courses_file, index=False)
    instructors_df.to_csv(instructors_file, index=False)
    groups_df.to_csv(groups_file, index=False)
    
    print(f"\nFixed data saved to:")
    print(f"  {courses_file}")
    print(f"  {instructors_file}")
    print(f"  {groups_file}")
    
    return True

if __name__ == "__main__":
    if main():
        print("\n✅ Data integrity fix completed successfully!")
    else:
        print("\n❌ Data integrity fix failed!")
        sys.exit(1)
