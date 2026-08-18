import os
import jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from routers.user import router as user_router
from routers.product import router as product_router


app = FastAPI()

# Load environment variables
load_dotenv()

secret_key = os.getenv('SECRET_KEY', "default")
if secret_key == 'default':
    raise ValueError("SECRET_KEY environment variable is not set")

algo = os.getenv('ALGORITHM', 'default')
if algo == 'default':
    raise ValueError("ALGORITHM environment variable is not set")


app.include_router(user_router)
app.include_router(product_router)


fake_user = {
    "username": "goofy",
    "password": "secret123"
}

def create_access_token(username: str):
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    payload = {
        "sub": username,
        "exp": expires
    }
    
    token = jwt.encode(
        payload=payload,
        key=secret_key,
        algorithm=algo
    )
    
    return token
    


@app.get("/")
def root():
    return {
        "message": "This is root"
    }

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm)
):
    if form_data.username != fake_user["username"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if form_data.password != fake_user["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    token = create_access_token(form_data.username)
    
    return {
        "access_token": token,
        "token_type": "bearer"
    }

