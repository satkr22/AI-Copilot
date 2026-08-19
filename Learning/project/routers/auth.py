import os
import jwt
from uuid import uuid4
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordRequestForm
from utils.schemas import UserCreate, RefreshTokenRequest
from utils.password import hash_password, verify_password
from fastapi import APIRouter, HTTPException, Depends, status
from services.user_service import add_user, get_user, sessions


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





def create_access_token(username: str):
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    payload = {
        "sub": username,
        "type": "access",
        "exp": expires,
        "jti": str(uuid4())
    }
    
    token = jwt.encode(
        payload=payload,
        key=secret_key,
        algorithm=algo
    )
    
    return token


def create_refresh_token(username: str):
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    
    jti = str(uuid4())
    
    payload = {
        "sub": username,
        "type": "refresh",
        "exp": expires,
        "jti": jti
    }
    
    token = jwt.encode(
        payload=payload,
        key=secret_key,
        algorithm=algo
    )
    
    return token, jti


@router.post("/register")
def register(user: UserCreate):
    hashed_password = hash_password(user.password)
    
    new_user = {
        "username": user.username,
        "password_hash": hashed_password,
        "role": "user"
    }
    
    add_user(new_user=new_user)
    
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
        
    access_token = create_access_token(form_data.username)
    refresh_token, refresh_jti = create_refresh_token(form_data.username)
    
    sessions.append({
        "username": form_data.username,
        "refresh_token_jti": refresh_jti,
        "revoked": False
    })
    print(sessions)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
        
@router.post("/refresh")
def refresh(refresh_token: RefreshTokenRequest):
    try:
        payload = jwt.decode(
            jwt=refresh_token.refresh_token,
            key=secret_key,
            algorithms=[algo]
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        username = payload.get("sub")
        jti = payload.get("jti")
        if username is None or jti is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        user = get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
            
        session = None
        for s in sessions:
            if s["refresh_token_jti"] == jti:
                session = s
                break
        
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )
        
        if session["revoked"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session revoked"
            )
        
        new_access_token = create_access_token(username=username)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
        
@router.post("/logout")
def logout(refresh_token: RefreshTokenRequest):
    try:
        payload = jwt.decode(
            jwt=refresh_token.refresh_token,
            key=secret_key,
            algorithms=[algo]
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        jti = payload.get("jti")

        if jti is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        for session in sessions:
            if session["refresh_token_jti"] == jti:
                session["revoked"] = True
                print(session)
                return {
                    "message": "Logged out successfully"
                }
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found"
        )
        
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )