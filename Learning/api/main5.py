from fastapi import FastAPI, Depends, Header
from pydantic import BaseModel
from typing import Any

app = FastAPI()

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
    return "Database connection established"

@app.get("/current_user")
def get_current_user(db = Depends(get_db)):
    return db + "and current user extracted"

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
def get_products(pagenation = Depends(get_pagination)):
    return pagenation
