from fastapi import FastAPI
from app.routes import assistant
from app.routes import student

app = FastAPI()
app.include_router(assistant.router)
app.include_router(student.router)


@app.get("/")
def root():
    return {"message": "Assistant Auth API Running"}
