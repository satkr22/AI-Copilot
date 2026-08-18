from fastapi import APIRouter, Depends

def verify_token():
    print("token verified")

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(verify_token)]
)

@router.get("")
def get_users():
    return {
        "message": "all users"
    }

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