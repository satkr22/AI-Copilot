import os
import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from services.user_service import get_user

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# Load environment variables
load_dotenv()

secret_key = os.getenv('SECRET_KEY', "default")
if secret_key == 'default':
    raise ValueError("SECRET_KEY environment variable is not set")

algo = os.getenv('ALGORITHM', 'default')
if algo == 'default':
    raise ValueError("ALGORITHM environment variable is not set")
    

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(
            jwt=token,
            key=secret_key,
            algorithms=[algo]
        )
        
        if payload.get("tye") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
            
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )
            
        current_user = get_user(username=username)
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return current_user
            
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials"
        )
    

def get_current_admin(
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user



@router.get("/me")
def get_me(
    current_user: dict = Depends(get_current_user)
):
    return current_user

@router.get("/{user_id}")
def get_users_by_id(user_id: int):
    return {
        "id": user_id
    }
    
@router.delete("/{user_id}")
def delete_users(
    user_id: int,
    current_user: dict = Depends(get_current_admin)
):
    return {
        "message": f"User {user_id} deleted",
        "performed_by": current_user["username"]
    }