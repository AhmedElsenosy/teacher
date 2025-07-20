from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.database import db
from app.schemas.assistant import AssistantRegister, AssistantLogin, AssistantOut
from app.utils.auth import hash_password, verify_password
from app.utils.jwt import create_access_token, decode_access_token
from datetime import timedelta

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter(prefix="/assistant", tags=["Assistant Auth"])
assistant_collection = db["assistants"]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="assistant/login")

@router.post("/register", response_model=AssistantOut)
async def register(data: AssistantRegister):
    existing = await assistant_collection.find_one({"name": data.name})
    if existing:
        raise HTTPException(status_code=400, detail="Assistant name already exists")

    hashed_pw = hash_password(data.password)

    new_assistant = {
        "name": data.name,
        "hashed_password": hashed_pw,
        "is_active": True
    }

    await assistant_collection.insert_one(new_assistant)
    return AssistantOut(name=data.name)
 


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    assistant = await assistant_collection.find_one({"name": form_data.username})
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")

    if not verify_password(form_data.password, assistant["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    payload = {
        "id": str(assistant["_id"]),
        "role": "assistant", 
        "sub": form_data.username, 
    }

    token = create_access_token(payload)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=AssistantOut)
async def get_me(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    assistant = await assistant_collection.find_one({"name": payload["sub"]})
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")

    return AssistantOut(name=assistant["name"])


@router.post("/logout")
async def logout():
    """
    Instruct the client to remove the token.
    """
    return {"message": "Logged out successfully. Please remove the token on the client side."}