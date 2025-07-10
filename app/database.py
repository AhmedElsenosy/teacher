from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config

MONGO_URI = config("MONGO_URI")
DATABASE_NAME = config("DATABASE_NAME")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
