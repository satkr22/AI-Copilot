from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Any

app = FastAPI()

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
def get_users(user = Depends(get_current_user)):
    return user

