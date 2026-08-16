from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# request body model
class Product(BaseModel):
    title: str
    price: float
    stock: int

# response model
class UserResponse(BaseModel):
    id: int
    name: str
    age: int

@app.get("/")
def root():
    return {"message": "this is root"}
    
@app.post("/products")
def create_product(product: Product):
    return product


@app.get("/users", response_model=UserResponse)
def get_users_id():
    return {
        "id": 1,
        "name": "boss",
        "age": 23,
        "password": "12345@"
    }
    
    
@app.get("/users_list", response_model=list[UserResponse])
def get_users_list():
    return [
        {
            "id": 2,
            "name": "boss",
            "age": 23,
            "password": "12345@"
        },
        {
            "id": 3,
            "name": "satkr",
            "age": 23,
            "password": "12$45@"
        }
            
    ]
    