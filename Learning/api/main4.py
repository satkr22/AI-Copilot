from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field

app = FastAPI()

# request model
class CreateUser(BaseModel):
    user_name: str = Field(min_length=3, max_length=15)
    age: int = Field(ge=18)

# response model
class UserResponse(BaseModel):
    name: str
    id: int

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
        "name": "Satkr"
    }

@app.get("/products")
def get_products(page_no: int = Query(ge = 1, le=100)):
    return {
        "Page number": page_no
    }