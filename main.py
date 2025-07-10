from fastapi import FastAPI
from app.routes import assistant

app = FastAPI()
app.include_router(assistant.router)

@app.get("/")
def root():
    return {"message": "Assistant Auth API Running"}
