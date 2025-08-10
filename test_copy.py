from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Access your database and collection
db = client["teacher_app"]
collection = db["monthsales"]

# Aggregation pipeline
pipeline = [
    {
        "$group": {
            "_id": None,
            "total_price": {"$sum": "$price"},
            "total_default_price": {"$sum": "$default_price"}
        }
    }
]

# Run aggregation
result = list(collection.aggregate(pipeline))

# Print results
if result:
    print("Total price:", result[0]["total_price"])
    print("Total default price:", result[0]["total_default_price"])
else:
    print("No data found.")
