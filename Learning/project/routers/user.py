from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
    tags=["Users"]
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