from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ---------- Register Request ----------

class UserRegister(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=100)
    
    
# ---------- Login Request ----------

class UserLogin(BaseModel):
    email: EmailStr


# ---------- Response ----------

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}
    

class LoginResponse(BaseModel):
    access_token: str
    user: UserResponse