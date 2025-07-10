from fastapi import FastAPI
from app.routes import assistant
from app.routes import student
from app.routes import course

app = FastAPI()
app.include_router(assistant.router)
app.include_router(student.router)
app.include_router(course.router)


@app.get("/")
def root():
    return {"message": "Assistant Auth API Running"}
