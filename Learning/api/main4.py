from typing import Any
from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field, field_validator

app = FastAPI()

# request model
class CreateUser(BaseModel):
    username: str = Field(min_length=3, max_length=15, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=7, max_length=30)
    age: int = Field(ge=18)
    
    @field_validator("username")
    @classmethod
    def validate_userame(cls, value: str):
        if " " in value:
            raise ValueError("Username cannot contain space")
        return value
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        if not any(char.isupper() for char in value):
            raise ValueError("Password should has atleast one upper case character")
        
        if not any(char.isdigit() for char in value):
            raise ValueError("Password should has atleast one number")
        
        if not any(char in value for char in ["@", "#", "$", "&", "_"]):
            raise ValueError("Password should has atleast one special character")
    
# response model
class UserResponse(BaseModel):
    name: str
    id: int
    
# response model
class CreateUserResponse(BaseModel):
    username: str
    age: int

@app.get("/")
def root():
    return {
        "message": "This is root"
    }
    
@app.get("/users/{user_id}", response_model=UserResponse, status_code=200)
def get_users(user_id: int = Path(ge=1)):
    if user_id > 10:
        raise HTTPException(
            status_code=404,
            detail="user not found"
        )
        
    return {
        "id": user_id,
    }
    
@app.post("/create_user", response_model=CreateUserResponse, status_code=201)
def create_user(user: CreateUser):
    return {
        "username": user.username,
        "age": user.age,
        "password_raw": user.password
    }

@app.get("/products")
def get_products(page_no: int = Query(ge = 1, le=100)):
    return {
        "Page number": page_no
    }