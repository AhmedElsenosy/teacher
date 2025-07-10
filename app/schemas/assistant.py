from pydantic import BaseModel, Field, validator

class AssistantRegister(BaseModel):
    name: str
    password: str
    confirm_password: str

    @validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

class AssistantLogin(BaseModel):
    name: str
    password: str

class AssistantOut(BaseModel):
    name: str
