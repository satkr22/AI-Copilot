from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

secret_key = os.getenv('SECRET_KEY', "default")
if secret_key == 'default':
    raise ValueError("SECRET_KEY environment variable is not set")

algo = os.getenv('ALGORITHM', 'default')
if algo == 'default':
    raise ValueError("ALGORITHM environment variable is not set")

def verify_token():
    print("token verified")
    
router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(verify_token)]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(
            jwt=token,
            key=secret_key,
            algorithms=[algo]
        )
        
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )
        
        return {
                "username": username
            }
        
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication credentials:{e}"
        )
    
    


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
    
@router.post("")
def create_users():
    return {
        "message": "User Created"
    }
    
@router.delete("/{user_id}")
def delete_users(user_id: int):
    return {
        "user deleted": user_id
    }