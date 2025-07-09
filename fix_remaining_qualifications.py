#!/usr/bin/env python3
"""
Fix remaining instructor qualification issues.
"""

import pandas as pd
import os
import sys

def fix_remaining_instructor_qualifications():
    """Fix the remaining instructor qualification issues."""
    print("Fixing remaining instructor qualifications...")
    
    # Read the instructor data
    instructors_df = pd.read_csv("data/sample_instructors.csv")
    
    # Fix missing qualifications
    missing_qualifications = [
        ("80", "ENAR 251"),
        ("82", "ENCE 256"),
        ("84", "ENIE 254")
    ]
    
    for instructor_id, course_id in missing_qualifications:
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
    
    # Save the updated data
    instructors_df.to_csv("data/sample_instructors.csv", index=False)
    print("Updated instructor qualifications saved.")

if __name__ == "__main__":
    fix_remaining_instructor_qualifications()
    print("✅ Remaining instructor qualifications fixed!")
