import asyncio
import json

BASE_URL = "http://localhost:8000"

async def test_blacklist():
    """Test the blacklist functionality"""
    print("Testing Blacklist Functionality")
    print("=" * 50)
    
    # Note: You'll need to have the server running and be authenticated
    # This is just a demonstration of the API endpoints
    
    # Sample student ObjectId (you'll need to replace with actual ObjectId from your database)
    sample_student_id = "6885e54dfedee5eb77791ea8"
    
    print("Available Blacklist Endpoints:")
    print("-" * 30)
    
    print("1. Add student to blacklist:")
    print(f"POST {BASE_URL}/blacklist/add-student")
    print("Body:", json.dumps({
        "student_object_id": sample_student_id,
        "blacklist_reason": "Inappropriate behavior"
    }, indent=2))
    print()
    
    print("2. Get all blacklisted students:")
    print(f"GET {BASE_URL}/blacklist/")
    print()
    
    print("3. Get specific blacklisted student details:")
    print(f"GET {BASE_URL}/blacklist/{{blacklist_id}}")
    print()
    
    print("4. Remove student from blacklist (restore to students):")
    print(f"DELETE {BASE_URL}/blacklist/remove-student/{{blacklist_id}}")
    print()
    
    print("Features:")
    print("- When adding to blacklist: Student is MOVED from 'students' to 'blacklist' collection")
    print("- All student data is preserved (exams, attendance, subscription history, etc.)")
    print("- When removing from blacklist: Student is RESTORED to 'students' collection")
    print("- Prevents duplicates and handles edge cases")

if __name__ == "__main__":
    asyncio.run(test_blacklist())
