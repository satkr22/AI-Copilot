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
    name: str
    age: int

@app.get("/")
def root():
    return {"message": "this is root"}
    
@app.post("/products")
def create_product(product: Product):
    return product


@app.get("/users", response_model=UserResponse)
def get_users():
    return {
        "name": "boss",
        "age": 23,
        "password": "12345@"
    }