"""
Manual Test Script for Archive Scenarios
Run this step by step to test each scenario manually
"""

import asyncio
from datetime import datetime, timedelta
from app.database import student_collection, archived_student_collection
from app.routes.archive import archive_unpaid_students, get_month_key

async def create_test_student():
    """Create a test student for manual testing"""
    student_id = 8888
    
    # Clean up any existing test student
    await student_collection.delete_one({"student_id": student_id})
    await archived_student_collection.delete_one({"student_id": student_id})
    
    test_student = {
        "student_id": student_id,
        "first_name": "Test",
        "last_name": "Archive",
        "email": "test@archive.com",
        "phone_number": "1234567890",
        "guardian_number": "0987654321",
        "birth_date": datetime(2000, 1, 1),
        "national_id": "12345678888",
        "gender": "male",
        "level": 1,
        "school_name": "Test School",
        "is_subscription": True,
        "created_at": datetime.utcnow(),
        "exams": [],
        "uid": student_id,
        "attendance": {},
        "subscription": {"monthsales": {}},
        "months_without_payment": 0,
        "archived": False
    }
    
    await student_collection.insert_one(test_student)
    print(f"✅ Created test student with ID: {student_id}")
    return student_id

async def check_student_status(student_id):
    """Check if student is active or archived"""
    active = await student_collection.find_one({"student_id": student_id})
    archived = await archived_student_collection.find_one({"student_id": student_id})
    
    if active:
        months_without_payment = active.get("months_without_payment", 0)
        payments = active.get("subscription", {}).get("monthsales", {})
        print(f"📊 Student {student_id} Status: ACTIVE")
        print(f"   - Months without payment: {months_without_payment}")
        print(f"   - Payments: {payments}")
        return "active"
    elif archived:
        print(f"📊 Student {student_id} Status: ARCHIVED")
        print(f"   - Archive reason: {archived.get('archive_reason', 'N/A')}")
        print(f"   - Archived at: {archived.get('archived_at', 'N/A')}")
        return "archived"
    else:
        print(f"📊 Student {student_id} Status: NOT FOUND")
        return "not_found"

async def add_payment(student_id, month_offset=0):
    """Add payment for a specific month (0=current, -1=last month, etc.)"""
    today = datetime.now()
    target_date = today.replace(day=1) + timedelta(days=32*month_offset)  # Move by months
    target_date = target_date.replace(day=1)  # First day of target month
    month_key = get_month_key(target_date)
    
    await student_collection.update_one(
        {"student_id": student_id},
        {
            "$set": {
                f"subscription.monthsales.{month_key}": 100.0
            }
        }
    )
    print(f"💰 Added payment for {month_key}")

async def run_archive_check():
    """Run the archive check function"""
    print("🔍 Running archive check...")
    await archive_unpaid_students()
    print("✅ Archive check complete")

async def scenario_1():
    """Test Scenario 1: Consecutive non-payment"""
    print("\n" + "="*50)
    print("SCENARIO 1: Consecutive Non-Payment Test")
    print("="*50)
    
    student_id = await create_test_student()
    
    print("\n--- Initial State ---")
    await check_student_status(student_id)
    
    print("\n--- Month 1: No payment ---")
    await run_archive_check()
    await check_student_status(student_id)
    
    print("\n--- Month 2: Still no payment ---")
    await run_archive_check()
    status = await check_student_status(student_id)
    
    if status == "archived":
        print("✅ PASSED: Student archived after 2 months without payment")
    else:
        print("❌ FAILED: Student should be archived")
    
    return student_id

async def scenario_2():
    """Test Scenario 2: Irregular payment"""
    print("\n" + "="*50)
    print("SCENARIO 2: Irregular Payment Test")
    print("="*50)
    
    student_id = await create_test_student()
    
    print("\n--- Initial State ---")
    await check_student_status(student_id)
    
    print("\n--- Month 1: No payment ---")
    await run_archive_check()
    await check_student_status(student_id)
    
    print("\n--- Make payment for last month ---")
    await add_payment(student_id, -1)  # Pay for last month
    await run_archive_check()
    await check_student_status(student_id)
    
    print("\n--- Still no payment for current month (but paid last month) ---")
    await run_archive_check()
    await check_student_status(student_id)
    
    # Manually set months_without_payment to 2 to simulate another month passing
    await student_collection.update_one(
        {"student_id": student_id},
        {"$set": {"months_without_payment": 2}}
    )
    
    print("\n--- Simulate another month without payment ---")
    await run_archive_check()
    status = await check_student_status(student_id)
    
    if status == "archived":
        print("✅ PASSED: Student archived after 2 consecutive months without payment (with irregular payments)")
    else:
        print("❌ FAILED: Student should be archived")
    
    return student_id

async def scenario_3():
    """Test Scenario 3: Regular payment"""
    print("\n" + "="*50)
    print("SCENARIO 3: Regular Payment Test")
    print("="*50)
    
    student_id = await create_test_student()
    
    print("\n--- Initial State ---")
    await check_student_status(student_id)
    
    print("\n--- Add payments for current and last month ---")
    await add_payment(student_id, 0)   # Current month
    await add_payment(student_id, -1)  # Last month
    
    print("\n--- Run multiple archive checks ---")
    for i in range(3):
        print(f"\n--- Archive Check #{i+1} ---")
        await run_archive_check()
        status = await check_student_status(student_id)
    
    if status == "active":
        print("✅ PASSED: Student remains active with regular payments")
    else:
        print("❌ FAILED: Student should remain active")
    
    return student_id

async def cleanup_test_data():
    """Clean up all test data"""
    test_ids = [8888]
    for student_id in test_ids:
        await student_collection.delete_one({"student_id": student_id})
        await archived_student_collection.delete_one({"student_id": student_id})
    print("🧹 Test data cleaned up")

async def main():
    """Main test function"""
    print("🧪 MANUAL ARCHIVE TESTING")
    print("This script will test all 3 scenarios step by step")
    
    try:
        await scenario_1()
        await scenario_2() 
        await scenario_3()
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS COMPLETED!")
        print("="*50)
        print("Check the results above to see if each scenario worked correctly.")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await cleanup_test_data()

# Individual test functions you can run separately
async def test_current_months():
    """Show current and last month keys"""
    today = datetime.now()
    current_month = get_month_key(today)
    last_month = get_month_key(today.replace(day=1) - timedelta(days=1))
    
    print(f"Current month key: {current_month}")
    print(f"Last month key: {last_month}")

if __name__ == "__main__":
    # You can run the full test or individual functions
    print("Choose what to run:")
    print("1. Full test (all scenarios)")
    print("2. Show current months")
    print("3. Create test student only")
    print("4. Check existing test student")
    
    import sys
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("Enter choice (1-4): ")
    
    if choice == "1":
        asyncio.run(main())
    elif choice == "2":
        asyncio.run(test_current_months())
    elif choice == "3":
        asyncio.run(create_test_student())
    elif choice == "4":
        asyncio.run(check_student_status(8888))
    else:
        print("Running full test...")
        asyncio.run(main())
