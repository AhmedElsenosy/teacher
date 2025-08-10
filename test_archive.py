"""
Test script to verify archive functionality
This script demonstrates how the archive system works
"""

import asyncio
from app.database import student_collection, archived_student_collection
from app.routes.archive import move_student_to_archive, restore_student_from_archive

async def test_archive_functionality():
    print("=== Archive System Test ===")
    
    # Check if there are any students in the main collection
    student_count = await student_collection.count_documents({})
    archived_count = await archived_student_collection.count_documents({})
    
    print(f"Current active students: {student_count}")
    print(f"Current archived students: {archived_count}")
    
    if student_count == 0:
        print("No students found to test archiving. Please add some students first.")
        return
    
    # Get the first student for testing
    first_student = await student_collection.find_one()
    if first_student:
        student_id = first_student.get("student_id")
        print(f"\nTesting with student ID: {student_id}")
        print(f"Student name: {first_student.get('first_name')} {first_student.get('last_name')}")
        
        # Archive the student
        try:
            print("\n--- Archiving student ---")
            archived_student = await move_student_to_archive(student_id, "Testing archive functionality")
            print(f"✅ Student {student_id} archived successfully")
            print(f"Archive reason: {archived_student.get('archive_reason')}")
            
            # Check collections
            new_student_count = await student_collection.count_documents({})
            new_archived_count = await archived_student_collection.count_documents({})
            print(f"Active students after archiving: {new_student_count}")
            print(f"Archived students after archiving: {new_archived_count}")
            
            # Restore the student
            print("\n--- Restoring student ---")
            restored_student = await restore_student_from_archive(student_id)
            print(f"✅ Student {student_id} restored successfully")
            
            # Check collections again
            final_student_count = await student_collection.count_documents({})
            final_archived_count = await archived_student_collection.count_documents({})
            print(f"Active students after restoring: {final_student_count}")
            print(f"Archived students after restoring: {final_archived_count}")
            
        except Exception as e:
            print(f"❌ Error during testing: {str(e)}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_archive_functionality())
