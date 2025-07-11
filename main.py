from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.routes import assistant
from app.routes import student
from app.routes import course
from app.routes import exam
from app.models.exam import ExamModel
from app.config import settings
from fastapi.staticfiles import StaticFiles
import os




app = FastAPI()

@app.on_event("startup")
async def app_init():
    client = AsyncIOMotorClient(settings.MONGO_URI)  
    db = client[settings.DATABASE_NAME]             

    await init_beanie(
        database=db,
        document_models=[
            ExamModel,
        ]
    )


app.mount(
    "/solutions",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "upload/solutions")),
    name="solutions"
)


app.include_router(assistant.router)
app.include_router(student.router)
app.include_router(course.router)
app.include_router(exam.router)


@app.get("/")
def root():
    return {"message": "Assistant Auth API Running"}
