from pymongo import MongoClient
from bson import ObjectId

client = MongoClient("mongodb://localhost:27017")
db = client["teacher_app"]
students = db["students"]

for student in students.find():
    updated_exams = []
    changed = False
    for exam in student.get("exams", []):
        # Only fix if old structure detected
        if isinstance(exam.get("exam_id"), ObjectId) or "student_degree" in exam:
            changed = True
            updated_exams.append({
                "exam_id": str(exam.get("exam_id")),
                "degree": exam.get("student_degree") or exam.get("degree"),
                "percentage": exam.get("degree_percentage") or exam.get("percentage"),
                "delivery_time": exam.get("delivery_time"),
                "solution_photo": exam.get("solution_photo"),
            })
        else:
            updated_exams.append(exam)
    if changed:
        students.update_one({"_id": student["_id"]}, {"$set": {"exams": updated_exams}})
print("Migration complete.")