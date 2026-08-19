import os
import jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from routers.user import router as user_router
from routers.product import router as product_router
from routers.auth import router as auth_router


app = FastAPI()


app.include_router(user_router)
app.include_router(product_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "This is root"
    }

