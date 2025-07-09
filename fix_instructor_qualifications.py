#!/usr/bin/env python3
"""
Fix the specific instructor qualification issues.
"""

import pandas as pd
import os
import sys

def fix_instructor_qualifications():
    """Fix the specific instructor qualification issues."""
    print("Fixing instructor qualifications...")
    
    # Read the instructor data
    instructors_df = pd.read_csv("data/sample_instructors.csv")
    
    # Fix instructor 80 - add ENAR 251
    mask = instructors_df['instructor_id'] == 80
    if mask.any():
        current = instructors_df.loc[mask, 'qualified_courses'].iloc[0]
        if "ENAR 251" not in current:
            new_qualifications = f"{current},ENAR 251"
            instructors_df.loc[mask, 'qualified_courses'] = new_qualifications
            print(f"  Added ENAR 251 to instructor 80's qualifications")
    
    # Fix instructor 82 - add ENCE 256
    mask = instructors_df['instructor_id'] == 82
    if mask.any():
        current = instructors_df.loc[mask, 'qualified_courses'].iloc[0]
        if "ENCE 256" not in current:
            new_qualifications = f"{current},ENCE 256"
            instructors_df.loc[mask, 'qualified_courses'] = new_qualifications
            print(f"  Added ENCE 256 to instructor 82's qualifications")
    
    # Fix instructor 84 - add ENIE 254
    mask = instructors_df['instructor_id'] == 84
    if mask.any():
        current = instructors_df.loc[mask, 'qualified_courses'].iloc[0]
        if "ENIE 254" not in current:
            new_qualifications = f"{current},ENIE 254"
            instructors_df.loc[mask, 'qualified_courses'] = new_qualifications
            print(f"  Added ENIE 254 to instructor 84's qualifications")
    
    # Save the updated data
    instructors_df.to_csv("data/sample_instructors.csv", index=False)
    print("Updated instructor qualifications saved.")

if __name__ == "__main__":
    fix_instructor_qualifications()
    print("✅ Instructor qualifications fixed!")
