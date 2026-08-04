from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Product(BaseModel):
    title: str
    price: float
    stock: int
    
@app.get("/")
def root():
    return {"message": "this is root"}
    
@app.post("/products")
def create_product(product: Product):
    return product