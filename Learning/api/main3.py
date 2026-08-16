from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# request body model for products
class Product(BaseModel):
    title: str
    price: float
    stock: int

# request body model for users
class User(BaseModel):
    name: str
    age: int

# response model
class UserResponse(BaseModel):
    name: str

@app.get("/")
def root():
    return {"message": "this is root"}
    
@app.post("/products")
def create_product(product: Product):
    return product


@app.get("/users_id", response_model=UserResponse)
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
    

@app.post("/users", response_model=UserResponse)
def get_users(user: User):
    return {
        "name": user.name,
        "age": user.age
    }