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
    expires = datetime.now(timezone.utc) + timedelta(seconds=30)
    
    payload = {
        "sub": username,
        "tye": "access",
        "exp": expires,
        "jti": str(uuid4())
    }
    
    token = jwt.encode(
        payload=payload,
        key=secret_key,
        algorithm=algo
    )
    
    return token


def create_refresh_token(username: str, session_id: str):
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    jti = str(uuid4())
    
    payload = {
        "sid": session_id,
        "sub": username,
        "tye": "refresh",
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
    
    session_id = str(uuid4())
    
    access_token = create_access_token(form_data.username)
    refresh_token, refresh_jti = create_refresh_token(form_data.username, session_id=session_id)
    
    sessions.append({
        "session_id": session_id,
        "username": form_data.username,
        "current_refresh_token_jti": refresh_jti,
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
        
        if payload.get("tye") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        username = payload.get("sub")
        jti = payload.get("jti")
        session_id = payload.get("sid")
        
        if username is None or jti is None or session_id is None:
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
       
        # find the logical session  
        session = None
        for s in sessions:
            if s["session_id"] == session_id:
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
            
        if jti != session["current_refresh_token_jti"]:
            session["revoked"] = True
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token reuse detected"
            )
        
        
        # legitimate refresh starts
        # Create new access token
        new_access_token = create_access_token(username=username)
        
        # Create new refresh token
        new_refresh_token, new_refresh_jti = create_refresh_token(username=username, session_id=session_id)
        
        # update the same logical session
        session["current_refresh_token_jti"] = new_refresh_jti
        
        print(sessions)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
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
        
        if payload.get("tye") != "refresh":
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
                if session["revoked"]:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Session already revoked"
                    )
                
                session["revoked"] = True
                    
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