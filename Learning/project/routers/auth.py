import os
import jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from schemas import UserCreate, UserLogin
from utils.password import hash_password, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

load_dotenv()

secret_key = os.getenv('SECRET_KEY', "default")
if secret_key == 'default':
    raise ValueError("SECRET_KEY environment variable is not set")

algo = os.getenv('ALGORITHM', 'default')
if algo == 'default':
    raise ValueError("ALGORITHM environment variable is not set")



fake_user_db = []

def get_user(username: str):
    for user in fake_user_db:
        if user["username"] == username:
            return user

    return None

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


@router.post("/register")
def register(user: UserCreate):
    hashed_password = hash_password(user.password)
    
    new_user = {
        "username": user.username,
        "password_hash": hashed_password
    }
    
    fake_user_db.append(new_user)
    print(fake_user_db)
    
    return {
        "message": "User registered successfully!!"
    }

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm)
):
    
    stored_user = get_user(form_data.username)
    
    if stored_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials"
        )
    
    if not verify_password(
        password=form_data.password,
        hashed_password=stored_user["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials"
        )
        
    token = create_access_token(form_data.username)
    
    return {
        "access_token": token,
        "token_type": "bearer"
    }
        
