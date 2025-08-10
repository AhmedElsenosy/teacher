"""
Test script to verify all 3 archive scenarios
This script simulates different payment patterns and tests the archive logic
"""

import asyncio
from datetime import datetime, timedelta
from app.database import student_collection, archived_student_collection
from app.routes.archive import archive_unpaid_students, get_month_key

async def setup_test_student(student_data):
    """Insert a test student into the database"""
    result = await student_collection.insert_one(student_data)
    return result.inserted_id

async def simulate_payment(student_id, month_key):
    """Simulate a payment for a specific month"""
    await student_collection.update_one(
        {"student_id": student_id},
        {
            "$set": {
                f"subscription.monthsales.{month_key}": 100.0  # Simulate payment amount
            }
        }
    )

async def get_student_status(student_id):
    """Get current status of a student"""
    # Check active students
    active_student = await student_collection.find_one({"student_id": student_id})
    if active_student:
        return {
            "status": "active",
            "months_without_payment": active_student.get("months_without_payment", 0),
            "subscription": active_student.get("subscription", {})
        }
    
    # Check archived students
    archived_student = await archived_student_collection.find_one({"student_id": student_id})
    if archived_student:
        return {
            "status": "archived",
            "months_without_payment": archived_student.get("months_without_payment", 0),
            "archive_reason": archived_student.get("archive_reason", ""),
            "archived_at": archived_student.get("archived_at")
        }
    
    return {"status": "not_found"}

async def cleanup_test_students():
    """Clean up test students"""
    test_student_ids = [9991, 9992, 9993]
    for student_id in test_student_ids:
        await student_collection.delete_one({"student_id": student_id})
        await archived_student_collection.delete_one({"student_id": student_id})

async def test_scenario_1_consecutive_non_payment():
    """Test Scenario 1: Student stops paying consecutively"""
    print("\n" + "="*60)
    print("SCENARIO 1: Student stops paying consecutively")
    print("="*60)
    
    student_id = 9991
    test_student = {
        "student_id": student_id,
        "first_name": "Test",
        "last_name": "Student1",
        "email": "test1@example.com",
        "phone_number": "1234567890",
        "guardian_number": "0987654321",
        "birth_date": datetime(2000, 1, 1),
        "national_id": "12345678901",
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
    
    await setup_test_student(test_student)
    print(f"✅ Created test student {student_id}")
    
    # Get current and previous months
    today = datetime.now()
    current_month = get_month_key(today)
    last_month = get_month_key(today.replace(day=1) - timedelta(days=1))
    
    print(f"Current month: {current_month}")
    print(f"Last month: {last_month}")
    
    # Initial status
    status = await get_student_status(student_id)
    print(f"Initial status: {status}")
    
    # Run archive check - Month 1 without payment
    print("\n--- Month 1: No payment ---")
    await archive_unpaid_students()
    status = await get_student_status(student_id)
    print(f"After Month 1: {status}")
    
    # Simulate moving to next month by adding a payment to an older month
    # This simulates the student not paying for 2 consecutive months
    older_month = get_month_key(today.replace(day=1) - timedelta(days=62))  # 2 months ago
    await simulate_payment(student_id, older_month)
    
    print("\n--- Month 2: Still no payment (consecutive) ---")
    await archive_unpaid_students()
    status = await get_student_status(student_id)
    print(f"After Month 2: {status}")
    
    if status["status"] == "archived":
        print("✅ SCENARIO 1 PASSED: Student archived after 2 consecutive months without payment")
    else:
        print("❌ SCENARIO 1 FAILED: Student should be archived")

async def test_scenario_2_irregular_payment():
    """Test Scenario 2: Student pays irregularly"""
    print("\n" + "="*60)
    print("SCENARIO 2: Student pays irregularly")
    print("="*60)
    
    student_id = 9992
    test_student = {
        "student_id": student_id,
        "first_name": "Test",
        "last_name": "Student2",
        "email": "test2@example.com",
        "phone_number": "1234567891",
        "guardian_number": "0987654322",
        "birth_date": datetime(2000, 1, 1),
        "national_id": "12345678902",
        "gender": "female",
        "level": 2,
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
    
    await setup_test_student(test_student)
    print(f"✅ Created test student {student_id}")
    
    today = datetime.now()
    current_month = get_month_key(today)
    last_month = get_month_key(today.replace(day=1) - timedelta(days=1))
    
    # Step 1: No payment this month
    print(f"\n--- Step 1: No payment for {current_month} ---")
    await archive_unpaid_students()
    status = await get_student_status(student_id)
    print(f"Status: {status}")
    
    # Step 2: Simulate payment for last month (resets counter)
    print(f"\n--- Step 2: Make payment for {last_month} ---")
    await simulate_payment(student_id, last_month)
    await archive_unpaid_students()
    status = await get_student_status(student_id)
    print(f"Status after payment: {status}")
    
    # Step 3: Still no payment for current month (but paid last month, so counter = 1)
    print(f"\n--- Step 3: Still no payment for {current_month}, but paid {last_month} ---")
    await archive_unpaid_students()
    status = await get_student_status(student_id)
    print(f"Status: {status}")
    
    # Step 4: Remove the payment for last month to simulate 2 consecutive months without payment
    print(f"\n--- Step 4: Remove last month payment (simulating 2 consecutive months without payment) ---")
    await student_collection.update_one(
        {"student_id": student_id},
        {"$unset": {f"subscription.monthsales.{last_month}": ""}}
    )
    
    # Now when we run archive check, student will have:
    # - No payment for current month (2025-07)
    # - No payment for last month (2025-06) 
    # This should trigger archiving
    await archive_unpaid_students()
    status = await get_student_status(student_id)
    print(f"Final status: {status}")
    
    if status["status"] == "archived":
        print("✅ SCENARIO 2 PASSED: Student archived after 2 consecutive months without payment (even with irregular payments)")
    else:
        print("❌ SCENARIO 2 FAILED: Student should be archived")

async def test_scenario_3_regular_payment():
    """Test Scenario 3: Student pays regularly"""
    print("\n" + "="*60)
    print("SCENARIO 3: Student pays regularly")
    print("="*60)
    
    student_id = 9993
    test_student = {
        "student_id": student_id,
        "first_name": "Test",
        "last_name": "Student3",
        "email": "test3@example.com",
        "phone_number": "1234567892",
        "guardian_number": "0987654323",
        "birth_date": datetime(2000, 1, 1),
        "national_id": "12345678903",
        "gender": "male",
        "level": 3,
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
    
    await setup_test_student(test_student)
    print(f"✅ Created test student {student_id}")
    
    today = datetime.now()
    current_month = get_month_key(today)
    last_month = get_month_key(today.replace(day=1) - timedelta(days=1))
    
    # Make payments for both months
    print(f"\n--- Making payments for {last_month} and {current_month} ---")
    await simulate_payment(student_id, last_month)
    await simulate_payment(student_id, current_month)
    
    # Run archive check multiple times
    for i in range(3):
        print(f"\n--- Archive check #{i+1} ---")
        await archive_unpaid_students()
        status = await get_student_status(student_id)
        print(f"Status: {status}")
    
    if status["status"] == "active":
        print("✅ SCENARIO 3 PASSED: Student remains active with regular payments")
    else:
        print("❌ SCENARIO 3 FAILED: Student should remain active")

async def main():
    """Run all test scenarios"""
    print("🧪 STARTING ARCHIVE SYSTEM TESTS")
    print("This will test all 3 scenarios for the archive system")
    
    # Clean up any existing test data
    await cleanup_test_students()
    
    try:
        # Test all scenarios
        await test_scenario_1_consecutive_non_payment()
        await test_scenario_2_irregular_payment()
        await test_scenario_3_regular_payment()
        
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print("All scenarios have been tested!")
        print("Check the results above to see if each scenario passed.")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test data
        print("\n🧹 Cleaning up test data...")
        await cleanup_test_students()
        print("✅ Cleanup complete")

if __name__ == "__main__":
    asyncio.run(main())
