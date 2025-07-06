"""
Quick test script to verify the system is working correctly.
This tests basic functionality without full optimization.
"""

import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules can be imported correctly."""
    print("Testing imports...")
    
    try:
        from src.entities import Course, Instructor, Room, Group
        print("✅ Entity imports OK")
        
        from src.ga import Chromosome, Gene, Population, GeneticOperators, GAEngine
        print("✅ GA module imports OK")
        
        from src.constraints import ConstraintChecker, HardConstraintChecker, SoftConstraintChecker
        print("✅ Constraint module imports OK")
        
        from src.fitness import FitnessEvaluator
        print("✅ Fitness module imports OK")
        
        from src.data import DataIngestion, DataValidator
        print("✅ Data module imports OK")
        
        from src.output import OutputGenerator
        print("✅ Output module imports OK")
        
        from src.utils import get_logger, setup_logging
        print("✅ Utility imports OK")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_entity_creation():
    """Test creation of basic entities."""
    print("\\nTesting entity creation...")
    
    try:
        from src.entities import Course, Instructor, Room, Group
        
        # Test Course creation
        course = Course(
            course_id="TEST101",
            name="Test Course",
            sessions_per_week=2,
            duration=90,
            required_room_type="lecture",
            group_ids=["1"],
            qualified_instructor_ids=["1"]
        )
        print("✅ Course creation OK")
        
        # Test Instructor creation
        instructor = Instructor(
            instructor_id="1",
            name="Test Instructor",
            qualified_courses=["TEST101"],
            available_slots={"monday": ["09:00-10:30"]},
            preferred_slots={"monday": ["09:00-10:30"]}
        )
        print("✅ Instructor creation OK")
        
        # Test Room creation
        room = Room(
            room_id="R1",
            name="Test Room",
            capacity=30,
            room_type="lecture",
            available_slots={"monday": ["09:00-10:30"]}
        )
        print("✅ Room creation OK")
        
        # Test Group creation
        group = Group(
            group_id="1",
            name="Test Group",
            student_count=25,
            enrolled_courses=["TEST101"]
        )
        print("✅ Group creation OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Entity creation error: {e}")
        return False

def test_ga_components():
    """Test GA component creation."""
    print("\\nTesting GA components...")
    
    try:
        from src.ga import Chromosome, Gene, Population, GeneticOperators
        
        # Test Gene creation
        gene = Gene(
            course_id="TEST101",
            instructor_id="1",
            room_id="R1",
            day="monday",
            time_slot="09:00-10:30",
            session_index=0
        )
        print("✅ Gene creation OK")
        
        # Test Chromosome creation
        chromosome = Chromosome([gene])
        print("✅ Chromosome creation OK")
        
        # Test Population creation
        population = Population(size=10)
        print("✅ Population creation OK")
        
        # Test GeneticOperators creation
        operators = GeneticOperators()
        print("✅ GeneticOperators creation OK")
        
        return True
        
    except Exception as e:
        print(f"❌ GA component error: {e}")
        return False

def test_data_files():
    """Test that sample data files exist and are readable."""
    print("\\nTesting data files...")
    
    data_dir = Path(__file__).parent / "data"
    print(f"Looking for data files in: {data_dir.absolute()}")
    
    files_to_check = [
        "sample_courses.csv",
        "sample_instructors.csv", 
        "sample_rooms.csv",
        "sample_groups.csv"
    ]
    
    all_exist = True
    for filename in files_to_check:
        file_path = data_dir / filename
        if file_path.exists():
            print(f"✅ {filename} exists")
        else:
            print(f"❌ {filename} missing at {file_path}")
            all_exist = False
    
    return all_exist

def run_all_tests():
    """Run all tests."""
    print("="*50)
    print("TIMETABLING SYSTEM - QUICK TESTS")
    print("="*50)
    
    tests = [
        ("Import Test", test_imports),
        ("Entity Creation Test", test_entity_creation),
        ("GA Components Test", test_ga_components),
        ("Data Files Test", test_data_files)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        emoji = "✅" if result else "❌"
        print(f"{emoji} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System appears to be working correctly.")
        print("\\nYou can now run the basic example:")
        print("  python examples/basic_example.py")
        return True
    else:
        print("⚠️  Some tests failed. Please check the installation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
