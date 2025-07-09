#!/usr/bin/env python3

"""
Simple debug script to check what's happening with violations data.
"""

import sys
sys.path.append('src')

# Try to determine the issue with minimal imports
def test_comparison():
    """Test comparison operations that might be causing the issue."""
    
    # Test what happens when we compare different data types
    test_dict = {'hard': {'no_conflict': 5, 'room_capacity': 10}, 'soft': {'preference': 3}}
    test_int = 5
    
    print(f"Test dict: {test_dict}")
    print(f"Test int: {test_int}")
    
    # This would cause the error
    try:
        result = test_dict > test_int
        print(f"Dict > int: {result}")
    except TypeError as e:
        print(f"Error comparing dict > int: {e}")
    
    # Test flattening
    flat_dict = {}
    flat_dict.update(test_dict.get('hard', {}))
    flat_dict.update(test_dict.get('soft', {}))
    print(f"Flattened dict: {flat_dict}")
    
    # Test if flattened dict values are correct
    for key, value in flat_dict.items():
        print(f"Key: {key}, Value: {value}, Type: {type(value)}")
        if isinstance(value, dict):
            print(f"  WARNING: Value is still a dict: {value}")

if __name__ == "__main__":
    test_comparison()
