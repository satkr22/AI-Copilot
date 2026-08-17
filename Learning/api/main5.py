from fastapi import FastAPI, Depends, Header
from pydantic import BaseModel
from typing import Any

app = FastAPI()


class Pagination:
    def __init__(
        self,
        limit: int = 20,
        offset: int = 0
        ):
        self.limit = limit
        self.offset = offset
        

def get_pagination(limit: int = 10, offset: int = 0):
    if limit > 100:
        limit = 100

    return {
        "limit": limit,
        "offset": offset
    }

@app.get("/")
def root():
    return {
        "message": "This is root"
    }
    
def get_db():
    print("1. resourse created")
    try:
        yield "Database connection established"
    finally:
        print("3. resource destroyed")

@app.get("/current_user")
def get_current_user(db = Depends(get_db)):
    print("2. endpoint executed")
    raise ValueError("Just an error for testing")
    # return db + "and current user extracted"

@app.get("/users")
def get_users(user = Depends(get_current_user), header_text = Header()):
    return {
        "user": user,
        "header": header_text
    }

@app.get("/orders")
def get_orders(pagenation = Depends(get_pagination)):
    return pagenation

@app.get("/products")
def get_products(pagenation = Depends(Pagination)):
    return {
        "limit": pagenation.limit,
        "offset": pagenation.offset
    }

def fake_current_user():
    return "FAKE USER"

# Dependency override
app.dependency_overrides[get_current_user] = fake_current_user