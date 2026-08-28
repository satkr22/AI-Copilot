from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    LoginResponse
)
from app.services.users.user_service import UserService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)




@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201
)
def register(
    payload: UserRegister,
    db: Session = Depends(get_db)
):
    service = UserService(db)
    return service.register(payload)


@router.post(
    "/login",
    response_model=LoginResponse
)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db)
):
    service = UserService(db)

    user = service.login(payload)

    return LoginResponse(
        access_token=user.id,
        user=UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserResponse
)
def me(
    current_user: User = Depends(get_current_user)
):
    return current_user